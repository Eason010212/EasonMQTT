# -*-coding:utf-8 -*-
'''
@file    :   Encoders.py
@time    :   2021/01/21 23:27:34
@author  :   宋义深 
@version :   1.0
@contact :   1371033826@qq.com 
@license :   GPL-3.0 License
@link    :   https://github.com/Eason010212/EasonMQTT
'''

import definition

def utf8_Encoder(str):
    """
        Description:
            编码带长度头部的utf-8字节串。
        Args:
            str(string)
                待编码的字符串。
        Returns:
            byte[]
                编码的带长度头部的utf-8字节串。   
        Raises:
            None
    """
    b = str.encode('utf-8')
    len = b.__len__()
    l = b''
    if len>65535:
        return b''
    else:
        l = int.to_bytes(len,2,'big')
    return l+b

def remainingBytes_Encoder(length):
    """
        Description:
            编码MQTT规定的“剩余长度”字节串。
        Args:
            len(int)
                剩余长度。
        Returns:
            byte[]
                编码的“剩余长度”字节串。   
        Raises:
            None
    """
    remainingBytes = b''
    while length>0:
        tmpByte = int(length%128)
        length = int(length/128)
        if length>0:
            tmpByte = tmpByte|128
        remainingBytes += tmpByte.to_bytes(1,'big')
    return remainingBytes

def CONNECT_Encoder(userNameFlag, passwordFlag, willRetain, willQos, willFlag, cleanSession, keepAlive, clientId, willTopic='', willMessage='', userName='', password=''):
    """
        Description:
            编码CONNECT报文字节串。
        Args:
            userNameFlag(int)
                用户名标志，1为存在用户名字段，0为不存在。
            passwordFlag(int)
                密码标志，1为存在密码字段，0为不存在。
            willRetain(int)
                遗嘱保留（willFlag = 0时必须设置为0），1为遗嘱保留，0为遗嘱不保留。
            willQos(int)
                遗嘱消息服务质量（willFlag = 0时必须设置为0）。
            willFlag(int)
                遗嘱标志。
            cleanSession(int)
                清理会话标志，1为清除历史订阅信息，0为不清除。
            keepAlive(int)
                保活时长，单位为s。
            clientId(int)
                ClientID。
            willTopic(string)
                遗嘱消息主题（仅willFlag = 1时可设置）。
            willMessage(string)
                遗嘱消息内容（仅willFlag = 1时可设置）。
            userName(string)
                用户名（仅userNameFlag = 1时可设置）。
            password(string)
                密码（仅password = 1时可设置）。
        Returns:
            byte[]
                编码的CONNECT报文字节串。   
        Raises:
            None
    """
    payload = b''
    payload += utf8_Encoder(clientId)
    if willFlag == 1:
        payload += utf8_Encoder(willTopic)
        payload += utf8_Encoder(willMessage)
    if userNameFlag == 1:
        payload += utf8_Encoder(userName)
    if passwordFlag == 1:
        payload += utf8_Encoder(password)
    varHeader = b''
    varHeader += utf8_Encoder(definition.PROTOCOL_NAME)
    varHeader += int.to_bytes(definition.PROTOCOL_LEVEL,1,'big')
    varHeader += int.to_bytes((userNameFlag<<7)+(passwordFlag<<6)+(willRetain<<5)+(willQos<<3)+(willFlag<<2)+(cleanSession<<1),1,'big')
    varHeader += int.to_bytes(keepAlive,2,'big')
    fixHeader = b''
    fixHeader += int.to_bytes(definition.messageType.CONNECT<<4,1,'big')
    fixHeader += remainingBytes_Encoder(varHeader.__len__()+payload.__len__())
    return fixHeader+varHeader+payload

def CONNACK_Encoder(sessionPresent, returnCode):
    """
        Description:
            编码CONNACK报文字节串。
        Args:
            sessionPresent(int)
                当前会话标志。
            returnCode(int)
                CONNACK返回码（具体含义见definiton.ConnackReturnCode)。
        Returns:
            byte[]
                编码的CONNACK报文字节串。   
        Raises:
            None
    """
    varHeader = b''
    varHeader += int.to_bytes(sessionPresent,1,'big')
    varHeader += int.to_bytes(returnCode,1,'big')
    fixHeader = b''
    fixHeader += int.to_bytes(definition.messageType.CONNACK<<4,1,'big')
    fixHeader += remainingBytes_Encoder(varHeader.__len__())
    return fixHeader+varHeader

