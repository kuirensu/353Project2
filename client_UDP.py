from __future__ import print_function
import socket               # Import socket module
import argparse             # Import argparse module
import atexit
import thread
import threading
# Part 1,2,3 Done

# Required arguments specification
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("-s", "--serverIP", help="indicate the server IP address", required=True)
parser.add_argument("-p", "--port", type=int, help="port number for client to connect to server", required=True)
parser.add_argument("-l", "--logfile", help="name of logfile", required=True)
parser.add_argument("-n", "--name", help="indicates client name", required=True)
parser.add_argument("--help", action="help", default=argparse.SUPPRESS, help=argparse._("show this help message and exit"))
args = parser.parse_args()
# Global variables
CLIENT_NAME = args.name
# Global output file
outputFile = open(args.logfile, 'w')

# On exit, log to file
@atexit.register
def exitCleanUp():
    logToFile("terminating client...")

# Logging method
def logToFile(msg):
    outputFile.write(msg)
    outputFile.write("\n")
    outputFile.flush()

# Listener thread log messages recieved from server
def msgListener(sock):
    while True:
        serverMsgData = sock.recv(1024)
        print("[DEBUG] Received message from server :", serverMsgData)
        serverMsgDataList = serverMsgData.split()
        
        if len(serverMsgDataList) == 2 and serverMsgDataList[0] == "welcome" and serverMsgDataList[1].lower() == CLIENT_NAME.lower():
            serverWelcomeMsg = serverMsgDataList[0]
            #log print
            logToFile("received " + serverWelcomeMsg)
        elif len(serverMsgDataList) > 2 and serverMsgDataList[0] == "recvfrom":
            print(serverMsgData)
            logToFile(serverMsgData)
        else:
            print("[ERROR] incorrect server msg format")

def main():
    # Socket initialization
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    serverAddress = (args.serverIP, args.port)
    print ("[DEBUG] server_address is ", serverAddress)
    
    # Message Type: register <client1>
    clientRegisterMsg = "register " + CLIENT_NAME
    sock.sendto(clientRegisterMsg, serverAddress)
    # log
    logToFile("connecting to the server " + serverAddress[0] + " at port " + str(serverAddress[1]))
    logToFile("sending register message " + CLIENT_NAME)
    print("connected to server and registered\nwaiting for messages...")
    # Initialize listener thread
    msgListenerThread = threading.Thread(target=msgListener, args=(sock,))
    msgListenerThread.setDaemon(True)
    msgListenerThread.start()
    # handle command line input
    while True:
        cmd = raw_input("> ")
        print("[DEBUG] Input command :", cmd)
        if cmd == "exit":
            exitMsg = "exit " + CLIENT_NAME
            sock.sendto(exitMsg, serverAddress)
            break
        elif cmd.startswith("sendto "):
            cmdList = cmd.split()
            if len(cmdList) > 2:
                sock.sendto(cmd, serverAddress)
                print(cmd)
                logToFile(cmd)
        else:
            print("[DEBUG] Unsupported command")

main()



