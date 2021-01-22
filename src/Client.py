# -*-coding:utf-8 -*-
'''
@file    :   Client.py
@time    :   2021/01/21 17:15:51
@author  :   宋义深 
@version :   1.0
@contact :   1371033826@qq.com 
@license :   GPL-3.0 License
@link    :   https://github.com/Eason010212/EasonMQTT
'''

import socket
import threading
import sys
import Encoders, Decoders, definition, time

subscribes = []
tmpSubscribes = []
tmpUnsubscribes = []
tmpPublishAtQos1 = []
tmpPublishAtQos2 = []
tmpReceiveAtQos2 = []
messageReceived = []

SOCKET_DISCONNECTED = 0
SOCKET_CONNECTED = 1
MQTT_CONNECTED = 2

alive = SOCKET_DISCONNECTED
sessionPresent = 0
packetIdentifier = 0
socketLock = threading.Lock()

def generatePacketIdentifier():
    """
        Description:
            生成短期内唯一的报文标识符。
        Args:
            None
        Returns:
            生成的报文标识符。
        Raises:
            None
    """
    global packetIdentifier
    if packetIdentifier < 511:
        packetIdentifier = packetIdentifier+1
    else:
        packetIdentifier = 1
    return packetIdentifier

def getTime():
    """
        Description:
            获取用以在控制台进行输出的当前时间字符串。
        Args:
            None
        Returns:
            string
                当前时间字符串。
        Raises:
            None
    """
    return time.strftime("%H:%M:%S", time.localtime()) 

def receive(socket):
    """
        Description:
            接收消息的主方法，基于剩余长度实现帧定界，并传递给解码方法。
        Args:
            socket(Socket):
                客户端socket对象。
        Returns:
            None
        Raises:
            None
    """
    global alive
    while alive!=SOCKET_DISCONNECTED:
        try:
            oneMessage = b''
            data = socket.recv(2)
            if data != b'':
                oneMessage += data
                remainedLengthBytes = b''
                remainedLengthBytes += int.to_bytes(data[1],1,'big')
                while data !=b'' and (data[data.__len__()-1] & 128 )!=0:
                    data = socket.recv(1)
                    oneMessage += data
                    remainedLengthBytes += data
                data = socket.recv(Decoders.remainingBytes_Decoder(remainedLengthBytes,True)[1])
                oneMessage += data
            if oneMessage != b'':
                decode(oneMessage,socket)
        except Exception as e:
            print("["+getTime()+"]"+" [CLIENT/INFO] Socket Disconnected: Connection closed by server.")
            alive = SOCKET_DISCONNECTED
            break

def startClient(serverHost, serverPort, userNameFlag, passwordFlag, willRetain, willQos, willFlag, cleanSession, keepAlive, clientId, willTopic='', willMessage='', userName='', password=''):
    """
        Description:
            启动客户端。
        Args:
            serverHost(string)
                服务器地址。
            serverPort(int)
                服务器端口。
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
            Socket:
                客户端socket对象。
        Raises:
            IOException
                socket连接错误。
    """
    print("====Eason MQTT-Client v1.0====")
    global alive
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(True)
        print("["+getTime()+"]"+" [CLIENT/INFO] Socket Connecting...")
        sock.connect((serverHost, serverPort))
    except:
        print("["+getTime()+"]"+" [CLIENT/INFO] Socket Disconnected: Can not connect to server.")
        alive = SOCKET_DISCONNECTED
        input("Press ENTER to continue...")
        sys.exit(0)
    alive = SOCKET_CONNECTED
    print("["+getTime()+"]"+" [CLIENT/INFO] Socket Connected.")
    receiveThread = threading.Thread(target = receive, args = (sock,))
    receiveThread.start()
    sendMessage(sock, Encoders.CONNECT_Encoder(userNameFlag, passwordFlag, willRetain, willQos, willFlag, cleanSession, keepAlive, clientId, willTopic, willMessage, userName, password))
    print("["+getTime()+"]"+" [CLIENT/INFO] MQTT Connecting...")
    return sock

