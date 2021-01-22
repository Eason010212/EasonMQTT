# -*-coding:utf-8 -*-
'''
@file    :   localTest_Client1.py
@time    :   2021/01/22 13:23:34
@author  :   宋义深 
@version :   1.0
@contact :   1371033826@qq.com 
@license :   GPL-3.0 License
@link    :   https://github.com/Eason010212/EasonMQTT
'''

'''
    EasonMQTT - 本地环回测试
    请复制到src文件夹下进行测试。
    运行顺序：启动Server - 启动Client1 - 启动Client2 - 退出Client2 - 退出Client1 - 启动Client1。
    测试内容：MQTT连接、3种QOS级别的消息发布与接收、多级主题订阅、WILL机制测试、RETAIN机制测试。
'''
from Client import *

client1 = startClient('localhost',8888,0,0,0,0,0,0,200,'testClient1','','')
subscribe(client1,[{
    'topic':'test/#',
    'qos':2
}])
