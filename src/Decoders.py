# -*-coding:utf-8 -*-
'''
@file    :   Decoders.py
@time    :   2021/01/21 17:42:58
@author  :   宋义深 
@version :   1.0
@contact :   1371033826@qq.com 
@license :   GPL-3.0 License
@link    :   https://github.com/Eason010212/EasonMQTT
'''

import definition

class IllegalMessageException(Exception):
    '''
        Description:
            消息解码错误时抛出此异常。
        Args:
            None
    '''
    pass

def utf8_decoder(bytes):
    """
        Description:
            带长度头部的utf-8字节串解码。此方法从给定的字节串中解码一个utf-8字符串，将解码结果与剩余部分一并返回。
        Args:
            bytes(byte[])
                待解码的字节串。
        Returns:
            string
                解码出的utf-8字符串。
            byte[]
                解码后剩余的字节串。    
        Raises:
            None
    """
    length = int.from_bytes(bytes[0:2],byteorder='big')
    str = bytes[2:2+length].decode('utf-8')
    return str, bytes[2+length:]

def remainingBytes_Decoder(bytes, preMode=False):
    """
        Description:
            解析报文的剩余长度，并提供可选的验证功能：当preMode为True（预解码模式）时，仅返回剩余字节与报文剩余长度，不进行验证；当preMode为False（常规模式）时，会额外进行长度校验。
        Args:
            bytes(byte[])
                待解析的字节串。
            preMode(boolean, DEFAULT=False)
                True - 预解码模式； False - 常规模式。
        Returns:
            byte[]
                除去“剩余长度”字节的剩余字节。
            int
                报文剩余长度。
        Raises:
            Decoders.IllegalMessageException
                长度校验出错（仅常规模式）。
    """
    remainedLength = 0
    multiplier = 1
    bytePos = -1
    while bytePos == -1 or (int.from_bytes(bytes[bytePos:bytePos+1],'big') & 128) != 0:
        bytePos += 1
        remainedLength += (int.from_bytes(bytes[bytePos:bytePos+1],'big') & 127)*multiplier
        multiplier *= 128
        if multiplier > (128*128*128) :
            raise IllegalMessageException()
    if remainedLength!=bytes[bytePos+1:].__len__() and not preMode:
        raise IllegalMessageException()
    else:
        return bytes[bytePos+1:],remainedLength

def CONNECT_Decoder(bytes):
    """
        Description:
            CONNECT报文解码器。
        Args:
            bytes(byte[])
                待解码的报文字节串。
        Returns:
            dict
                CONNECT报文解析结果字典。包含字段: 
                cleanSession - 清理会话标志；
                willFlag - 遗嘱标志；
                willQos - 遗嘱服务质量等级；
                willRetain - 遗嘱保留标志；
                passwordFlag - 密码标志；
                userNameFlag - 用户名标志；
                keepAlive - 保活时长；
                clientId - ClientID；
                willTopic - 遗嘱主题；
                willMessage - 遗嘱消息；
                userName - 用户名；
                password - 密码。
        Raises:
            Decoders.IllegalMessageException
                长度校验出错。
    """
    if int.from_bytes(bytes[0:1],byteorder='big')==16:
        remBytes = remainingBytes_Decoder(bytes[1:])[0]
        protocolName, remBytes = utf8_decoder(remBytes)
        if protocolName == 'MQTT':
            protocolLevel = int.from_bytes(remBytes[0:1],byteorder='big')
            remBytes = remBytes[1:]
            if protocolLevel == 4:
                flags = int.from_bytes(remBytes[0:1],byteorder='big')
                remBytes = remBytes[1:]
                reserved = flags&1
                if reserved == 0:
                    cleanSession = (flags&2)>>1
                    willFlag = (flags&4)>>2
                    willQos = (flags&24)>>3
                    willRetain = (flags&32)>>5
                    passwordFlag = (flags&64)>>6
                    userNameFlag = (flags&128)>>7
                    if (willFlag==0 and willQos!=0) or (willFlag==0 and willRetain!=0) or willQos==3 or (userNameFlag==0 and passwordFlag==1):
                        raise IllegalMessageException()
                    else:
                        keepAlive = int.from_bytes(remBytes[0:2],byteorder='big')
                        remBytes = remBytes[2:]
                        clientId, remBytes = utf8_decoder(remBytes)
                        if willFlag==1:
                            willTopic, remBytes = utf8_decoder(remBytes)
                            willMessage, remBytes = utf8_decoder(remBytes)
                        if userNameFlag==1:
                            userName, remBytes = utf8_decoder(remBytes)
                            if passwordFlag==1:
                                password, remBytes = utf8_decoder(remBytes)
                    return {
                        'cleanSession': cleanSession,
                        'willFlag': willFlag,
                        'willQos': willQos,
                        'willRetain': willRetain,
                        'passwordFlag': passwordFlag,
                        'userNameFlag': userNameFlag,
                        'keepAlive': keepAlive,
                        'clientId': clientId,
                        'willTopic': willTopic if willFlag==1 else '',
                        'willMessage': willMessage if willFlag==1 else '',
                        'userName': userName if userNameFlag==1 else '',
                        'password': password if passwordFlag==1 else ''
                    }
                else:
                    raise IllegalMessageException()
            else:
                raise IllegalMessageException()
        else:
            raise IllegalMessageException()
    else:
        raise IllegalMessageException()