def sendMessage(sock, message):
    """
        Description:
            在给定的socket连接中发送消息。
        Args:
            sock(Socket):
                客户端socket对象。
            message(byte[]):
                将要发送的字节串。
        Returns:
            None
        Raises:
            IOException
                socket连接错误。
    """
    socketLock.acquire()
    sock.sendall(message)
    socketLock.release()

def removeSubscribe(topic):
    """
        Description:
            从本地存储中移除特定的订阅主题（非向服务器请求取消订阅）。
        Args:
            topic(string)
                移除的主题名。
        Returns:
            None
        Raises:
            None
    """
    for k in range(0,subscribes.__len__()):
        if subscribes[k]['topic'] == topic:
            subscribes.pop(k)
            break

def subscribe(sock, topics):
    """
        Description:
            订阅一组主题消息。
        Args:
            sock(Socket):
                客户端socket对象。
            topics(array[dict]):
                将要订阅的主题数组，数组单元为主题字典，必须包含topic和qos两个字段。
        Returns:
            packetIdentifier(int)
                本次请求使用的报文标识符。
        Raises:
            IOException
                socket连接异常。
    """
    packetIdentifier = generatePacketIdentifier()
    tmpSubscribes.append({'packetIdentifier':packetIdentifier,'topics':topics})
    sendMessage(sock, Encoders.SUBSCRIBE_Encoder(packetIdentifier,topics))
    print("["+getTime()+"]"+" [CLIENT/INFO] Packet "+str(packetIdentifier)+": Subscribing...")
    return packetIdentifier

def unsubscribe(sock, topics):
    """
        Description:
            取消订阅一组主题消息。
        Args:
            sock(Socket):
                客户端socket对象。
            topics(array[string]):
                将要取消订阅的主题数组，数组单元为主题字符串。
        Returns:
            packetIdentifier(int)
                本次请求使用的报文标识符。
        Raises:
            IOException
                socket连接异常。
    """
    packetIdentifier = generatePacketIdentifier()
    tmpUnsubscribes.append({'packetIdentifier':packetIdentifier,'topics':topics})
    sendMessage(sock, Encoders.UNSUBSCRIBE_Encoder(packetIdentifier,topics))
    print("["+getTime()+"]"+" [CLIENT/INFO] Packet "+str(packetIdentifier)+": Unsubscribing...")
    return packetIdentifier

def disconnect(sock):
    """
        Description:
            主动断开与服务端的连接。
        Args:
            sock(Socket):
                客户端socket对象。
        Returns:
            None
        Raises:
            IOException
                socket连接异常。
    """
    print("["+getTime()+"]"+" [CLIENT/INFO] Sending DISCONNECT message...")
    sendMessage(sock, Encoders.DISCONNECT_Encoder())

def ping(sock):
    """
        Description:
            向服务器发送PING请求。
        Args:
            sock(Socket):
                客户端socket对象。
        Returns:
            None
        Raises:
            IOException
                socket连接异常。
    """
    print("["+getTime()+"]"+" [CLIENT/INFO] Sending heartbeat...")
    sendMessage(sock, Encoders.PINGREQ_Encoder())
    print("["+getTime()+"]"+" [CLIENT/INFO] Heartbeat sent.")

def publishAtQos0(sock, topic, message, retain):
    """
        Description:
            发送一则服务质量等级为0的消息。
        Args:
            sock(Socket):
                客户端socket对象。
            topic(string):
                消息主题。
            message(string):
                消息内容。
            retain(int):
                消息保留标志。
        Returns:
            None
        Raises:
            IOException
                socket连接异常。
    """
    sendMessage(sock, Encoders.PUBLISH_Encoder(0, 0, retain, topic, 0, message))
    print("["+getTime()+"]"+" [CLIENT/INFO] Message published at Qos0" + ".")

