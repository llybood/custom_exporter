# 简介
该项目是基于python3实现的prometheus的自定义exporter.目前可以通过编写shell脚本或者python脚本获取并输出格式化的监控数据,prometheus会通过该exporter抓取监控数据

# 快速开始
## 直接部署

### 1.运行环境
> 需要安装Python3,建议Python版本在3.9以上。

### 2.项目代码克隆
```
git clone https://github.com/llybood/custom_exporter.git
cd custom_exporter/
```
> 或在 [Release](https://github.com/llybood/custom_exporter/releases) 直接手动下载源码。

### 3. 安装依赖
```
pip3 install -r requirements.txt
```

### 4. 配置
编辑conf/config.yaml文件
```
test:                  -----------------job名称,该名称配置完以后对应http访问路径,示例http://{IP}:9111/{job}/metrics
  script: test.sh      -----------------脚本名称,对应script下的采集数据脚本。
canal-data-sync-monitor:
  script: canal_job_monitor.py
```
>以上为示例配置,定义了2个监控采集job,分别为test和canal-data-sync-monitor,并配置了要调用的采集数据脚本

### 5. 启动
```
nohup python3 custom_exporter.py > custom_exporter.log 2>&1 &
```
## docker部署
### 1.项目代码克隆
```
git clone https://github.com/llybood/custom_exporter.git
cd custom_exporter/
```
> 或在 Realase 直接手动下载源码。
### 2. 修改配置同上

### 3. 启动
```
docker-compose up -d
```

# 获取访问数据说明
按照示例配置,抓取数据地址为
```
curl http://{IP}:9111/test/metrics
curl http://{IP}:9111/canal-data-sync-monitor/metrics
```
访问地址可以带target参数,获取job下某个实例的监控数据,比如
```
curl http://{IP}:9111/test/metrics?target=test1
```

# 采集脚本编写说明
## 输出格式
数据以JSON数组输出,一个job下可以有多个metric,每个metric下可以有多个instance,如下所示
```
[{
	"instances": [{
		"instance": "test1",
		"type": "business",
		"value": "1000"
	}, {
		"instance": "test2",
		"type": "business",
		"value": "2000"
	}],
	"metric": "test1",
	"description": "this is test1"
}, {
	"instances": [{
		"instance": "test3",
		"type": "module",
		"value": "3000"
	}, {
		"instance": "test4",
		"type": "module",
		"value": "4000"
	}],
	"metric": "test2",
	"description": "this is test2"
}]
```
**备注**
1. 每个metric下必须有metric,description和instances的键值对
2. instances值是一个列表
3. 示例中instance和type会生成prometheus的标签,并不是定义死的,可以根据自己需求修改对应的键名,也可以增加键值对,生成更多对应的标签。

以上示例脚本,访问输出如下
```
# HELP test1 this is test1
# TYPE test1 gauge
test1{instance="test1",type="business"} 1000.0
test1{instance="test2",type="business"} 2000.0
# HELP test2 this is test2
# TYPE test2 gauge
test2{instance="test3",type="module"} 3000.0
test2{instance="test4",type="module"} 4000.0
```
## shell脚本编写
> shell脚本编写无特殊说明,但是需要注意如果需要传入target,shell脚本也需要带入这个参数

## python脚本编写
> 为了提高python的执行速度,这里并没有通过subprocess执行python脚本的方法获取数据,而是以调用python模块的方法来执行自定义python脚本的,所以需要在main函数返回数据,如下所示:
```
......
def main(target):
    metric["instances"] = instances
    metric["metric"] = "custom_canal_monitor_data_diff"
    metric["description"] = "monitor canal sync data differences, normal is 0"
    metrics.append(metric)
    return metrics
    
if __name__ == "main":
    main(target)
```