def CONNACK_Decoder(bytes):
    """
        Description:
            CONNACK报文解码器。
        Args:
            bytes(byte[])
                待解码的报文字节串。
        Returns:
            dict
                CONNACK报文解析结果字典。包含字段: 
                sessionPresent - 当前会话标志；
                returnCode - CONNACK返回码，具体含义见definition.ConnackReturnCode。
        Raises:
            Decoders.IllegalMessageException
                长度校验出错。
    """
    if int.from_bytes(bytes[0:1],byteorder='big')==32:
        remBytes = remainingBytes_Decoder(bytes[1:])[0]
        sessionPresent = int.from_bytes(remBytes[0:1],'big')
        if sessionPresent<=1:
            returnCode = int.from_bytes(remBytes[1:2],'big')
        else:
            raise IllegalMessageException()
    else:
        raise IllegalMessageException()
    return {
        'sessionPresent': sessionPresent,
        'returnCode': returnCode
    }

def PUBLISH_Decoder(bytes):
    """
        Description:
            PUBLISH报文解码器。
        Args:
            bytes(byte[])
                待解码的报文字节串。
        Returns:
            dict
                PUBLISH报文解析结果字典。包含字段: 
                dup - 重发标志；
                qos - 服务质量等级；
                retain - 保留标志；
                topic - 消息主题；
                packetIdentifier - 报文标识符；
                message - 消息内容。
        Raises:
            Decoders.IllegalMessageException
                长度校验出错。
    """
    attrs = int.from_bytes(bytes[0:1],'big')
    remBytes = bytes[1:]
    dup = (attrs&8)>>3
    qos = (attrs&6)>>1
    retain = attrs&1
    remBytes = remainingBytes_Decoder(remBytes)[0]
    topic, remBytes = utf8_decoder(remBytes)
    packetIdentifier = int.from_bytes(remBytes[0:2],'big')
    message = utf8_decoder(remBytes[2:])[0]
    return {
        'dup': dup,
        'qos': qos,
        'retain': retain,
        'topic': topic,
        'packetIdentifier': packetIdentifier,
        'message': message
    }

def PUBACK_Decoder(bytes):
    """
        Description:
            PUBACK报文解码器。
        Args:
            bytes(byte[])
                待解码的报文字节串。
        Returns:
            dict
                PUBACK报文解析结果字典。包含字段: 
                packetIdentifier - 报文标识符。
        Raises:
            Decoders.IllegalMessageException
                长度校验出错。
    """
    if int.from_bytes(bytes[0:1],byteorder='big')==64:
        remBytes = remainingBytes_Decoder(bytes[1:])[0]
        packetIdentifier = int.from_bytes(remBytes,'big')
    else:
        raise IllegalMessageException()
    return {
        'packetIdentifier': packetIdentifier
    }

def PUBREC_Decoder(bytes):
    """
        Description:
            PUBREC报文解码器。
        Args:
            bytes(byte[])
                待解码的报文字节串。
        Returns:
            dict
                PUBREC报文解析结果字典。包含字段: 
                packetIdentifier - 报文标识符。
        Raises:
            Decoders.IllegalMessageException
                长度校验出错。
    """
    if int.from_bytes(bytes[0:1],byteorder='big')==80:
        remBytes = remainingBytes_Decoder(bytes[1:])[0]
        packetIdentifier = int.from_bytes(remBytes,'big')
    else:
        raise IllegalMessageException()
    return {
        'packetIdentifier': packetIdentifier
    }

