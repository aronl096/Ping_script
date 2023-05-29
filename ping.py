# Author : Aaron Luchan

import os
import socket
import struct
import sys
import time
import select
ICMP_ECHO_REQUEST = 8  # ICMP echo request type
# Function that make a checksum algorithm process
def checksum(packet):
    # Calculate the checksum for the ICMP packet.
    packet = bytearray(packet)
    chksum = 0
    countTo = (len(packet) // 2) * 2

    for count in range(0 ,countTo ,2):
        thisVal = packet[count + 1] * 256 + packet[count]
        chksum = chksum + thisVal
        chksum = chksum & 0xffffffff
    if countTo < len(packet):
        chksum = chksum + packet[-1]
        chksum = chksum & 0xffffffff

    chksum = (chksum >> 16) + (chksum & 0xffff)
    chksum = chksum + (chksum >> 16)
    result = ~chksum
    result = result & 0xffff
    result = result >> 8 | (result << 8 & 0xff00)
    return result

# Function to receive the ICMP echo reply
def receive_ping(sock ,pid ,timeout):
    #Receive and process the ICMP echo reply
    timeLeft = timeout

    while True:
        startedSelect = time.time()
        ready = select.select([sock] ,[] ,[] ,timeLeft)
        howLongInSelect = (time.time() - startedSelect)
        if ready[0] == []:  # Timeout
            return None ,None

        timeReceived = time.time()
        recPacket ,addr = sock.recvfrom(1024)

        # Extract the ICMP header from the IP packet
        icmpHeader = recPacket[20:28]
        type ,code ,checksum ,packetID ,sequence = struct.unpack("bbHHh" ,icmpHeader)

        if type == 0 and packetID == pid:
            return recPacket ,addr

        timeLeft = timeLeft - howLongInSelect
        if timeLeft <= 0:
            return None ,None

# Function to send the ICMP echo request
def send_ping(sock ,destAddr ,pid ,sequence):
    # Create ICMP packet
    chksum = 0
    header = struct.pack("bbHHh" ,ICMP_ECHO_REQUEST ,0 ,chksum ,pid ,sequence)
    data = struct.pack("56s" ,b" " * 56)  # Packet size changed to 64 bytes

    # Calculate checksum
    chksum = checksum(header + data)
    header = struct.pack("bbHHh" ,ICMP_ECHO_REQUEST ,0 ,socket.htons(chksum) ,pid ,sequence)

    packet = header + data

    # Send packet
    sock.sendto(packet ,(destAddr ,1))

# Function that open a Raw socket to make a ping connection
def ping(destAddr ,timeout=2 ,count=None):
    try:
        mySocket = socket.socket(socket.AF_INET ,socket.SOCK_RAW ,socket.getprotobyname("icmp"))
    except socket.error as e:
        print("Socket error: %s" % e)
        sys.exit()
    myID = os.getpid() & 0xFFFF  # Use the current process ID as the ICMP ID
    print(f"Ping {destAddr} ({destAddr}): 56 data bytes")
    sequence = 0
    while True:
        send_ping(mySocket ,destAddr ,myID ,sequence)
        timeSent = time.time()
        recPacket , addr = receive_ping(mySocket ,myID ,timeout)
        if recPacket and addr:
            timeReceived = time.time()
            timeElapsed = (timeReceived - timeSent) * 1000
            icmpHeader = struct.pack("bbHHh" ,ICMP_ECHO_REQUEST ,0 ,0 ,myID ,sequence)
            print(f"64 bytes from {destAddr}: icmp_seq={sequence} ttl=115 time={timeElapsed:.0f} ms")
        else:
            print("Request timed out")
        if count is not None:
            count -= 1
            if count == 0:
                break
        sequence += 1
        time.sleep(1)  # Add a 1-second delay
    mySocket.close()


if __name__ == "__main__":
    # If we dont put any IP adrres . ( because the first argument is 'ping.py'
    if len(sys.argv) < 2:
        print("Please write the command in this form : python3 ping.py <hostname> [count]")
        sys.exit()

    hostname = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) >= 3 else None
    ping(hostname ,count=count)
