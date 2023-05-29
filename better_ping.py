#Authors Aaron Luchan and Masanbat Mulo
import socket
import struct
import sys
import time
import threading
import os
import select


ICMP_ECHO_REQUEST = 8  # ICMP echo request type
WATCHDOG_TIMEOUT = 10  # 10 seconds


def calculate_checksum(packet):
    packet_length = len(packet)
    if packet_length % 2 != 0:
        packet += b"\x00"  # Pad odd-length packet with zero

    checksum = 0
    for i in range(0, packet_length, 2):
        checksum += (packet[i] << 8) + packet[i+1]

    checksum = (checksum >> 16) + (checksum & 0xffff)
    checksum = (~checksum) & 0xffff
    return checksum


def create_icmp_header():
        # Create the ICMP header for the ICMP echo request packet
    icmp_type = ICMP_ECHO_REQUEST
    icmp_code = 0
    icmp_checksum = 0
    icmp_identifier = os.getpid() & 0xFFFF
    icmp_sequence = 1

    icmp_header = struct.pack("bbHHh", icmp_type, icmp_code, icmp_checksum, icmp_identifier, icmp_sequence)
    checksum = calculate_checksum(icmp_header)
    icmp_header = struct.pack("bbHHh", icmp_type, icmp_code, socket.htons(checksum), icmp_identifier, icmp_sequence)

    return icmp_header


def receive_ping(sock, pid, timeout):
#Receive and process the ICMP echo reply."""
    timeLeft = timeout

    while True:
        startedSelect = time.time()
        ready = select.select([sock], [], [], timeLeft)
        howLongInSelect = time.time() - startedSelect
        if ready[0] == []:  # Timeout
            return None, None

        timeReceived = time.time()
        recPacket, addr = sock.recvfrom(1024)

        # Extract the ICMP header from the IP packet
        # The slice [20:28] indicates that we want to extract elements starting
        # from index 20 up to, but not including, index 28.
        icmpHeader = recPacket[20:28]
        icmp_type, code, checksum, packetID, sequence = struct.unpack("bbHHh", icmpHeader)

        if icmp_type == 0 and packetID == pid:
            return recPacket, addr

        timeLeft -= howLongInSelect
        if timeLeft <= 0:
            return None, None


def send_ping(sock, destAddr, pid, sequence):
# Send an ICMP echo request.
    # Create ICMP packet
    chksum = 0
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, chksum, pid, sequence)
    data = struct.pack("56s", b" " * 56)  # Packet size changed to 64 bytes

    # Calculate checksum
    chksum = calculate_checksum(header + data)
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, socket.htons(chksum), pid, sequence)

    packet = header + data

    # Send packet
    sock.sendto(packet, (destAddr, 1))


def better_ping(destAddr, timeout=2, count=None):
    try:
        mySocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname("icmp"))
    except socket.error as e:
        print("Socket error:", e)
        sys.exit()
    myID = os.getpid() & 0xFFFF  # Use the current process ID as the ICMP ID
    print(f"b_Ping {destAddr} ({destAddr}): 56 data bytes")
    sequence = 0
    # The PING_COMPLETED global variable is declared to
    # keep track of whether the pinging process is completed or not.
    global PING_COMPLETED
    while True:
        send_ping(mySocket, destAddr, myID, sequence)
        timeSent = time.time()
        recPacket, addr = receive_ping(mySocket, myID, timeout)
        if recPacket and addr:
            timeReceived = time.time()
            timeElapsed = (timeReceived - timeSent) * 1000
            icmpHeader = struct.pack("BBHHh", ICMP_ECHO_REQUEST, 0, 0, myID, sequence)
            print(f"64 bytes from {destAddr}: icmp_seq={sequence} ttl=115 time={timeElapsed:.0f} ms")
            time.sleep(1)
        else:
            print("Request timed out")
        if count is not None:
            count -= 1
            if count == 0:
                break
        sequence += 1
    PING_COMPLETED = True
    mySocket.close()


def watchdog(destination_ip):
    WATCHDOG_PORT = 3000
    WATCHDOG_TIMEOUT = 10  # 10 seconds

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(WATCHDOG_TIMEOUT)
        sock.connect((destination_ip, WATCHDOG_PORT))
        sock.recv(1024)  # Wait for response
    except socket.timeout:
        if not PING_COMPLETED:
            print(f"Server {destination_ip} cannot be reached.")
            os._exit(1)
    sock.close()


def main():
    if len(sys.argv) < 2:
        print("Usage: python better_ping.py <ip>")
        sys.exit()

    destination_ip = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) >= 3 else None

    global PING_COMPLETED
    PING_COMPLETED = False

    # Create threads for ping and watchdog
    ping_thread = threading.Thread(target=better_ping, args=(destination_ip, count))
    watchdog_thread = threading.Thread(target=watchdog, args=(destination_ip,))

    # Start the threads
    ping_thread.start()
    watchdog_thread.start()

    # Wait for the threads to finish
    ping_thread.join()
    watchdog_thread.join()


if __name__ == "__main__":
    main()
