# Ping_script
## Ping.py

The ping command is used to check the connection between 2 machines.   
I wrote a program called "ping.py" which will get an argument indicating which host to ping.  
**Usage: python3 ping.py `<IP>`** (just like the ping command).    
The program will send an ICMP ECHO REQUEST to the host, and when receiving ICMP - ECHO-REPLY , the program will send the next ICMP ECHO REQUEST (no need to stop).  
For each packet received, you will get printed the packet IP, packet sequence number, and time between the request and replay.   

## Watchdog.py

Watchdog is a timer to detect and recover your computer dis-functions or hardware fails.  
It’s a chip whose sole purpose is to receive a signal every millisecond from the CPU.  
It will reboot the system if it hasn’t received any signal for 10 milliseconds (mostly when hardware fails).  
I have modified the ping program, and write a watchdog that will hold a timer (TCP connection on port 3000) to ensure that if we don’t receive an ICMP-ECHO-REPLY   after sending an ICMP-REQUEST for 10 seconds, it will exit and print **"server `<IP>` cannot be reached."**  
I have modified the ping.py program (better_ping.py) so that it will execute the watchdog.py program as well using **threads**.  