def PUBLISH_Encoder(dup, qos, retain, topic, packetIdentifier, message):
    """
        Description:
            编码PUBLISH报文字节串。
        Args:
            dup(int)
                消息重发标志，1为重发消息，0为非重发消息。
            qos(int)
                消息服务质量等级。
            retain(int)
                消息保留标志，1为保留消息，0为非保留消息。
            topic(string)
                消息主题。
            packetIdentifier(int)
                报文标识符。
            message(string)
                消息内容。
        Returns:
            byte[]
                编码的PUBLISH报文字节串。   
        Raises:
            None
    """
    payload = utf8_Encoder(message)
    varHeader = b''
    varHeader += utf8_Encoder(topic)
    varHeader += int.to_bytes(packetIdentifier, 2, 'big')
    fixHeader = b''
    fixHeader += int.to_bytes((definition.messageType.PUBLISH<<4)+(dup<<3)+(qos<<1)+retain,1,'big')
    fixHeader += remainingBytes_Encoder(varHeader.__len__()+payload.__len__())
    return fixHeader+varHeader+payload

def PUBACK_Encoder(packetIdentifier):
    """
        Description:
            编码PUBACK报文字节串。
        Args:
            packetIdenifier(int)
                报文标识符。
        Returns:
            byte[]
                编码的PUBACK报文字节串。   
        Raises:
            None
    """
    varHeader = int.to_bytes(packetIdentifier, 2, 'big')
    fixHeader = b''
    fixHeader += int.to_bytes(definition.messageType.PUBACK<<4,1,'big')
    fixHeader += remainingBytes_Encoder(varHeader.__len__())
    return fixHeader+varHeader

def PUBREC_Encoder(packetIdentifier):
    """
        Description:
            编码PUBREC报文字节串。
        Args:
            packetIdentifier(int)
                报文标识符。
        Returns:
            byte[]
                编码的PUBREC报文字节串。   
        Raises:
            None
    """
    varHeader = int.to_bytes(packetIdentifier, 2, 'big')
    fixHeader = b''
    fixHeader += int.to_bytes(definition.messageType.PUBREC<<4,1,'big')
    fixHeader += remainingBytes_Encoder(varHeader.__len__())
    return fixHeader+varHeader

def PUBREL_Encoder(packetIdentifier):
    """
        Description:
            编码PUBREL报文字节串。
        Args:
            packetIdentifier(int)
                报文标识符。
        Returns:
            byte[]
                编码的PUBREL报文字节串。   
        Raises:
            None
    """
    varHeader = int.to_bytes(packetIdentifier, 2, 'big')
    fixHeader = b''
    fixHeader += int.to_bytes((definition.messageType.PUBREL<<4)+2,1,'big')
    fixHeader += remainingBytes_Encoder(varHeader.__len__())
    return fixHeader+varHeader

def PUBCOMP_Encoder(packetIdentifier):
    """
        Description:
            编码PUBCOMP报文字节串。
        Args:
            packetIdentifier(int)
                报文标识符。
        Returns:
            byte[]
                编码的PUBCOMP报文字节串。   
        Raises:
            None
    """
    varHeader = int.to_bytes(packetIdentifier, 2, 'big')
    fixHeader = b''
    fixHeader += int.to_bytes(definition.messageType.PUBCOMP<<4,1,'big')
    fixHeader += remainingBytes_Encoder(varHeader.__len__())
    return fixHeader+varHeader

def SUBSCRIBE_Encoder(packetIdentifier,topics):
    """
        Description:
            编码SUBSCRIBE报文字节串。
        Args:
            packetIdentifier(int)
                报文标识符。
            topics(array[dict])
                订阅信息数组。数组单元为字典，字典中必须包含topic字段和qos字段。
        Returns:
            byte[]
                编码的SUBSCRIBE报文字节串。   
        Raises:
            None
    """
    payload = b''
    topicCount = topics.__len__()
    for i in range(0,topicCount):
        topic = topics[i]['topic']
        qos = topics[i]['qos']
        payload += utf8_Encoder(topic)
        payload += int.to_bytes(qos,1,'big')
    varHeader = int.to_bytes(packetIdentifier, 2, 'big')
    fixHeader = b''
    fixHeader += int.to_bytes((definition.messageType.SUBSCRIBE<<4)+2,1,'big')
    fixHeader += remainingBytes_Encoder(varHeader.__len__()+payload.__len__())
    return fixHeader+varHeader+payload

