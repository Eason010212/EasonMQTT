import definition

class MessageLengthException(Exception):
    pass

def utf8_Encoder(str):
    b = str.encode('utf-8')
    len = b.__len__()
    l = b''
    if len>65535:
        raise MessageLengthException()
    else:
        l = int.to_bytes(len,2,'big')
    return l+b

def remainingBytes_Encoder(length):
    remainingBytes = b''
    while length>0:
        tmpByte = int(length%128)
        length = int(length/128)
        if length>0:
            tmpByte = tmpByte|128
        remainingBytes += tmpByte.to_bytes(1,'big')
    return remainingBytes

def CONNECT_Encoder(userNameFlag, passwordFlag, willRetain, willQos, willFlag, cleanSession, keepAlive, clientId, willTopic='', willMessage='', userName='', password=''):
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
    varHeader = b''
    varHeader += int.to_bytes(sessionPresent,1,'big')
    varHeader += int.to_bytes(returnCode,1,'big')
    fixHeader = b''
    fixHeader += int.to_bytes(definition.messageType.CONNACK<<4,1,'big')
    fixHeader += remainingBytes_Encoder(varHeader.__len__())
    return fixHeader+varHeader

def PUBLISH_Encoder(dup, qos, retain, topic, packetIdentifier, message):
    payload = utf8_Encoder(message)
    varHeader = b''
    varHeader += utf8_Encoder(topic)
    varHeader += int.to_bytes(packetIdentifier, 2, 'big')
    fixHeader = b''
    fixHeader += int.to_bytes((definition.messageType.PUBLISH<<4)+(dup<<3)+(qos<<1)+retain,1,'big')
    fixHeader += remainingBytes_Encoder(varHeader.__len__()+payload.__len__())
    return fixHeader+varHeader+payload

def PUBACK_Encoder(packetIdentifier):
    varHeader = int.to_bytes(packetIdentifier, 2, 'big')
    fixHeader = b''
    fixHeader += int.to_bytes(definition.messageType.PUBACK<<4,1,'big')
    fixHeader += remainingBytes_Encoder(varHeader.__len__())
    return fixHeader+varHeader

def PUBREC_Encoder(packetIdentifier):
    varHeader = int.to_bytes(packetIdentifier, 2, 'big')
    fixHeader = b''
    fixHeader += int.to_bytes(definition.messageType.PUBREC<<4,1,'big')
    fixHeader += remainingBytes_Encoder(varHeader.__len__())
    return fixHeader+varHeader

def PUBREL_Encoder(packetIdentifier):
    varHeader = int.to_bytes(packetIdentifier, 2, 'big')
    fixHeader = b''
    fixHeader += int.to_bytes((definition.messageType.PUBREL<<4)+2,1,'big')
    fixHeader += remainingBytes_Encoder(varHeader.__len__())
    return fixHeader+varHeader

def PUBCOMP_Encoder(packetIdentifier):
    varHeader = int.to_bytes(packetIdentifier, 2, 'big')
    fixHeader = b''
    fixHeader += int.to_bytes(definition.messageType.PUBCOMP<<4,1,'big')
    fixHeader += remainingBytes_Encoder(varHeader.__len__())
    return fixHeader+varHeader

def SUBSCRIBE_Encoder(packetIdentifier,topics):
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
    varHeader = int.to_bytes(packetIdentifier, 2, 'big')
    fixHeader = b''
    fixHeader += int.to_bytes(definition.messageType.UNSUBACK<<4,1,'big')
    fixHeader += remainingBytes_Encoder(varHeader.__len__())
    return fixHeader+varHeader

def PINGREQ_Encoder():
    fixHeader = b''
    fixHeader += int.to_bytes(definition.messageType.PINGREQ<<4,1,'big')
    fixHeader += int.to_bytes(0,1,'big')
    return fixHeader

def PINGRESP_Encoder():
    fixHeader = b''
    fixHeader += int.to_bytes(definition.messageType.PINGRESP<<4,1,'big')
    fixHeader += int.to_bytes(0,1,'big')
    return fixHeader

def DISCONNECT_Encoder():
    fixHeader = b''
    fixHeader += int.to_bytes(definition.messageType.DISCONNECT<<4,1,'big')
    fixHeader += int.to_bytes(0,1,'big')
    return fixHeader