def publishAtQos1(sock, topic, message, retain):
    """
        Description:
            发送一则服务质量等级为1的消息。
        Args:
            sock(Socket):
                客户端socket对象。
            topic(string):
                消息主题。
            message(string):
                消息内容。
            retain(int):
                消息保留标志。
        Returns:
            packetIdentifier(int)
                本次请求使用的报文标识符。
        Raises:
            IOException
                socket连接异常。
    """
    packetIdentifier = generatePacketIdentifier()
    sendMessage(sock, Encoders.PUBLISH_Encoder(0,1,retain,topic,packetIdentifier,message))
    tmpPublishAtQos1.append({
        "packetIdentifier":packetIdentifier,
        "waitingFor":'PUBACK'
    })
    return packetIdentifier

def publishAtQos2(sock, topic, message, retain):
    """
        Description:
            发送一则服务质量等级为2的消息。
        Args:
            sock(Socket):
                客户端socket对象。
            topic(string):
                消息主题。
            message(string):
                消息内容。
            retain(int):
                消息保留标志。
        Returns:
            packetIdentifier(int)
                本次请求使用的报文标识符。
        Raises:
            IOException
                socket连接异常。
    """
    packetIdentifier = generatePacketIdentifier()
    sendMessage(sock, Encoders.PUBLISH_Encoder(0,2,retain,topic,packetIdentifier,message))
    tmpPublishAtQos2.append({
        "packetIdentifier":packetIdentifier,
        "waitingFor":'PUBREC'
    })
    return packetIdentifier

