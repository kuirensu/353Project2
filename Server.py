from __future__ import print_function
import socket               								# Import socket module
import argparse                                             # Import argparse module
import atexit
import thread
import threading
import os
import SpawnedClient as SpawnedClient
# Part 1,2,3 Done

# Required arguments specification
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("-p", "--port", type=int, help="the port number for the chat server", required=True)
parser.add_argument("-l", "--logfile", help="name of logfile", required=True)
parser.add_argument("-h", "--handler", type=int, help="indicates unknown clients", required=True)
parser.add_argument("--help", action="help", default=argparse.SUPPRESS, help=argparse._("show this help message and exit"))
args = parser.parse_args()
# Global data structures
clientsList = []
spawnedClientThreads = []
pendingMsgsForUnregisteredClients = {} # {clientName1 : {senderName1 : [msgs1]}}
# Lock
clientsListLock = threading.Lock()
pendingMsgsDictLock = threading.Lock()
# Global output file
outputFile = open(args.logfile, 'w')

# On exit, log to file
@atexit.register
def exitCleanUp():
    # print("[DEBUG] server called exit clean up")
    # print("[DEBUG] removing spawned clients:", spawnedClientThreads)
    for spawnedClient in spawnedClientThreads:
        # print("[DEBUG] removing client:", spawnedClient)
        spawnedClient.exit()
    logToFile("terminating server...")

# Logging method
def logToFile(msg):
    #LOCK?
    outputFile.write(msg)
    outputFile.write("\n")
    outputFile.flush()

def handelNewConnection(clientName, clientAddress, sock):
    # log
    logToFile("client connection from host " + clientAddress[0] + " port " + str(clientAddress[1]))
    # Add new client to clientsList
    clientsList.append((clientName, clientAddress))
    # print("[DEBUG] clientsList : ", clientsList)
    # terminal output
    print(clientName, "registered from host", clientAddress[0], "port", str(clientAddress[1]))
    # log
    logToFile("received register " + clientName + " from host " + clientAddress[0] + " port " + str(clientAddress[1]))
    if (clientName):
        # Message Type: welcome <client1>
        welcomeMsg = "welcome " + clientName
        sock.sendto(welcomeMsg, clientAddress)

    # If there is pending Msg for new client
    if args.handler == 1 and clientName in pendingMsgsForUnregisteredClients:
        sendPendingMsgs(clientName, clientAddress, sock)

def sendPendingMsgs(receiverName, receiverAddress, sock):
    for senderName in pendingMsgsForUnregisteredClients[receiverName]:
        for rawMsg in pendingMsgsForUnregisteredClients[receiverName][senderName]:
            msg = getMsgFromRawMsg(rawMsg)
            senderMsg = "recvfrom " + senderName + " " + msg
            sock.sendto(senderMsg, receiverAddress)
            # print("[DEBUG] send pending msgs to", receiverName, "from", senderName, msg)
            # Log recvfrom
            logRecvfrom(senderName, receiverName, rawMsg)
    with pendingMsgsDictLock:
        del pendingMsgsForUnregisteredClients[receiverName]

def getNameFromAddress(address):
    for client in clientsList:
        if client[1] == address:
            return client[0]
    return None

def getAddressFromName(clientName):
    for client in clientsList:
        if client[0] == clientName:
            return client[1]
    return None

def handleClientToClientMsg(senderAddress, senderMsgData, sock):
    senderMsgDataList = senderMsgData.split()
    receiverName = senderMsgDataList[1]
    senderName = getNameFromAddress(senderAddress)
    if senderName is None:
        print("[ERROR] sender with address", senderAddress, "does not exist")
            
    # Log sendto
    logSendto(senderName, receiverName, senderMsgData)

    if isClientExist(receiverName):
        receiverAddress = getAddressFromName(receiverName)
        if receiverAddress is None:
            print("[ERROR] receiver with name", receiverName, "does not exist")
        senderMsgDataList[0] = "recvfrom"
        senderMsgDataList[1] = senderName
        senderMsg = " ".join(senderMsgDataList)
        sock.sendto(senderMsg, receiverAddress)
        # Log recvfrom
        logRecvfrom(senderName, receiverName, senderMsgData)
    elif args.handler == 0:
        logToFile(receiverName + " not registered with server")
    elif args.handler == 1:
        logToFile(receiverName + " not registered with server, spawning " + receiverName)
        addPendingMsgs(senderName, receiverName, senderMsgData)
        # spwan client
        # TODO make ip variable
        serverIp = socket.gethostbyname('localhost')
        newSpawnedClient = SpawnedClient.SpawnedClient(serverIp, args.port, "spawned_" + receiverName + ".txt", receiverName)
        spawnedClientThreads.append(newSpawnedClient)
        # print("[DEBUG] adding spawned client:", newSpawnedClient)
        newSpawnedClientThread = threading.Thread(target=newSpawnedClient.spawnedClient())
        newSpawnedClientThread.setDaemon(True)
        newSpawnedClientThread.start()

