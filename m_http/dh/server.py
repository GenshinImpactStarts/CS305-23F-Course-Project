import socket
from ..threading_tcp import ThreadingTCP

__all__ = 'Server',


class Server(ThreadingTCP):
    def handle(self, conn: socket.socket, addr: tuple):
        pass
