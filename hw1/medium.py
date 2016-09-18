import sys
import socket
import select
import time
from threading import Timer

HOST = ''
SOCKET_LIST = []
PORT = 9009 

# Settable parameters
NUM_OF_NODES = 10 # The maximum number of nodes
BANDWIDTH = 10000 # 1000 = 1KB, in turn, 10000  = 10KB (B/SEC)
MTU = 1000 # Maximum Transmit Unit for this medium (B)
RECV_BUFFER = 2*MTU # Receive buffer size
PDELAY = 0.1 # Propagation delay (s)

IDLE = 'I'
BUSY = 'B'

#Global variable
STATUS = IDLE # Status of Medium : I -> Idle, B -> Busy


def medium():

    medium_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    medium_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    medium_socket.bind((HOST, PORT))
    medium_socket.listen(NUM_OF_NODES)

    # Add medium socket object to the list of readable connections
    SOCKET_LIST.append(medium_socket)

    global STATUS # Status of Medium : I -> Idle, B -> Busy

    t=None; # Event Scheduler
    print("Medium is Activated (port:" + str(PORT) + ") ")

    while 1:
      try:
        # Get the list sockets which are ready to be read through select
        ready_to_read, ready_to_write, in_error = select.select(SOCKET_LIST, [], [], 0)

        for sock in ready_to_read:
          # A new connection request received
          if sock == medium_socket: # 0.0.0.0 : 9009 (sock)
            sockfd, addr = medium_socket.accept()
            SOCKET_LIST.append(sockfd)
            print("Node (%s, %s) connected" % addr)
          # A message from a node, not a new connection
          else: # 127.0.0.1 : 9009 (sock)
            try:
              # Receiving packet from the socket.
              packet = sock.recv(RECV_BUFFER)
              if packet:
                # Check medium here!
                if STATUS == BUSY:
                  print('Collision has happend on medium!')
                  t.cancel()
                  Timer(MTU/BANDWIDTH+PDELAY,change_status).start() # Collided packet is still in medium
                # Collision occurs!
                elif STATUS ==IDLE:
                  change_status() #Change status to busy
                  # Message packet is being propagated to nodes through medium
                  t=Timer(MTU/BANDWIDTH+PDELAY,forward_pkt, (medium_socket, sock, packet))
                  t.start()
                else:
                  print('Undefined status')
              else:
                if sock in SOCKET_LIST:
                  print("Node (%s, %s) disconnected" % sock.getpeername())
                  SOCKET_LIST.remove(sock)
                  continue

            # Exception
            except:
              if sock in SOCKET_LIST:
                print("Error! Check Node (%s, %s)" % sock.getpeername())
                SOCKET_LIST.remove(sock)
              continue
      except:
        print('\nMedium program is terminated')
        medium_socket.close()
        sys.exit()

# Forward_pkt to all connected nodes exclude itself(source node)
def forward_pkt (medium_socket, sock, message):
 
    global STATUS

    for socket in SOCKET_LIST:
        # Send the message only to peer
        if socket != medium_socket and socket != sock:
            try:
                socket.send(message)
            except:
                # Broken socket connection
                socket.close()
                # Broken socket, remove it
                if socket in SOCKET_LIST:
                    SOCKET_LIST.remove(socket)

    #Packet transmission is finished
    change_status() #Change status to idle

# Chaning medium status 
def change_status():

    global STATUS

    if STATUS == 'B':
       STATUS = 'I'
    elif STATUS == 'I':
       STATUS = 'B'

if __name__ == "__main__":
    sys.exit(medium())
