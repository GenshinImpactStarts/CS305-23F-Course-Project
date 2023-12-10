from threading import Thread, Condition
from time import sleep
import socket

socks = [None] * 100
for i in range(100):
    socks[i] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socks[i].connect(('127.0.0.1', 65432))
sleep(1)
for i in range(100):
    socks[i].close()
print(1)
