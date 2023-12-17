import socket
from ..server import Server as HTTPServer

__all__ = 'Server',


class Server(HTTPServer):
    def handle(self, conn: socket.socket, addr: tuple):
        pass
