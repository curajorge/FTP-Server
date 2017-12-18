from socket import *
import threading
import sys 
import traceback
import errno
import mmap
import os
import subprocess
from configparser import ConfigParser

parser = ConfigParser()
parser.read('ftpserver/conf/fsys.cfg')

#global variables
THREADLIST = []
RECV_BUFFER = 1024
FTP_PORT = int(parser.get("DEFAULT", "DATA_PORT_FTP_SERVER"))
FTP_ROOT = parser.get("DEFAULT","ftp_root")
CMD_QUIT = "QUIT"
CMD_HELP = "HELP"
CMD_LOGIN = "LOGIN"
CMD_LOGOUT = "LOGOUT"
CMD_LS = "LS"
CMD_PWD = "PWD"
CMD_PORT = "PORT"
CMD_DELETE = "DELETE"
CMD_PUT = "STOR"
CMD_GET = "GET"

#Files
DATAFILE = parser.get("DEFAULT","user_data_file")
USERTOKEN = 0
PASSWORDTOKEN = 1
USERTYPETOKEN = 2



#FTP CODES
CODE150 = "150 : File status okay; about to open data connection."
CODE220 = "220 : Service ready for new user. " 
CODE226 = "226 : Transfer complete."
CODE331 = "331 : User name okay, need password. "
CODE430 = "430 : Invalid username or password. "
CODE230 = "230 : User logged in, proceed. Logged out if appropriate."
CODE200 = "200 : The requested action has been successfully completed."
CODE530 = "530 : Not logged in."
CODE221 = "221 : Goodbye."
CODE451 = "451 : Requested action aborted: local error in processing."

#FTP COMMANDS
CMD_QUIT = "QUIT"
CMD_USER = "USER"
CMD_PASS = "PASS"
CMD_LOGOUT = "LOGOUT"
CMD_LIST = "LIST"
CMD_PORT = "PORT"
CMD_DELETE = "DELE"
CMD_PUT = "STOR"
CMD_GET = "RETR"

#USER TYPES
ADMIN = "admin"
USER = "user"
WORKINGDIR = "first"



def clientThread(clientSocket, addr):
        
    root = FTP_ROOT
    userFlag = False
    userType = ""
    connected = False     
    dataPort = socket(AF_INET, SOCK_STREAM)
    clientHost = ""
    clientPort = 0
    
      
    
    clientSocket.send(CODE220.encode())
    while True:        
       ftp_recv = clientSocket.recv(RECV_BUFFER).decode()
       tokens = ftp_recv.split()
       root ,userFlag, userType, connected, dataPort, clientHost, clientPort = ftpCmd(root, tokens, clientSocket, dataPort, userFlag, userType, connected, clientHost, clientPort)
#       print(userType)

#working on USER
def ftpCmd(root, tokens, clientSocket, dataPort , userFlag, userType, connected, clientHost, clientPort):
    
    cmd = tokens[0].upper()    
 #   print(tokens)
 #   print(root)
    #USER
    if (cmd == CMD_USER):
       userFound, userType = findUserOrPass(tokens[1], USERTOKEN, userType)       
       if userFound:           
           userFlag = True 
           if(userType == USER):
               root = root + tokens[1]         
           send(CODE331 , clientSocket)           
       else: send(CODE430, clientSocket)
    #PASS
    if (cmd == CMD_PASS):
      if(userFlag == True):
        passFound, userType = findUserOrPass(tokens[1], PASSWORDTOKEN, userType)
        if (passFound==True):            
            connected = True                           
            send(CODE230, clientSocket)
        else: send(CODE430 , clientSocket)
      else: send(CODE430, clientSocket)
    
    #QUIT
    if(cmd == CMD_QUIT):
        send(CODE221, clientSocket)
        clientSocket.close()
        
    
    #PORT
    if (cmd == CMD_PORT):        
        clientHost, clientPort = ftp_dataPort(tokens)
        send(CODE200, clientSocket)  
    
    #LIST
    if ((cmd == CMD_LIST)):
        #change the NOT - REMOVE
        if  connected:           
            send(CODE150, clientSocket)
            cmd_list(root,clientHost, clientPort)
            send(CODE226, clientSocket)

            #revisite this- if not connected   
        else: send(CODE530 ,clientSocket) 
    #GET
    if(cmd == CMD_GET):
        if connected:
            cmd_get(root, tokens, clientSocket, clientHost, clientPort)

    #put
    if(cmd ==  CMD_PUT):
        if connected:
            cmd_put(root, tokens, clientSocket, clientHost, clientPort)
    #DELETE
    if(cmd == CMD_DELETE):
        if connected:
            cmd_delete(root, tokens, clientSocket)

    return root, userFlag , userType, connected, dataPort , clientHost, clientPort
        
