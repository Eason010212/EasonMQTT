#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@file    :   Server.py
@time    :   2021/01/14 16:35:32
@author  :   宋义深 
@version :   1.0
@contact :   1371033826@qq.com 
@license :   GPL-3.0 License
@link    :   https://github.com/Eason010212/EasonMQTT
'''

import socket
import threading, Decoders, definition, Encoders, time
import sqlite3,traceback
from queue import Queue

ACK_TIMEOUT = 5

connections = []
messageQueue = Queue(0)
timeoutTimers = []
retainedMessages = []
packetIdentifier = 513

def checkFatherSon(fatherTopic, sonTopic):
    if (fatherTopic.__len__()-2)<sonTopic.__len__():
        try:
            sonTopic.index(fatherTopic[0:fatherTopic.__len__()-2])
            if sonTopic[fatherTopic.__len__()-2]=='/':
                return True
            else:
                return False
        except:
            return False
    else:
        return False

def generatePacketIdentifier():
    global packetIdentifier
    if packetIdentifier < 1024:
        packetIdentifier = packetIdentifier+1
    else:
        packetIdentifier = 513
    return packetIdentifier

def install():
    conn = sqlite3.connect('serverDB.db')
    cursor = conn.cursor()
    cursor.execute('create table if not exists subscription (clientId varchar(100), topic varchar(100), qos int(2))')
    cursor.close()
    conn.commit()
    conn.close()

def getTime():
    return time.strftime("%H:%M:%S", time.localtime()) 

def addRetain(messageItem):
    for i in range(0,retainedMessages.__len__()):
        if retainedMessages[i]['topic'] == messageItem['topic']:
            retainedMessages.pop(i)
            break
    retainedMessages.append(messageItem)

def checkUser(userName, password):
    #0 = INVALID
    #1 = UNAUTHORIZED
    #2 = OK
    return 2

def getAllSubscribe():
    conn = sqlite3.connect('serverDB.db')
    cursor = conn.cursor()
    cursor.execute('select * from subscription')
    res = cursor.fetchall()
    cursor.close()
    conn.commit()
    conn.close()
    return res

def getSubscribe(clientId):
    conn = sqlite3.connect('serverDB.db')
    cursor = conn.cursor()
    cursor.execute('select * from subscription where clientId = ? ',(clientId,))
    res = cursor.fetchall()
    cursor.close()
    conn.commit()
    conn.close()
    return res

def getSubscribers(topic):
    conn = sqlite3.connect('serverDB.db')
    topicStages = topic.split('/')
    topics = [topic]
    allRes = []
    for i in range(0,topicStages.__len__()-1):
        ntopic = '/'.join(topicStages[0:topicStages.__len__()-1-i])
        ntopic = ntopic+'/#'
        topics.append(ntopic)
    for qtopic in topics:
        cursor = conn.cursor()
        cursor.execute('select * from subscription where topic = ?',(qtopic,))
        res = cursor.fetchall()
        allRes.extend(res)
        cursor.close()
    conn.commit()
    conn.close()
    return allRes

def addSubscribe(clientId, topic, qos):
    conn = sqlite3.connect('serverDB.db')
    cursor = conn.cursor()
    cursor.execute('insert into subscription(clientId, topic, qos) values (\''+clientId+'\',\''+topic+'\','+str(qos)+')')
    cursor.close()
    conn.commit()
    conn.close()

def removeSubscribe(clientId, topic = ''):
    if topic == '':
        conn = sqlite3.connect('serverDB.db')
        cursor = conn.cursor()
        cursor.execute('delete from subscription where clientId = ?',(clientId,))
        cursor.close()
    else:
        conn = sqlite3.connect('serverDB.db')
        cursor = conn.cursor()
        cursor.execute('delete from subscription where clientId = ? and topic = ?',(clientId,topic))
        cursor.close()
    conn.commit()
    conn.close()

def pubackNotReceived(connection):
    print("["+getTime()+"]"+" [SYSTEM/INFO] Client " + connection.getAddress() + " has disconnected: Puback timeout.")
    connection.onDisconnect()

def pubrecNotReceived(connection):
    print("["+getTime()+"]"+" [SYSTEM/INFO] Client " + connection.getAddress() + " has disconnected: Pubrec timeout.")
    connection.onDisconnect()

def publishFromQueue():
    while True:
        if messageQueue.qsize() != 0:
            messageItem = messageQueue.get()
            subscribers = getSubscribers(messageItem['topic'])
            for i in range(0,subscribers.__len__()):
                subscriber = subscribers[i][0]
                qos = subscribers[i][2]
                if qos == 0:
                    for j in range (0,connections.__len__()):
                        if connections[j].getClientId()==subscriber:
                            connections[j].send(Encoders.PUBLISH_Encoder(0, qos, 0, messageItem['topic'], 0, messageItem['message']))
                elif qos == 1:
                    packetIdentifier = generatePacketIdentifier()
                    for j in range (0,connections.__len__()):
                        if connections[j].getClientId()==subscriber:
                            connections[j].send(Encoders.PUBLISH_Encoder(0, qos, 0, messageItem['topic'], packetIdentifier, messageItem['message']))
                            timer = threading.Timer(ACK_TIMEOUT, pubackNotReceived, [connections[j],])
                            timeoutTimers.append({
                                'clientId': connections[j].getClientId(),
                                'packetIdentifier': packetIdentifier,
                                'waitingFor': 'PUBACK',
                                'timer': timer
                            })
                            timer.start()
                elif qos == 2:
                    packetIdentifier = generatePacketIdentifier()
                    for j in range (0,connections.__len__()):
                        if connections[j].getClientId()==subscriber:
                            connections[j].send(Encoders.PUBLISH_Encoder(0, qos, 0, messageItem['topic'], packetIdentifier, messageItem['message']))
                            timer = threading.Timer(ACK_TIMEOUT, pubrecNotReceived, [connections[j],])
                            timeoutTimers.append({
                                'clientId': connections[j].getClientId(),
                                'packetIdentifier': packetIdentifier,
                                'waitingFor': 'PUBREC',
                                'timer': timer
                            })
                            timer.start()
            if messageItem['retain'] == 1:
                addRetain(messageItem)
            print("["+getTime()+"]"+" [SYSTEM/INFO] Queue processed a message." + str(messageQueue.qsize()) + " message(s) in queue, "+str(retainedMessages.__len__())+" message(s) retained.")

class Connection(threading.Thread):

    SOCKET_DISCONNECTED = 0
    SOCKET_CONNECTED = 1
    MQTT_CONNECTED = 2

    socketLock = threading.Lock()

    def getClientId(self):
        return self.clientId

    def getAddress(self):
        return str(self.address)

    def getSock(self):
        return self.socket

    def __init__(self, socket, address):
        threading.Thread.__init__(self)
        self.socket = socket
        self.address = address
        self.alive = 1
        self.clientId = ''
        self.keepAlive = 0
        self.count = 0
        self.willFlag = 0
        self.willTopic = ''
        self.willMessage = ''
        self.willQos = 0
        self.willRetain = 0

    def __str__(self):
        return str(self.address)

    def publishWill(self):
        pass

    def onDisconnect(self):
        self.alive = self.SOCKET_DISCONNECTED
        try:
            delIndexs = []
            for i in range(0, timeoutTimers.__len__()):
                if timeoutTimers[i]['clientId'] == self.clientId:
                    timeoutTimers[i]['timer'].cancel()
                    delIndexs.append(i)
            while delIndexs.__len__()!=0:
                timeoutTimers.pop(delIndexs.pop())
            connections.remove(self)
        except:
            pass
        self.socketLock.acquire()
        self.socket.close()
        self.socketLock.release()
        self.publishWill()

    def counter(self):
        while self.alive != self.SOCKET_DISCONNECTED:
            time.sleep(1)
            self.count = self.count+1
            if self.count >= self.keepAlive:
                print("["+getTime()+"]"+" [SYSTEM/INFO] Client " + str(self.address) + " has disconnected: Connection time out.")
                self.onDisconnect()
                break

    def run(self):
        while self.alive != self.SOCKET_DISCONNECTED:
            try:
                oneMessage = b''
                data = self.socket.recv(2)
                oneMessage += data
                remainedLengthBytes = b''
                remainedLengthBytes += int.to_bytes(data[1],1,'big')
                while data !=b'' and (data[data.__len__()-1] & 128 )!=0:
                    self.count = 0
                    data = self.socket.recv(1)
                    oneMessage += data
                    remainedLengthBytes += data
                data = self.socket.recv(Decoders.remainingBytes_Decoder(remainedLengthBytes,True)[1])
                oneMessage += data
            except Exception as e:
                print(traceback.format_exc())
                print("["+getTime()+"]"+" [SYSTEM/INFO] Client " + str(self.address) + " has disconnected.")
                self.onDisconnect()
                break
            if oneMessage != b'':
                self.decode(oneMessage)

    def pubcompNotReceived(self):
        print("["+getTime()+"]"+" [SYSTEM/INFO] Client " + self.getAddress() + " has disconnected: Pubcomp timeout.")
        self.onDisconnect()
    
    def decode(self, data):
        if data == b'':
            return
        try:
            messageType, results = Decoders.message_Decoder(data)
            if messageType == definition.messageType.CONNECT:
                if results['clientId'].isalnum() and results['clientId'].__len__()>=1 and results['clientId'].__len__()<=23:
                    self.clientId = results['clientId']
                    if checkUser(results['userName'], results['password'])==2:
                        if results['cleanSession']==1:
                            removeSubscribe(results['clientId'])
                        self.keepAlive = results['keepAlive']
                        self.willFlag = results['willFlag']
                        if self.willFlag==1:
                            self.willTopic = results['willTopic']
                            self.willMessage = results['willMessage']
                            self.willQos = results['willQos']
                            self.willRetain = results['willRetain']
                        print("["+getTime()+"]"+" [SYSTEM/INFO] Client " + str(self.address) + " has connected.")
                        sessionPresent = getSubscribe(self.clientId).__len__()
                        if sessionPresent >0:
                            sessionPresent = 1
                        self.send(Encoders.CONNACK_Encoder(sessionPresent, definition.ConnackReturnCode.ACCEPTED))
                        scs = getSubscribe(self.clientId)
                        for sc in scs:
                            for retainedMessage in retainedMessages:
                                if checkFatherSon(retainedMessage['topic'],sc[1]) or retainedMessage['topic']==sc[1]:
                                    packetIdentifier = generatePacketIdentifier()
                                    self.send(Encoders.PUBLISH_Encoder(0,sc[2],0,retainedMessage['topic'],packetIdentifier,retainedMessage['message']))
                                    if sc[2]==2:
                                        timer = threading.Timer(ACK_TIMEOUT, pubrecNotReceived, [self,])
                                        timeoutTimers.append({
                                            'clientId': self.getClientId(),
                                            'packetIdentifier': packetIdentifier,
                                            'waitingFor': 'PUBREC',
                                            'timer': timer
                                        })
                                        timer.start()
                                    elif sc[2]==1:
                                        timer = threading.Timer(ACK_TIMEOUT, pubackNotReceived, [self,])
                                        timeoutTimers.append({
                                            'clientId': self.getClientId(),
                                            'packetIdentifier': packetIdentifier,
                                            'waitingFor': 'PUBACK',
                                            'timer': timer
                                        })
                                        timer.start()
                                    print("["+getTime()+"]"+" [SYSTEM/INFO] A retained message sent to Client " + str(self.address) + " at packet "+str(packetIdentifier)+" .")
                                    retainedMessages.remove(retainedMessage)
                                    break
                        keepAliveThread = threading.Thread(target = self.counter)
                        keepAliveThread.start()
                    elif checkUser(results['userName'], results['password'])==0:
                        self.send(Encoders.CONNACK_Encoder(0, definition.ConnackReturnCode.REFUSED_INVALID_USER))
                        print("["+getTime()+"]"+" [SYSTEM/INFO] Client " + str(self.address) + " has disconnected: Illegal User or Password.")
                        self.onDisconnect()
                    else:
                        self.send(Encoders.CONNACK_Encoder(0, definition.ConnackReturnCode.REFUSED_UNAUTHORIZED))
                        print("["+getTime()+"]"+" [SYSTEM/INFO] Client " + str(self.address) + " has disconnected: Unauthorized user.")
                        self.onDisconnect()
                else:
                    self.send(Encoders.CONNACK_Encoder(0, definition.ConnackReturnCode.REFUSED_ILLEGAL_CLIENTID))
                    print("["+getTime()+"]"+" [SYSTEM/INFO] Client " + str(self.address) + " has disconnected: Illegal ClientId.")
                    self.onDisconnect()
            elif messageType == definition.messageType.SUBSCRIBE:
                print("["+getTime()+"]"+" [SYSTEM/INFO] Client " + str(self.address) + " subscribing...")
                packetIdentifier = results['packetIdentifier']
                topics = results['topics']
                returnCodes = []
                for i in range(0,topics.__len__()):
                    removeSubscribe(self.clientId, topics[i]['topic'])
                    addSubscribe(self.clientId, topics[i]['topic'], topics[i]['qos'])
                    returnCodes.append(topics[i]['qos'])
                self.send(Encoders.SUBACK_Encoder(packetIdentifier,returnCodes))
                print("["+getTime()+"]"+" [SYSTEM/INFO] Client " + str(self.address) + " subscribed.")
                print("["+getTime()+"]"+" [SYSTEM/INFO] Current subscirbes: " + str(getAllSubscribe()) + " .")
            elif messageType == definition.messageType.UNSUBSCRIBE:
                print("["+getTime()+"]"+" [SYSTEM/INFO] Client " + str(self.address) + " unsubscribing...")
                packetIdentifier = results['packetIdentifier']
                topics = results['topics']
                for i in range(0,topics.__len__()):
                    removeSubscribe(self.clientId, topics[i])
                self.send(Encoders.UNSUBACK_Encoder(packetIdentifier))
                print("["+getTime()+"]"+" [SYSTEM/INFO] Client " + str(self.address) + " unsubscribed.")
                print("["+getTime()+"]"+" [SYSTEM/INFO] Current subscirbes: " + str(getAllSubscribe()) + " .")
            elif messageType == definition.messageType.PINGREQ:
                print("["+getTime()+"]"+" [SYSTEM/INFO] Client " + str(self.address) + " sent a heartbeat.")
                self.send(Encoders.PINGRESP_Encoder())
            elif messageType == definition.messageType.PUBLISH:
                print("["+getTime()+"]"+" [SYSTEM/INFO] Client " + str(self.address) + " sent a message.")
                messageQueue.put({
                    'retain': results['retain'],
                    'topic': results['topic'],
                    'message': results['message']
                })
                if results['qos'] == 1:
                    self.send(Encoders.PUBACK_Encoder(results['packetIdentifier']))
                    print("["+getTime()+"]"+" [SYSTEM/INFO] PUBACK responded to Client " + str(self.address) + " at packet "+str(results['packetIdentifier'])+" .")
                elif results['qos'] == 2:
                    self.send(Encoders.PUBREC_Encoder(results['packetIdentifier']))
                    print("["+getTime()+"]"+" [SYSTEM/INFO] PUBREC responded to Client " + str(self.address) + " at packet "+str(results['packetIdentifier'])+" .")
            elif messageType == definition.messageType.PUBREL:
                self.send(Encoders.PUBCOMP_Encoder(results['packetIdentifier']))
                print("["+getTime()+"]"+" [SYSTEM/INFO] PUBCOMP responded to Client " + str(self.address) + " at packet "+str(results['packetIdentifier'])+" .")
            elif messageType == definition.messageType.PUBACK:
                print("["+getTime()+"]"+" [SYSTEM/INFO] Client " + str(self.address) + " responded a PUBACK.")
                clientId = self.clientId
                packetIdentifier = results['packetIdentifier']
                try:
                    for i in range(0, timeoutTimers.__len__()):
                        if timeoutTimers[i]['packetIdentifier'] == packetIdentifier and timeoutTimers[i]['clientId'] == clientId and timeoutTimers[i]['waitingFor'] == 'PUBACK':
                            timeoutTimers[i]['timer'].cancel()
                except:
                    pass
            elif messageType == definition.messageType.PUBREC:
                print("["+getTime()+"]"+" [SYSTEM/INFO] Client " + str(self.address) + " responded a PUBREC.")
                clientId = self.clientId
                packetIdentifier = results['packetIdentifier']
                self.send(Encoders.PUBREL_Encoder(packetIdentifier))
                print("["+getTime()+"]"+" [SYSTEM/INFO] PUBREL responded to Client " + str(self.address) + " at packet "+str(packetIdentifier)+" .")
                try:
                    for i in range(0, timeoutTimers.__len__()):
                        if timeoutTimers[i]['packetIdentifier'] == packetIdentifier and timeoutTimers[i]['clientId'] == clientId and timeoutTimers[i]['waitingFor'] == 'PUBREC':
                            timeoutTimers[i]['timer'].cancel()
                            break
                    timer = threading.Timer(ACK_TIMEOUT, self.pubcompNotReceived)
                    timeoutTimers.append({
                            'clientId': self.getClientId(),
                            'packetIdentifier': packetIdentifier,
                            'waitingFor': 'PUBCOMP',
                            'timer': timer
                    })
                    timer.start()
                except:
                    pass
            elif messageType == definition.messageType.PUBCOMP:
                print("["+getTime()+"]"+" [SYSTEM/INFO] Client " + str(self.address) + " responded a PUBCOMP.")
                clientId = self.clientId
                packetIdentifier = results['packetIdentifier']
                try:
                    for i in range(0, timeoutTimers.__len__()):
                        if timeoutTimers[i]['packetIdentifier'] == packetIdentifier and timeoutTimers[i]['clientId'] == clientId and timeoutTimers[i]['waitingFor'] == 'PUBCOMP':
                            timeoutTimers[i]['timer'].cancel()
                            break
                except:
                    pass
            elif messageType == definition.messageType.DISCONNECT:
                self.onDisconnect()
                print("["+getTime()+"]"+" [SYSTEM/INFO] Client " + str(self.address) + " has disconnected.")
        except Decoders.IllegalMessageException:
            print(data)
            print("["+getTime()+"]"+" [SYSTEM/INFO] Client " + str(self.address) + " has disconnected: Illegal Message Received.")
            self.onDisconnect()

    def send(self, data):
        self.socketLock.acquire()
        try:
            self.socket.sendall(data)
        except:
            pass
        self.socketLock.release()

def newConnections(socket):
    while True:
        sock, address = socket.accept()
        connections.append(Connection(sock, address))
        connections[len(connections) - 1].start()
        print("["+getTime()+"]"+" [SYSTEM/INFO] New connection at " + str(connections[len(connections) - 1]))

def startServer(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((host, port))
    sock.listen(128)
    newConnectionsThread = threading.Thread(target = newConnections, args = (sock,))
    newConnectionsThread.start()
    messageQueueThread = threading.Thread(target = publishFromQueue)
    messageQueueThread.start()
    print("====Eason MQTT-Server v1.0====")
    print("["+getTime()+"]"+" [SYSTEM/INFO] Successfully started!")
    print("["+getTime()+"]"+" [SYSTEM/INFO] running on "+host+":"+str(port))

#install()
startServer('localhost',8888)