def PUBREL_Decoder(bytes):
    """
        Description:
            PUBREL报文解码器。
        Args:
            bytes(byte[])
                待解码的报文字节串。
        Returns:
            dict
                PUBREL报文解析结果字典。包含字段: 
                packetIdentifier - 报文标识符。
        Raises:
            Decoders.IllegalMessageException
                长度校验出错。
    """
    if int.from_bytes(bytes[0:1],byteorder='big')==98:
        remBytes = remainingBytes_Decoder(bytes[1:])[0]
        packetIdentifier = int.from_bytes(remBytes,'big')
    else:
        raise IllegalMessageException()
    return {
        'packetIdentifier': packetIdentifier
    }

def PUBCOMP_Decoder(bytes):
    """
        Description:
            PUBCOMP报文解码器。
        Args:
            bytes(byte[])
                待解码的报文字节串。
        Returns:
            dict
                PUBCOMP报文解析结果字典。包含字段: 
                packetIdentifier - 报文标识符。
        Raises:
            Decoders.IllegalMessageException
                长度校验出错。
    """
    if int.from_bytes(bytes[0:1],byteorder='big')==112:
        remBytes = remainingBytes_Decoder(bytes[1:])[0]
        packetIdentifier = int.from_bytes(remBytes,'big')
    else:
        raise IllegalMessageException()
    return {
        'packetIdentifier': packetIdentifier
    }

def SUBSCRIBE_Decoder(bytes):
    """
        Description:
            SUBSCRIBE报文解码器。
        Args:
            bytes(byte[])
                待解码的报文字节串。
        Returns:
            dict
                SUBSCRIBE报文解析结果字典。包含字段: 
                packetIdentifier - 报文标识符；
                topics - 订阅主题数组；
        Raises:
            Decoders.IllegalMessageException
                长度校验出错。
    """
    if int.from_bytes(bytes[0:1],byteorder='big')==130:
        remBytes = remainingBytes_Decoder(bytes[1:])[0]
        packetIdentifier = int.from_bytes(remBytes[0:2],'big')
        remBytes = remBytes[2:]
        topics = []
        while remBytes.__len__()!=0:
            topic, remBytes = utf8_decoder(remBytes)
            qos = int.from_bytes(remBytes[0:1],'big')
            remBytes = remBytes[1:]
            combination = {
                'topic': topic,
                'qos': qos
            }
            topics.append(combination)
    else:
        raise IllegalMessageException()
    return {
        'packetIdentifier': packetIdentifier,
        'topics': topics
    }

def SUBACK_Decoder(bytes):
    """
        Description:
            SUBACK报文解码器。
        Args:
            bytes(byte[])
                待解码的报文字节串。
        Returns:
            dict
                SUBACK报文解析结果字典。包含字段: 
                packetIdentifier - 报文标识符；
                returnCodes - SUBACK返回码数组（具体含义见definition.SubackReturnCode）。
        Raises:
            Decoders.IllegalMessageException
                长度校验出错。
    """
    if int.from_bytes(bytes[0:1],byteorder='big')==144:
        remBytes = remainingBytes_Decoder(bytes[1:])[0]
        packetIdentifier = int.from_bytes(remBytes[0:2],'big')
        remBytes = remBytes[2:]
        returnCodes = []
        while remBytes.__len__()!=0:
            returnCodes.append(int.from_bytes(remBytes[0:1],'big'))
            remBytes = remBytes[1:]
    else:
        raise IllegalMessageException()
    return {
        'packetIdentifier': packetIdentifier,
        'returnCodes': returnCodes
    }

def UNSUBSCRIBE_Decoder(bytes):
    """
        Description:
            UNSUBSCRIBE报文解码器。
        Args:
            bytes(byte[])
                待解码的报文字节串。
        Returns:
            dict
                UNSUBSCRIBE报文解析结果字典。包含字段: 
                packetIdentifier - 报文标识符；
                topics - 取消订阅主题数组。
        Raises:
            Decoders.IllegalMessageException
                长度校验出错。
    """
    if int.from_bytes(bytes[0:1],byteorder='big')==162:
        remBytes = remainingBytes_Decoder(bytes[1:])[0]
        packetIdentifier = int.from_bytes(remBytes[0:2],'big')
        remBytes = remBytes[2:]
        topics = []
        while remBytes.__len__()!=0:
            topic, remBytes = utf8_decoder(remBytes)
            topics.append(topic)
    else:
        raise IllegalMessageException()
    return {
        'packetIdentifier': packetIdentifier,
        'topics': topics
    }

