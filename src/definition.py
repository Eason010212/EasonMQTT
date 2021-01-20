#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@file    :   definition.py
@time    :   2021/01/14 00:05:10
@author  :   宋义深 
@version :   1.0
@contact :   1371033826@qq.com 
@license :   GPL-3.0 License
@link    :   https://github.com/Eason010212/EasonMQTT
'''

PROTOCOL_NAME = "MQTT"
PROTOCOL_LEVEL = 4

class messageType:

    CONNECT = 1
    CONNACK = 2
    PUBLISH = 3
    PUBACK = 4
    PUBREC = 5
    PUBREL = 6
    PUBCOMP = 7
    SUBSCRIBE = 8
    SUBACK = 9
    UNSUBSCRIBE = 10
    UNSUBACK = 11
    PINGREQ = 12
    PINGRESP = 13
    DISCONNECT = 14

class ConnackReturnCode:
    ACCEPTED = 0
    REFUSED_UNSUPPORTED_PROTOCOL = 1
    REFUSED_ILLEGAL_CLIENTID = 2
    REFUSED_SERVER_UNAVAILABLE = 3
    REFUSED_INVALID_USER = 4
    REFUSED_UNAUTHORIZED = 5

class SubackReturnCode:
    SUCCESS_MAX_QOS_0 = 0
    SUCCESS_MAX_QOS_1 = 1
    SUCCESS_MAX_QOS_2 = 2
    FAILURE = 128