def cmd_delete(root, tokens, clientSocket):
    filepath = root+"/"+tokens[1]

    try:
        os.remove(filepath)
    except OSError as e:
        print("Error: " + e)
        return send(code451)
    send(CODE200,clientSocket)

def cmd_put(root, tokens, clientSocket, host, port):
    dataPort = createDataPort()
    dataPort.connect((host,port))
    send(CODE150, clientSocket)

    remote_filename = tokens[1]
    if (len(tokens) == 3):
        filename = tokens[2]
    else:
        filename = remote_filename
    filename = root+"/"+filename;
    
   
    try:
        file = open(filename, "wb")
    
        size_recv = 0
        sys.stdout.write("|")
        while True:
                sys.stdout.write("*")
                data = dataPort.recv(RECV_BUFFER)

                if (not data or data == '' or len(data) <= 0):
                  file.close()
                  break
                else:
                    file.write(data)
                    size_recv += len(data)

        sys.stdout.write("|")
        sys.stdout.write("\n")
    except (OSError,IOError) as e:
        print("error opening file: " ,e)
        send(CODE451, clientSocket)
    dataPort.close()
    
    send(CODE226, clientSocket)
        




def cmd_get(root,tokens, clientSocket, host, port):
    dataPort = createDataPort()
    dataPort.connect((host,port))

    #print("this is a test and it works ")
    
    
    try:
        #print(tokens[1])
        fileRoot = root+"/"+tokens[1] 
        #print(fileRoot)
        file = open( root+"/"+tokens[1], 'rb')
        dataFile = file.read()
        
        send(CODE150, clientSocket)
        dataPort.send(dataFile)
        
    except (OSError,IOError) as e:
        print("error opening file: " ,e)
        send(CODE451, clientSocket)

    send(CODE226, clientSocket)




def cmd_list(root, host, port):
    
   
    dataPort = createDataPort()
    dataPort.connect((host,port))
    command = "dir "+root 
    result = subprocess.check_output(command,shell=True).decode()

    
    send(result, dataPort)
    dataPort.close()

def createDataPort():
    dataPort = socket(AF_INET, SOCK_STREAM)
    dataPort.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    return dataPort




def ftp_dataPort(tokens):
    
    port_arguments = tokens[1].split(',')
    port = (int(port_arguments[4])*256) + int(port_arguments[5])
    host = port_arguments[0]+"."+port_arguments[1]+"."+port_arguments[2]+"."+port_arguments[3]
    print(host , " " , port)
        
   
    
    
    return  host , port

def findUserOrPass(userOrPass, USERORPASSTOKEN, userType):
    valid, userType = findInFile(userOrPass, DATAFILE, USERORPASSTOKEN, userType)
    if valid:
        return True , userType
    else: 
        return False, userType

#send DATA to a client (use for return codes)
def send(data, clientSocket):
    clientSocket.send(data.encode())
    
#finds Value:String in file:String within a TOKENVALUE:int
#reads '#' as comments, Skips entire line if comment found  
def findInFile(value, file, TOKENVALUE, userType):
    
    try:
        File = open(file, 'r')
        dataFile = File.read().split('\n')       
        
        for line in dataFile:
        
            if line:
                
               tokens = line.split()
               if ('#' not in line) & (len(tokens) > TOKENVALUE):    
                   #print(tokens[TOKENVALUE])               
                   if tokens[TOKENVALUE] == value:                       
                       return True, tokens[2]       

    except (OSError,IOError) as e:
        print("File retrieval error:", e)
    return False, ""



def main(): 
    
    
      
    global THREADLIST
    serverSocket = connectServer()
    while True:
        connectionSocket, addr = serverSocket.accept()
        thread = threading.Thread(target=clientThread, args=(connectionSocket,addr))
        thread.start()
        THREADLIST.append(thread)
   


def connectServer():
    try:
        serverSocket = socket(AF_INET,SOCK_STREAM)
        serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        serverSocket.bind(("",FTP_PORT))
        serverSocket.listen(15)
        print ("Ready to receive!")
    except OSError as e:
        print("Server error:" ,e)
    return (serverSocket)


#not working
def findInFile2(value, file): 
    found = False 
    
    try:
 
        #alleviate possible memory problems  
        dataFile = mmap.mmap(open(file).fileno(), 0, access=mmap.ACCESS_READ)
        dataFile.split('\n')
       
        #testing dataFile.plit(by line)
        for line in dataFile:
              print (dataFile[line])

        if (dataFile.find(str.encode(value)) == True ):
            return True
        else: return False 
    except (OSError,IOError) as e:
         print("File retrieval error:", e)

main()