from __future__ import print_function
import socket               # Import socket module
import atexit

class SpawnedClient:
    # Constructor
    def __init__(self, serverIP, port, filename, CLIENT_NAME):
        self.CLIENT_NAME = CLIENT_NAME
        self.logfile = filename
        self.serverIP = serverIP
        self.port = port
        self.outputFile = open(self.logfile, 'w')
        self.terminate = False
    
    # Logging method
    def logToFile(self, msg):
        self.outputFile.write(msg)
        self.outputFile.write("\n")
        self.outputFile.flush()

    def spawnedClient(self):
        # print("[DEBUG] called spawned client")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        serverAddress = (self.serverIP, self.port)
        # Message Type: register <client1>
        clientRegisterMsg = "register " + self.CLIENT_NAME
        sock.sendto(clientRegisterMsg, serverAddress)
        # log
        self.logToFile("connecting to the server " + serverAddress[0] + " at port " + str(serverAddress[1]))
        self.logToFile("sending register message " + self.CLIENT_NAME)
        while not self.terminate:
            serverMsgData = sock.recv(1024)
            # print("[DEBUG] Received message from server :", serverMsgData)
            serverMsgDataList = serverMsgData.split()
            
            if len(serverMsgDataList) == 2 and serverMsgDataList[0] == "welcome" and serverMsgDataList[1].lower() == self.CLIENT_NAME.lower():
                serverWelcomeMsg = serverMsgDataList[0]
                # log print
                self.logToFile("received " + serverWelcomeMsg)
            elif len(serverMsgDataList) > 2 and serverMsgDataList[0] == "recvfrom":
                # print(serverMsgData)
                self.logToFile(serverMsgData)
            else:
                print("[ERROR] Recieved incorrect server msg format")

    def exit(self):
        # print("[DEBUG] terminated by server")
        self.logToFile("terminating client...")
        self.terminate = True