def addPendingMsgs(senderName, receiverName, senderMsgData):
    with pendingMsgsDictLock:
        if receiverName in pendingMsgsForUnregisteredClients:
            if senderName in pendingMsgsForUnregisteredClients[receiverName]:
                pendingMsgsForUnregisteredClients[receiverName][senderName].append(senderMsgData)
            else:
                pendingMsgsForUnregisteredClients[receiverName][senderName] = [senderMsgData]
        else:
            pendingMsgsForUnregisteredClients[receiverName] = {senderName : [senderMsgData]}
    # print("DEBUG] updated pendingMsg dictionary:", pendingMsgsForUnregisteredClients)

# extract msg from sender's sento raw message
def getMsgFromRawMsg(rawMsg):
    rawMsgList = rawMsg.split()
    del rawMsgList[0]
    del rawMsgList[0]
    senderMsg = " ".join(rawMsgList)
    # <message string>
    return senderMsg

# write sendto log to server.txt
def logSendto(senderName, receiverName, senderMsgRaw):
    senderMsg = getMsgFromRawMsg(senderMsgRaw)
    sendtoLog = "sendto " + receiverName + " from " + senderName + " " + senderMsg
    logToFile(sendtoLog)

# write recvfrom log to server .txt
def logRecvfrom(senderName, receiverName, senderMsgRaw):
    senderMsg = getMsgFromRawMsg(senderMsgRaw)
    recvfromLog = "recvfrom " + senderName + " to " + receiverName + " " + senderMsg
    logToFile(recvfromLog)

def isClientExist(clientName):
    for client in clientsList:
        if client[0] == clientName:
            return True
    return False

def msgHandler(sock):
    while True:
        clientMsgData, clientAddress = sock.recvfrom(1024)
        clientMsgDataList = clientMsgData.split()
        # new client connection
        if len(clientMsgDataList) == 2 and clientMsgDataList[0].lower() == "register":
            # Initiate thread to send client welcome messages
            clientName = clientMsgDataList[1]
            handelNewConnectionThread = threading.Thread(target=handelNewConnection, args=(clientName, clientAddress, sock,))
            handelNewConnectionThread.setDaemon(True)
            handelNewConnectionThread.start()
        # Some client send msg
        elif len(clientMsgDataList) > 2 and clientMsgDataList[0] == "sendto":
            # Initiate thread to handle client to client msg
            handleClientToClientMsgThread = threading.Thread(target=handleClientToClientMsg, args=(clientAddress, clientMsgData, sock,))
            handleClientToClientMsgThread.setDaemon(True)
            handleClientToClientMsgThread.start()
        elif len(clientMsgDataList) == 2 and clientMsgDataList[0].lower() == "exit":
            clientName = clientMsgDataList[1]
            removeClientThread = threading.Thread(target=removeClient, args=(clientName,))
            removeClientThread.setDaemon(True)
            removeClientThread.start()
        else:
            print("[ERROR] Recieved unsupported message")

# Remove client in thread
def removeClient(clientName):
    # Acquire lock when entering this block, release lock after exit the block
    with clientsListLock:
        for client in clientsList:
            if client[0] == clientName:
                clientsList.remove(client)
                # print("[DEBUG] removed from client list:", clientName)


def main():
    # Socket initialization
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    port = args.port
    sock.bind(('localhost', port))
    # print("[DEBUG] Binding completed  ! !")
    # log
    logToFile("server started on "+ socket.gethostbyname('localhost') + " at port " + str(port) + "...")
    # handle msgs in thread
    msgHandlerThread = threading.Thread(target=msgHandler, args=(sock,))
    msgHandlerThread.setDaemon(True)
    msgHandlerThread.start()
    # handle command line input
    while True:
        cmd = raw_input("> ")
        # print("[DEBUG] Input command :", cmd)
        if str(cmd) == "exit":
            break
        else:
            print("[ERROR] Unsupported command")


main()