def SUBACK_Encoder(packetIdentifier,returnCodes):
    """
        Description:
            编码SUBACK报文字节串。
        Args:
            packetIdentifier(int)
                报文标识符。
            returnCodes(array[int])
                订阅结果数组。数组单元为definiton.SubackReturnCode中定义的内容。
        Returns:
            byte[]
                编码的SUBACK报文字节串。   
        Raises:
            None
    """
    payload = b''
    returnCount = returnCodes.__len__()
    for i in range(0,returnCount):
        returnCode = returnCodes[i]
        payload += int.to_bytes(returnCode,1,'big')
    varHeader = int.to_bytes(packetIdentifier, 2, 'big')
    fixHeader = b''
    fixHeader += int.to_bytes(definition.messageType.SUBACK<<4,1,'big')
    fixHeader += remainingBytes_Encoder(varHeader.__len__()+payload.__len__())
    return fixHeader+varHeader+payload

def UNSUBSCRIBE_Encoder(packetIdentifier,topics):
    """
        Description:
            编码UNSUBSCRIBE报文字节串。
        Args:
            packetIdentifier(int)
                报文标识符。
            topics(array[string])
                取消订阅信息数组，数组单元为取消订阅的主题字符串。
        Returns:
            byte[]
                编码的UNSUBSCRIBE报文字节串。   
        Raises:
            None
    """
    payload = b''
    topicCount = topics.__len__()
    for i in range(0,topicCount):
        topic = topics[i]
        payload += utf8_Encoder(topic)
    varHeader = int.to_bytes(packetIdentifier, 2, 'big')
    fixHeader = b''
    fixHeader += int.to_bytes((definition.messageType.UNSUBSCRIBE<<4)+2,1,'big')
    fixHeader += remainingBytes_Encoder(varHeader.__len__()+payload.__len__())
    return fixHeader+varHeader+payload

def UNSUBACK_Encoder(packetIdentifier):
    """
        Description:
            编码UNSUBACK报文字节串。
        Args:
            packetIdentifier(int)
                报文标识符。
        Returns:
            byte[]
                编码的UNSUBACK报文字节串。   
        Raises:
            None
    """
    varHeader = int.to_bytes(packetIdentifier, 2, 'big')
    fixHeader = b''
    fixHeader += int.to_bytes(definition.messageType.UNSUBACK<<4,1,'big')
    fixHeader += remainingBytes_Encoder(varHeader.__len__())
    return fixHeader+varHeader

def PINGREQ_Encoder():
    """
        Description:
            编码PINGREQ报文字节串。
        Args:
            None
        Returns:
            byte[]
                编码的PINGREQ报文字节串。   
        Raises:
            None
    """
    fixHeader = b''
    fixHeader += int.to_bytes(definition.messageType.PINGREQ<<4,1,'big')
    fixHeader += int.to_bytes(0,1,'big')
    return fixHeader

def PINGRESP_Encoder():
    """
        Description:
            编码PINGRESP报文字节串。
        Args:
            None
        Returns:
            byte[]
                编码的PINGRESP文字节串。   
        Raises:
            None
    """
    fixHeader = b''
    fixHeader += int.to_bytes(definition.messageType.PINGRESP<<4,1,'big')
    fixHeader += int.to_bytes(0,1,'big')
    return fixHeader

def DISCONNECT_Encoder():
    """
        Description:
            编码DISCONNECT报文字节串。
        Args:
            None
        Returns:
            byte[]
                编码的DISCONNECT报文字节串。   
        Raises:
            None
    """
    fixHeader = b''
    fixHeader += int.to_bytes(definition.messageType.DISCONNECT<<4,1,'big')
    fixHeader += int.to_bytes(0,1,'big')
    return fixHeader