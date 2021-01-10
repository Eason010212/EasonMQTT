import socket
import threading
import sys
import Encoders, Decoders, definition, time

subscribes = []
tmpSubscribes = []

SOCKET_DISCONNECTED = 0
SOCKET_CONNECTED = 1
MQTT_CONNECTED = 2

alive = SOCKET_DISCONNECTED
sessionPresent = 0
packetIdentifier = 0

def generatePacketIdentifier():
    global packetIdentifier
    if packetIdentifier < 1023:
        packetIdentifier = packetIdentifier+1
    else:
        packetIdentifier = 1
    return packetIdentifier

def getTime():
    return time.strftime("%H:%M:%S", time.localtime()) 

def receive(socket):
    global alive
    while alive!=SOCKET_DISCONNECTED:
        try:
            data = socket.recv(1024)
            decode(data)
        except:
            print("["+getTime()+"]"+" [SYSTEM/INFO] Socket Disconnected: Connection closed by server.")
            alive = SOCKET_DISCONNECTED
            break

def startClient(serverHost, serverPort, userNameFlag, passwordFlag, willRetain, willQos, willFlag, cleanSession, keepAlive, clientId, willTopic='', willMessage='', userName='', password=''):
    print("====Eason MQTT-Client v1.0====")
    global alive
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("["+getTime()+"]"+" [SYSTEM/INFO] Socket Connecting...")
        sock.connect((serverHost, serverPort))
    except:
        print("["+getTime()+"]"+" [SYSTEM/INFO] Socket Disconnected: Can not connect to server.")
        alive = SOCKET_DISCONNECTED
        input("Press ENTER to continue...")
        sys.exit(0)
    alive = SOCKET_CONNECTED
    print("["+getTime()+"]"+" [SYSTEM/INFO] Socket Connected.")
    receiveThread = threading.Thread(target = receive, args = (sock,))
    receiveThread.start()
    sendMessage(sock, Encoders.CONNECT_Encoder(userNameFlag, passwordFlag, willRetain, willQos, willFlag, cleanSession, keepAlive, clientId, willTopic, willMessage, userName, password))
    print("["+getTime()+"]"+" [SYSTEM/INFO] MQTT Connecting...")
    return sock

def sendMessage(sock, message):
    sock.sendall(message)

def subscribe(sock, topics):
    packetIdentifier = generatePacketIdentifier()
    tmpSubscribes.append({'packetIdentifier':packetIdentifier,'topics':topics})
    sendMessage(sock, Encoders.SUBSCRIBE_Encoder(packetIdentifier,topics))
    print("["+getTime()+"]"+" [SYSTEM/INFO] Packet "+str(packetIdentifier)+": Subscribing...")

def decode(data):
    global alive, sessionPresent,subscribes
    try:
        messageType, results = Decoders.message_Decoder(data)
        if messageType == definition.messageType.CONNACK:
            if results['sessionPresent'] == 0:
                subscribes = []
            if results['returnCode'] == definition.ConnackReturnCode.ACCEPTED:
                print("["+getTime()+"]"+" [SYSTEM/INFO] MQTT Connected!")
            elif results['returnCode'] == definition.ConnackReturnCode.REFUSED_ILLEGAL_CLIENTID:
                print("["+getTime()+"]"+" [SYSTEM/INFO] MQTT Disconnected: Illegal ClientID.")
                alive = SOCKET_DISCONNECTED
                sock.close()
            elif results['returnCode'] == definition.ConnackReturnCode.REFUSED_INVALID_USER:
                print("["+getTime()+"]"+" [SYSTEM/INFO] MQTT Disconnected: Invalid User.")
                alive = SOCKET_DISCONNECTED
                sock.close()
            elif results['returnCode'] == definition.ConnackReturnCode.REFUSED_SERVER_UNAVAILABLE:
                print("["+getTime()+"]"+" [SYSTEM/INFO] MQTT Disconnected: Server temporarily unavailable.")
                alive = SOCKET_DISCONNECTED
                sock.close()
            elif results['returnCode'] == definition.ConnackReturnCode.REFUSED_UNAUTHORIZED:
                print("["+getTime()+"]"+" [SYSTEM/INFO] MQTT Disconnected: Unauthorized.")
                alive = SOCKET_DISCONNECTED
                sock.close()
            elif results['returnCode'] == definition.ConnackReturnCode.REFUSED_UNSUPPORTED_PROTOCOL:
                print("["+getTime()+"]"+" [SYSTEM/INFO] MQTT Disconnected: Unsupported protocol.")
                alive = SOCKET_DISCONNECTED
                sock.close()
        elif messageType == definition.messageType.SUBACK:
            packetIdentifier = results['packetIdentifier']
            for i in range(0,tmpSubscribes.__len__()):
                if tmpSubscribes[i]['packetIdentifier'] == packetIdentifier:
                    for j in range(0,tmpSubscribes[i]['topics'].__len__()):
                        if results['returnCodes'][j] == definition.SubackReturnCode.FAILURE:
                            print("["+getTime()+"]"+" [SYSTEM/WARN] Subscribe failure at topic "+tmpSubscribes[i]['topics'][j]['topic']+".")
                        elif results['returnCodes'][j] == definition.SubackReturnCode.SUCCESS_MAX_QOS_0:
                            print("["+getTime()+"]"+" [SYSTEM/INFO] Subscribe success at topic "+tmpSubscribes[i]['topics'][j]['topic']+", Qos 0 .")
                            for k in range(0,subscribes.__len__()):
                                if subscribes[k]['topic'] == tmpSubscribes[i]['topics'][j]['topic']:
                                    subscribes.pop(k)
                            subscribes.append({'topic':tmpSubscribes[i]['topics'][j]['topic'],'qos':0})
                        elif results['returnCodes'][j] == definition.SubackReturnCode.SUCCESS_MAX_QOS_1:
                            print("["+getTime()+"]"+" [SYSTEM/INFO] Subscribe success at topic "+tmpSubscribes[i]['topics'][j]['topic']+", Qos 1 .")
                            for k in range(0,subscribes.__len__()):
                                if subscribes[k]['topic'] == tmpSubscribes[i]['topics'][j]['topic']:
                                    subscribes.pop(k)
                            subscribes.append({'topic':tmpSubscribes[i]['topics'][j]['topic'],'qos':1})
                        elif results['returnCodes'][j] == definition.SubackReturnCode.SUCCESS_MAX_QOS_2:
                            print("["+getTime()+"]"+" [SYSTEM/INFO] Subscribe success at topic "+tmpSubscribes[i]['topics'][j]['topic']+", Qos 2 .")
                            for k in range(0,subscribes.__len__()):
                                if subscribes[k]['topic'] == tmpSubscribes[i]['topics'][j]['topic']:
                                    subscribes.pop(k)
                            subscribes.append({'topic':tmpSubscribes[i]['topics'][j]['topic'],'qos':2})
            print("["+getTime()+"]"+" [SYSTEM/INFO] Current subscribes: "+str(subscribes)+" .")    
    except Decoders.IllegalMessageException:
        print("["+getTime()+"]"+" [SYSTEM/INFO] MQTT Disconnected: Illegal message received.")
        sock.close()

if __name__=="__main__":
    sock = startClient('localhost',8888,1,0,1,2,1,0,10,'eason0212','is','ijsfs','eason')
    time.sleep(1)
    subscribe(sock, [{'topic':'233','qos':1}])