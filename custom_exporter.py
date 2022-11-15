#!/usr/local/python381/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2022/11/1 10:58
# @Author  : llybood

import os
import yaml
import sys
import ujson
import asyncio
import uvloop
import importlib
from prometheus_client import Counter
from prometheus_client import Gauge
from prometheus_client import Histogram
from prometheus_client import generate_latest
from prometheus_client import CollectorRegistry
from sanic import Sanic
from sanic import response
from sanic import json
from MySQLdb import _mysql

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

SCRIPT_DIR = os.path.split(os.path.realpath(__file__))[0] + '/script'
CONFIG_PATH = os.path.split(os.path.realpath(__file__))[0] + '/conf/config.yaml'

# 加载自定义脚本模块路径
sys.path.append(SCRIPT_DIR)

# 获取监控采集配置
def get_config():
    with open(CONFIG_PATH, 'r') as f:
        data = yaml.load(f.read(), Loader=yaml.FullLoader)
    return data

def get_module_name(script_file):
    if script_file.endswith('.py'):
        return script_file.replace('.py', '')
    else:
        return None

# 获取python脚本采集数据
async def get_python_collect_metrics(monitor):
    metrics = []
    target = monitor.get('target')
    script = monitor.get('script')
    custom_module = importlib.import_module(get_module_name(script))
    #metric = canal_job_monitor_test.main(target)
    metric = custom_module.main(target)
    metric['name'] = monitor.get('name')
    metric['description'] = monitor.get('description')
    metrics.append(metric)
    return metrics

# 获取shell脚本采集数据
async def get_shell_collect_metrics(monitor):
    metrics = []
    target = monitor.get('target')
    script = SCRIPT_DIR + '/' + monitor.get('script')
    if target:
        command_line = script + " " + target_instance
    else:
        command_line = script
    proc = await asyncio.create_subprocess_shell(command_line, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    res  = await proc.stdout.readline()
    metric = ujson.loads(res.decode())
    await proc.wait()
    metric['name'] = monitor.get('name')
    metric['description'] = monitor.get('description')
    metrics.append(metric)
    return metrics

# 汇总采集数据
async def get_metrics(monitor):
    script = monitor.get('script')
    if script.endswith(".py"):
        metrics = await get_python_collect_metrics(monitor) 
    elif script.endswith(".sh"):
        metrics = await get_shell_collect_metrics(monitor) 
    else:
        metrics = []
    return metrics

# 格式化成gauge类型监控数据
async def set_gauge_metrics(metrics):
    for metric in metrics:
        registry = CollectorRegistry()
        name = metric['name']
        description = metric['description']
        gauge = Gauge(name, description, ['instance','type'], registry=registry)
        for instance in metric['instances']:
            instance_value = instance['value']
            instance_labels = instance
            instance.pop('value')
            gauge.labels(**instance_labels).set(instance_value)
    return generate_latest(registry).decode()

app = Sanic(__name__)
config_settings = get_config()
app.config.update(config_settings)

sem = None

@app.listener('before_server_start')
def init(sanic, loop):
    global sem
    concurrency_per_worker = 4
    sem = asyncio.Semaphore(concurrency_per_worker)

@app.route("/metrics", methods=["GET"])
async def index(request):
    return response.text("I'm Running")

@app.route("/<job:str>/metrics", methods=["GET"])
async def get_job_metrics(request, job):
    monitor = app.config.get(job)
    if monitor is None:
        return response.html("Sorry,server didn't find this page, maybe you didn't configure the collection task correctly")
    target_args = request.args.get('target')
    if target_args is not None:
        monitor['target'] = target_args
    metrics = await get_metrics(monitor)
    prometheus_metrics = await set_gauge_metrics(metrics)
    if monitor.__contains__('target'):
        del monitor['target']
    return response.text(prometheus_metrics)

if __name__ == '__main__': 
    app.run(host="0.0.0.0", port=9111, workers=2, debug=False, access_log=True)
