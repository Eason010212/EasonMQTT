import socket
import threading, Decoders, definition, Encoders, time

connections = []
subscribes = []

def getTime():
    return time.strftime("%H:%M:%S", time.localtime()) 

def checkUser(userName, password):
    #0 = INVALID
    #1 = UNAUTHORIZED
    #2 = OK
    return 2

def checkSubscribe(clientId):
    res = 0
    for i in range(0,subscribes.__len__()):
        if subscribes[i]['clientId'] == clientId:
            res = 1
            break
    return res

def addSubscribe(clientId, topic, qos):
    subscribes.append({
        'clientId': clientId,
        'topic': topic,
        'qos': qos
    })

def removeSubscribe(clientId, topic = ''):
    delIndexs = []
    if topic == '':
        for i in range(0,subscribes.__len__()):
            if subscribes[i]['clientId'] == clientId:
                delIndexs.append(i)
    else:
        for i in range(0,subscribes.__len__()):
            if subscribes[i]['clientId'] == clientId and subscribes[i]['topic']== topic:
                delIndexs.append(i)
    while delIndexs.__len__()!=0:
        del subscribes[delIndexs.pop()]

class Connection(threading.Thread):

    SOCKET_DISCONNECTED = 0
    SOCKET_CONNECTED = 1
    MQTT_CONNECTED = 2

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
                        self.send(Encoders.CONNACK_Encoder(checkSubscribe(self.clientId), definition.ConnackReturnCode.ACCEPTED))
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
                print("["+getTime()+"]"+" [SYSTEM/INFO] Current subscirbes: " + str(subscribes) + " .")
            elif messageType == definition.messageType.UNSUBSCRIBE:
                print("["+getTime()+"]"+" [SYSTEM/INFO] Client " + str(self.address) + " unsubscribing...")
                packetIdentifier = results['packetIdentifier']
                topics = results['topics']
                for i in range(0,topics.__len__()):
                    removeSubscribe(self.clientId, topics[i])
                self.send(Encoders.UNSUBACK_Encoder(packetIdentifier))
                print("["+getTime()+"]"+" [SYSTEM/INFO] Client " + str(self.address) + " unsubscribed.")
                print("["+getTime()+"]"+" [SYSTEM/INFO] Current subscirbes: " + str(subscribes) + " .")

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
    print("====Eason MQTT-Server v1.0====")
    print("["+getTime()+"]"+" [SYSTEM/INFO] Successfully started!")
    print("["+getTime()+"]"+" [SYSTEM/INFO] running on "+host+":"+str(port))

startServer('localhost',8888)
    