def UNSUBACK_Decoder(bytes):
    """
        Description:
            UNSUBACK报文解码器。
        Args:
            bytes(byte[])
                待解码的报文字节串。
        Returns:
            dict
                UNSUBACK报文解析结果字典。包含字段: 
                packetIdentifier - 报文标识符。
        Raises:
            Decoders.IllegalMessageException
                长度校验出错。
    """
    if int.from_bytes(bytes[0:1],byteorder='big')==176:
        remBytes = remainingBytes_Decoder(bytes[1:])[0]
        packetIdentifier = int.from_bytes(remBytes[0:2],'big')
    else:
        raise IllegalMessageException()
    return {
        'packetIdentifier': packetIdentifier
    }

def PINGREQ_Decoder(bytes):
    """
        Description:
            PINGREQ报文解码器。
        Args:
            bytes(byte[])
                待解码的报文字节串。
        Returns:
            dict
                空字典。
        Raises:
            Decoders.IllegalMessageException
                长度校验出错。
    """
    if int.from_bytes(bytes[0:1],byteorder='big')==192:
        remBytes = remainingBytes_Decoder(bytes[1:])[0]
    else:
        raise IllegalMessageException()
    return {}

def PINGRESP_Decoder(bytes):
    """
        Description:
            PINGRESP报文解码器。
        Args:
            bytes(byte[])
                待解码的报文字节串。
        Returns:
            dict
                空字典。
        Raises:
            Decoders.IllegalMessageException
                长度校验出错。
    """
    if int.from_bytes(bytes[0:1],byteorder='big')==208:
        remBytes = remainingBytes_Decoder(bytes[1:])[0]
    else:
        raise IllegalMessageException()
    return {}

def DISCONNECT_Decoder(bytes):
    """
        Description:
            DISCONNECT报文解码器。
        Args:
            bytes(byte[])
                待解码的报文字节串。
        Returns:
            dict
                空字典。
        Raises:
            Decoders.IllegalMessageException
                长度校验出错。
    """
    if int.from_bytes(bytes[0:1],byteorder='big')==224:
        remBytes = remainingBytes_Decoder(bytes[1:])[0]
    else:
        raise IllegalMessageException()
    return {}

def message_Decoder(bytes):
    """
        Description:
            报文解码器选择器。
        Args:
            bytes(byte[])
                待解码的报文字节串。
        Returns:
            None
        Raises:
            Decoders.IllegalMessageException
                报文头部出错。
    """
    messageType = ((int.from_bytes(bytes[0:1],byteorder='big'))&240)>>4
    if messageType == definition.messageType.CONNECT:
        return messageType, CONNECT_Decoder(bytes)
    elif messageType == definition.messageType.CONNACK:
        return messageType, CONNACK_Decoder(bytes)
    elif messageType == definition.messageType.PUBLISH:
        return messageType, PUBLISH_Decoder(bytes)
    elif messageType == definition.messageType.PUBACK:
        return messageType, PUBACK_Decoder(bytes)
    elif messageType == definition.messageType.PUBREC:
        return messageType, PUBREC_Decoder(bytes)
    elif messageType == definition.messageType.PUBREL:
        return messageType, PUBREL_Decoder(bytes)
    elif messageType == definition.messageType.PUBCOMP:
        return messageType, PUBCOMP_Decoder(bytes)
    elif messageType == definition.messageType.SUBSCRIBE:
        return messageType, SUBSCRIBE_Decoder(bytes)
    elif messageType == definition.messageType.SUBACK:
        return messageType, SUBACK_Decoder(bytes)
    elif messageType == definition.messageType.UNSUBSCRIBE:
        return messageType, UNSUBSCRIBE_Decoder(bytes)
    elif messageType == definition.messageType.UNSUBACK:
        return messageType, UNSUBACK_Decoder(bytes)
    elif messageType == definition.messageType.PINGREQ:
        return messageType, PINGREQ_Decoder(bytes)
    elif messageType == definition.messageType.PINGRESP:
        return messageType, PINGRESP_Decoder(bytes)
    elif messageType == definition.messageType.DISCONNECT:
        return messageType, DISCONNECT_Decoder(bytes)
    else:
        raise IllegalMessageException()