import definition
import Encoders
class IllegalMessageException(Exception):
    pass

def utf8_decoder(bytes):
    length = int.from_bytes(bytes[0:2],byteorder='big')
    str = bytes[2:2+length].decode('utf-8')
    return str, bytes[2+length:]

def remainingBytes_Decoder(bytes):
    remainedLength = 0
    multiplier = 1
    bytePos = -1
    while bytePos == -1 or (int.from_bytes(bytes[bytePos:bytePos+1],'big') & 128) != 0:
        bytePos += 1
        remainedLength += (int.from_bytes(bytes[bytePos:bytePos+1],'big') & 127)*multiplier
        multiplier *= 128
        if multiplier > (128*128*128) :
            raise IllegalMessageException()
    if remainedLength!=bytes[bytePos+1:].__len__():
        raise IllegalMessageException()
    else:
        return bytes[bytePos+1:]

def CONNECT_Decoder(bytes):
    if int.from_bytes(bytes[0:1],byteorder='big')==16:
        remBytes = remainingBytes_Decoder(bytes[1:])
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
    if int.from_bytes(bytes[0:1],byteorder='big')==32:
        remBytes = remainingBytes_Decoder(bytes[1:])
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
    attrs = int.from_bytes(bytes[0:1],'big')
    remBytes = bytes[1:]
    dup = (attrs&8)>>3
    qos = (attrs&6)>>1
    retain = attrs&1
    remBytes = remainingBytes_Decoder(remBytes)
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
    if int.from_bytes(bytes[0:1],byteorder='big')==64:
        remBytes = remainingBytes_Decoder(bytes[1:])
        packetIdentifier = int.from_bytes(remBytes,'big')
    else:
        raise IllegalMessageException()
    return {
        'packetIdentifier': packetIdentifier
    }

def PUBREC_Decoder(bytes):
    if int.from_bytes(bytes[0:1],byteorder='big')==80:
        remBytes = remainingBytes_Decoder(bytes[1:])
        packetIdentifier = int.from_bytes(remBytes,'big')
    else:
        raise IllegalMessageException()
    return {
        'packetIdentifier': packetIdentifier
    }

def PUBREL_Decoder(bytes):
    if int.from_bytes(bytes[0:1],byteorder='big')==98:
        remBytes = remainingBytes_Decoder(bytes[1:])
        packetIdentifier = int.from_bytes(remBytes,'big')
    else:
        raise IllegalMessageException()
    return {
        'packetIdentifier': packetIdentifier
    }

def PUBCOMP_Decoder(bytes):
    if int.from_bytes(bytes[0:1],byteorder='big')==112:
        remBytes = remainingBytes_Decoder(bytes[1:])
        packetIdentifier = int.from_bytes(remBytes,'big')
    else:
        raise IllegalMessageException()
    return {
        'packetIdentifier': packetIdentifier
    }

def SUBSCRIBE_Decoder(bytes):
    if int.from_bytes(bytes[0:1],byteorder='big')==130:
        remBytes = remainingBytes_Decoder(bytes[1:])
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
    if int.from_bytes(bytes[0:1],byteorder='big')==144:
        remBytes = remainingBytes_Decoder(bytes[1:])
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
    if int.from_bytes(bytes[0:1],byteorder='big')==162:
        remBytes = remainingBytes_Decoder(bytes[1:])
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
    if int.from_bytes(bytes[0:1],byteorder='big')==176:
        remBytes = remainingBytes_Decoder(bytes[1:])
        packetIdentifier = int.from_bytes(remBytes[0:2],'big')
    else:
        raise IllegalMessageException()
    return {
        'packetIdentifier': packetIdentifier
    }

def PINGREQ_Decoder(bytes):
    if int.from_bytes(bytes[0:1],byteorder='big')==192:
        remBytes = remainingBytes_Decoder(bytes[1:])
    else:
        raise IllegalMessageException()
    return {}

def PINGRESP_Decoder(bytes):
    if int.from_bytes(bytes[0:1],byteorder='big')==208:
        remBytes = remainingBytes_Decoder(bytes[1:])
    else:
        raise IllegalMessageException()
    return {}

def DISCONNECT_Decoder(bytes):
    if int.from_bytes(bytes[0:1],byteorder='big')==224:
        remBytes = remainingBytes_Decoder(bytes[1:])
    else:
        raise IllegalMessageException()
    return {}

def message_Decoder(bytes):
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

def logicTest():
    print(CONNECT_Decoder(Encoders.CONNECT_Encoder(1,0,1,2,1,0,256,'eason0212','is','ijsfs','eason')))
    print(CONNACK_Decoder(Encoders.CONNACK_Encoder(1,definition.ConnackReturnCode.REFUSED_ILLEGAL_CLIENTID)))
    print(PUBLISH_Decoder(Encoders.PUBLISH_Encoder(1,2,1,'hhh',10,'hhhhh')))
    print(PUBACK_Decoder(Encoders.PUBACK_Encoder(10)))
    print(PUBREC_Decoder(Encoders.PUBREC_Encoder(10)))
    print(PUBREL_Decoder(Encoders.PUBREL_Encoder(10)))
    print(PUBCOMP_Decoder(Encoders.PUBCOMP_Encoder(10)))
    print(SUBSCRIBE_Decoder(Encoders.SUBSCRIBE_Encoder(11,[{'topic':'2333','qos':1},{'topic':'2433','qos':2}])))
    print(SUBACK_Decoder(Encoders.SUBACK_Encoder(11,[0,128])))
    print(UNSUBSCRIBE_Decoder(Encoders.UNSUBSCRIBE_Encoder(12,['2333','2433','2533'])))
    print(UNSUBACK_Decoder(Encoders.UNSUBACK_Encoder(12)))
    print(PINGREQ_Decoder(Encoders.PINGREQ_Encoder()))
    print(PINGRESP_Decoder(Encoders.PINGRESP_Encoder()))
    print(DISCONNECT_Decoder(Encoders.DISCONNECT_Encoder()))
