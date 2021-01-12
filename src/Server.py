import socket
import threading, Decoders, definition, Encoders, time
import sqlite3
from queue import Queue

connections = []
messageQueue = Queue(0)
retainedMessages = []

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
    cursor = conn.cursor()
    cursor.execute('select * from subscription where topic = ?',(topic,))
    res = cursor.fetchall()
    cursor.close()
    conn.commit()
    conn.close()
    return res

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

def publishFromQueue():
    while True:
        if messageQueue.qsize() != 0:
            messageItem = messageQueue.get()
            subscribers = getSubscribers(messageItem['topic'])
            for i in range(0,subscribers.__len__()):
                subscriber = subscribers[i][0]
                qos = subscribers[i][2]
                for j in range (0,connections.__len__()):
                    if connections[j].getClientId()==subscriber:
                        connections[j].send(Encoders.PUBLISH_Encoder(0, qos, 0,messageItem['topic'],0,messageItem['message']))
                if messageItem['retain'] == 1:
                    addRetain(retainedMessages)
            print("["+getTime()+"]"+" [SYSTEM/INFO] Queue processed a message." + str(messageQueue.qsize()) + " message(s) in queue, "+str(retainedMessages.__len__())+" message(s) retained.")
            
class Connection(threading.Thread):

    SOCKET_DISCONNECTED = 0
    SOCKET_CONNECTED = 1
    MQTT_CONNECTED = 2

    def getClientId(self):
        return self.clientId

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
            connections.remove(self)
        except:
            pass
        self.socket.close()
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
                data = self.socket.recv(1024)
                if data != b'':
                    self.count = 0
            except:
                print("["+getTime()+"]"+" [SYSTEM/INFO] Client " + str(self.address) + " has disconnected.")
                self.onDisconnect()
                break
            if data != "":
                self.decode(data)
    
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
                    'qos': results['qos'],
                    'dup': results['dup'],
                    'retain': results['retain'],
                    'topic': results['topic'],
                    'message': results['message'],
                    'packetIdentifier': results['packetIdentifier']
                })
                print("["+getTime()+"]"+" [SYSTEM/INFO] " + str(messageQueue.qsize()) + " message(s) in queue.")
        except Decoders.IllegalMessageException:
            print("["+getTime()+"]"+" [SYSTEM/INFO] Client " + str(self.address) + " has disconnected: Illegal Message Received.")
            self.onDisconnect()

    def send(self, data):
        self.socket.sendall(data)

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
    