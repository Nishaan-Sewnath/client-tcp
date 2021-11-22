import socket
import sys
import time
from datetime import datetime
import threading
import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

S_IP =  '192.168.43.59' #input server IP
S_PORT = 1078 #input same port as the server
BUFFER = 1024 

circuitstat = True
lastsample = None
chan_temp = None
chan_LDR = None
s = None
s_conn = False

def CreateMessage(header, message):
    return (header + "{:<5}".format(len(message)) + message)

def readMessage(message):
    try:
        if (int(message[1:6]) == len(message[6:])):
            return [message[0],message[1:6],message[6:]]
        else:
            return False
    except:
        return False

def threads():
    global chan_temp, chan_LDR, circuitstat
    #sends data through tcp constantly
    while(True):
        lightval = chan_LDR.value/100
        tempval = round(chan_temp.voltage*25)
        #sensor 'ON'
        if(circuitstat):
            sendTo(tempval, lightval)
        #Wait for 10s     
        time.sleep(10)

def sendTo(temp, light):
    global lastsample, s
    #putting message into a specific format
    message = str(light) + "#" + str(temp)
    #creates a message with the appripriate command
    message = CreateMessage("S",message)
    #Message format: <cmd> <length> <light>#<temp>
    s.send(message.encode())
    #Note time as the new latest sample   
    lastsample = str(datetime.now().time())[0:8]

def main():
    #notification that the main method is working
    global s, circuitstat, chan_LDR, chan_temp, lastsample

    #gets server info and connects to the appropriate socket
    for res in socket.getaddrinfo(S_IP, S_PORT, socket.AF_UNSPEC, socket.SOCK_STREAM, 0, socket.AI_PASSIVE):
        af, socktype, proto, canonname, sa = res
        try:

            s = socket.socket(af, socktype, proto)
            print('Sockets working!') 
            s.connect((sa))
            print('Connected')  

        except OSError as msg:
            print('Connection failed!')
            s.close() 
            s = None
            continue  
        break

    #sets up the ldr and temperature sensors
    spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
    cs = digitalio.DigitalInOut(board.D5)
    mcp = MCP.MCP3008(spi, cs)
    chan_temp = AnalogIn(mcp, MCP.P1)
    chan_LDR = AnalogIn(mcp, MCP.P2)

    #creates and starts the threads
    td  = threading.Thread(target = threads)
    td.daemon = True
    td.start()
    with s:
        #infinite loop until serverIn = 'Exit'
        while (True):

            #recevies and decodes the message sent by the server to the client
            serverIn = s.recv(BUFFER)
            serverIn = readMessage(serverIn.decode())
            
            if (serverIn == False):
                print("Error, incorrect sent message")
                continue
            if (serverIn[0] == 'M'):
                print(serverIn[2])

            if(serverIn[2] == 'Exit'): #Receive's Exit when the client has terminated the session
	            print('Server has Terminated the session')
	            break

            elif(serverIn[2] == 'Turn ON'): #turns on the sensors for server
                message = CreateMessage("M","Sensors On")
                s.send(message.encode())
                circuitstat = True

            elif(serverIn[2] == 'Turn OFF'): #turns off sensors for server
                message = CreateMessage("M","Sensors Off")
                s.send(message.encode())
                circuitstat = False

            elif(serverIn[2] == 'Status'): #checks if sensors are on or off
                if(circuitstat == True):
                    message = CreateMessage("M","Status: On |Last sample at "+lastsample)
                    s.send(message.encode())
                else:
                    message = CreateMessage("M","Status: Off |Last sample at "+lastsample)
                    s.send(message.encode())

            time.sleep(1)
            
            
    s.close()
    s = None    
    quit()

if __name__ == '__main__':
    main()