def decode(data,sock):
    """
        Description:
            解码报文，并做出对应的逻辑响应。
        Args:
            data(byte[]):
                待解码的报文字符串。
            sock(Socket):
                客户端socket对象。
        Returns:
            None
        Raises:
            IOException
                socket连接异常。
            Decoders.IllegalMessageException
                报文解码异常。
    """
    global alive, sessionPresent,subscribes
    try:
        messageType, results = Decoders.message_Decoder(data)
        if messageType == definition.messageType.CONNACK:
            if results['sessionPresent'] == 0:
                subscribes = []
            if results['returnCode'] == definition.ConnackReturnCode.ACCEPTED:
                print("["+getTime()+"]"+" [CLIENT/INFO] MQTT Connected!")
            elif results['returnCode'] == definition.ConnackReturnCode.REFUSED_ILLEGAL_CLIENTID:
                print("["+getTime()+"]"+" [CLIENT/INFO] MQTT Disconnected: Illegal ClientID.")
                alive = SOCKET_DISCONNECTED
                sock.close()
            elif results['returnCode'] == definition.ConnackReturnCode.REFUSED_INVALID_USER:
                print("["+getTime()+"]"+" [CLIENT/INFO] MQTT Disconnected: Invalid User.")
                alive = SOCKET_DISCONNECTED
                sock.close()
            elif results['returnCode'] == definition.ConnackReturnCode.REFUSED_SERVER_UNAVAILABLE:
                print("["+getTime()+"]"+" [CLIENT/INFO] MQTT Disconnected: Server temporarily unavailable.")
                alive = SOCKET_DISCONNECTED
                sock.close()
            elif results['returnCode'] == definition.ConnackReturnCode.REFUSED_UNAUTHORIZED:
                print("["+getTime()+"]"+" [CLIENT/INFO] MQTT Disconnected: Unauthorized.")
                alive = SOCKET_DISCONNECTED
                sock.close()
            elif results['returnCode'] == definition.ConnackReturnCode.REFUSED_UNSUPPORTED_PROTOCOL:
                print("["+getTime()+"]"+" [CLIENT/INFO] MQTT Disconnected: Unsupported protocol.")
                alive = SOCKET_DISCONNECTED
                sock.close()
        elif messageType == definition.messageType.SUBACK:
            packetIdentifier = results['packetIdentifier']
            for i in range(0,tmpSubscribes.__len__()):
                if tmpSubscribes[i]['packetIdentifier'] == packetIdentifier:
                    for j in range(0,tmpSubscribes[i]['topics'].__len__()):
                        if results['returnCodes'][j] == definition.SubackReturnCode.FAILURE:
                            print("["+getTime()+"]"+" [CLIENT/WARN] Subscribe failure at topic "+tmpSubscribes[i]['topics'][j]['topic']+".")
                        elif results['returnCodes'][j] == definition.SubackReturnCode.SUCCESS_MAX_QOS_0:
                            print("["+getTime()+"]"+" [CLIENT/INFO] Subscribe success at topic "+tmpSubscribes[i]['topics'][j]['topic']+", Qos 0 .")
                            removeSubscribe(tmpSubscribes[i]['topics'][j]['topic'])
                            subscribes.append({'topic':tmpSubscribes[i]['topics'][j]['topic'],'qos':0})
                        elif results['returnCodes'][j] == definition.SubackReturnCode.SUCCESS_MAX_QOS_1:
                            print("["+getTime()+"]"+" [CLIENT/INFO] Subscribe success at topic "+tmpSubscribes[i]['topics'][j]['topic']+", Qos 1 .")
                            removeSubscribe(tmpSubscribes[i]['topics'][j]['topic'])
                            subscribes.append({'topic':tmpSubscribes[i]['topics'][j]['topic'],'qos':1})
                        elif results['returnCodes'][j] == definition.SubackReturnCode.SUCCESS_MAX_QOS_2:
                            print("["+getTime()+"]"+" [CLIENT/INFO] Subscribe success at topic "+tmpSubscribes[i]['topics'][j]['topic']+", Qos 2 .")
                            removeSubscribe(tmpSubscribes[i]['topics'][j]['topic'])
                            subscribes.append({'topic':tmpSubscribes[i]['topics'][j]['topic'],'qos':2})
                    tmpSubscribes.pop(i)
                    break
            print("["+getTime()+"]"+" [CLIENT/INFO] Current subscribes: "+str(subscribes)+" .")
        elif messageType == definition.messageType.UNSUBACK:
            packetIdentifier = results['packetIdentifier']
            for i in range(0,tmpUnsubscribes.__len__()):
                if tmpUnsubscribes[i]['packetIdentifier'] == packetIdentifier:
                    for j in range(0,tmpUnsubscribes[i]['topics'].__len__()):
                        removeSubscribe(tmpUnsubscribes[i]['topics'][j])
                    tmpUnsubscribes.pop(i)
                    print("["+getTime()+"]"+" [CLIENT/INFO] Packet "+str(packetIdentifier)+": Unsubscribe success.")
                    break
            print("["+getTime()+"]"+" [CLIENT/INFO] Current subscribes: "+str(subscribes)+" .")
        elif messageType == definition.messageType.PUBACK:
            packetIdentifier = results['packetIdentifier']
            print("["+getTime()+"]"+" [CLIENT/INFO] Packet "+str(packetIdentifier)+": PUBACK received.")
            for i in range (0,tmpPublishAtQos1.__len__()):
                if tmpPublishAtQos1[i]['packetIdentifier'] == packetIdentifier and tmpPublishAtQos1[i]['waitingFor'] == 'PUBACK':
                    tmpPublishAtQos1.pop(i)
                    break
        elif messageType == definition.messageType.PUBREC:
            packetIdentifier = results['packetIdentifier']
            print("["+getTime()+"]"+" [CLIENT/INFO] Packet "+str(packetIdentifier)+": PUBREC received.")
            sendMessage(sock,Encoders.PUBREL_Encoder(packetIdentifier))
            print("["+getTime()+"]"+" [CLIENT/INFO] Packet "+str(packetIdentifier)+": PUBREL sent.")
            for i in range (0,tmpPublishAtQos2.__len__()):
                if tmpPublishAtQos2[i]['packetIdentifier'] == packetIdentifier and tmpPublishAtQos2[i]['waitingFor'] == 'PUBREC':
                    tmpPublishAtQos2[i]['waitingFor'] = 'PUBCOMP'
                    break
        elif messageType == definition.messageType.PUBCOMP:
            packetIdentifier = results['packetIdentifier']
            print("["+getTime()+"]"+" [CLIENT/INFO] Packet "+str(packetIdentifier)+": PUBCOMP received.")
            for i in range (0,tmpPublishAtQos2.__len__()):
                if tmpPublishAtQos2[i]['packetIdentifier'] == packetIdentifier and tmpPublishAtQos2[i]['waitingFor'] == 'PUBCOMP':
                    tmpPublishAtQos2.pop(i)
                    break
        elif messageType == definition.messageType.PUBLISH:
            qos = results['qos']
            topic = results['topic']
            message = results['message']
            packetIdentifier = results['packetIdentifier']
            if qos == 0:
                print("["+getTime()+"]"+" [CLIENT/INFO] A message received: topic - "+topic+" , message - "+message+" .")
                messageReceived.append({
                    'topic': topic,
                    'message': message
                })
            elif qos == 1:
                print("["+getTime()+"]"+" [CLIENT/INFO] A message received: topic - "+topic+" , message - "+message+" .")
                messageReceived.append({
                    'topic': topic,
                    'message': message
                })
                sendMessage(sock, Encoders.PUBACK_Encoder(packetIdentifier))
                print("["+getTime()+"]"+" [CLIENT/INFO] Packet "+str(packetIdentifier)+": PUBACK sent.")
            elif qos == 2:
                print("["+getTime()+"]"+" [CLIENT/INFO] A message received but not confirmed: topic - "+topic+" , message - "+message+" .")
                tmpReceiveAtQos2.append({
                    'packetIdentifier': packetIdentifier,
                    'topic': topic,
                    'message': message
                })
                sendMessage(sock, Encoders.PUBREC_Encoder(packetIdentifier))
                print("["+getTime()+"]"+" [CLIENT/INFO] Packet "+str(packetIdentifier)+": PUBREC sent.")
        elif messageType == definition.messageType.PUBREL:
            packetIdentifier = results['packetIdentifier']
            print("["+getTime()+"]"+" [CLIENT/INFO] Packet "+str(packetIdentifier)+": PUBREL received.")
            for i in range(0,tmpReceiveAtQos2.__len__()):
                if tmpReceiveAtQos2[i]['packetIdentifier'] == packetIdentifier:
                    res = tmpReceiveAtQos2.pop(i)
                    messageReceived.append({
                        'topic': res['topic'],
                        'message': res['message']
                    })
                    print("["+getTime()+"]"+" [CLIENT/INFO] A message received and confirmed: topic - "+res['topic']+" , message - "+res['message']+" .")
                    sendMessage(sock, Encoders.PUBCOMP_Encoder(packetIdentifier))
                    print("["+getTime()+"]"+" [CLIENT/INFO] Packet "+str(packetIdentifier)+": PUBCOMP sent.")
                    break
        elif messageType == definition.messageType.PINGRESP:
            print("["+getTime()+"]"+" [CLIENT/INFO] Heartbeat response received.")
    except Decoders.IllegalMessageException as e:
        print(data)
        print("["+getTime()+"]"+" [CLIENT/INFO] MQTT Disconnected: Illegal message received.")
        sock.close()

def checkPackageStatus(packetIdenifier):
    """
        Description:
            检查报文标识符对应的报文是否已按对应的服务质量等级完成交互。
        Args:
            packetIdentifier(int)
                待检查报文的报文标识符。
        Returns:
            boolean
                True - 已完成交互；False - 尚未完成交互。
        Raises:
            None
    """
    global tmpSubscribes, tmpUnsubscribes, tmpPublishAtQos1, tmpPublishAtQos2
    for m in tmpSubscribes:
        if m['packetIdentifier'] == packetIdenifier:
            return False
    for m in tmpUnsubscribes:
        if m['packetIdentifier'] == packetIdenifier:
            return False
    for m in tmpPublishAtQos1:
        if m['packetIdentifier'] == packetIdenifier:
            return False
    for m in tmpPublishAtQos2:
        if m['packetIdentifier'] == packetIdenifier:
            return False
    return True
