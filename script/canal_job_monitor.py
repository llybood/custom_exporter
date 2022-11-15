#!/usr/local/python381/bin/python3
# -*- coding: UTF-8 -*-
import os 
import json
import sys
from MySQLdb import _mysql

source_db_host = "127.0.0.1"
source_db_port = 3306
source_db_user = "root"
source_db_password = "123456"
middle_db_host = "127.0.0.1"
middle_db_port = "3306"
middle_db_user = "root"
middle_db_password = "123456"
middle_db_database = "mysql"


def get_mysql_result(db_conn, sql):
    db_conn.query(sql)
    r = db_conn.use_result()
    return r.fetch_row()[0][0].decode()
    db_conn.close()
    
def main(target):
    metrics = []
    metric = {}
    instances = []
    # 获取源端表数据量
    source_sql = "select count(*) from %s" %(target,)
    source_db = _mysql.connect(host=source_db_host, port=source_db_port, user=source_db_user, password=source_db_password)
    source_counts = get_mysql_result(source_db, source_sql)
    # 获取目标端表数据量
    middle_table = middle_db_database + "." + target.split(".")[1]
    middle_sql = "select count(*) from %s" %(middle_table,)
    middle_db = _mysql.connect(host=source_db_host, port=source_db_port, user=source_db_user, password=source_db_password)
    middle_counts = get_mysql_result(middle_db, middle_sql)
    # 比较差异,返回json数据量
    data_diff_num = int(source_counts) - int(middle_counts) 
    instances.append({"instance": target, "type": "business", "value": data_diff_num})
    metric["instances"] = instances
    metric["metric"] = "custom_canal_monitor_data_diff"
    metric["description"] = "monitor canal sync data differences, normal is 0"
    metrics.append(metric)
    return metrics

if __name__ == "main":
    main(target)
