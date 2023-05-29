#Authors Aaron Luchan and Masanbat Mulo
import socket
import sys
import os

def watchdog(destination_ip):
    WATCHDOG_PORT = 3000
    WATCHDOG_TIMEOUT = 10  # 10 seconds

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(WATCHDOG_TIMEOUT)
        sock.connect((destination_ip, WATCHDOG_PORT))
        sock.recv(1024)  # Wait for response
    except socket.timeout:
        print(f"Server {destination_ip} cannot be reached.")
        os._exit(1)
    sock.close()

def main():
    if len(sys.argv) < 2:
        print("The right command: python watchdog.py <IP address>")
        return

    destination_ip = sys.argv[1]

    watchdog(destination_ip)

if __name__ == "__main__":
    main()
