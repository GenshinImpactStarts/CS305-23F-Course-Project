import random
import socket
from ..client import Client as HTTPClient
from .message import RequestType, RespondType
from .symm import Symm
from time import sleep

__all__ = 'Client',


class Client(HTTPClient):
    def __init__(self, host, port):
        super().__init__(host, port)
        self.conn = None
        self.session_key = None

    def connect(self) -> bool:
        for _ in range(3):
            self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.conn.connect((self.host, self.port))
            self.conn.sendall(RequestType.ask_request + b'\r\n')
            response_code, public_key_raw, p, g = self.conn.recv(
                2048).split(b'\r\n')
            p = int(p)
            g = int(g)
            private_key = random.randint(1000, 9999)
            response_key = g ** private_key % p
            print(f'random key (b): {private_key}')
            print(f'B: {response_key}')
            public_key = int(public_key_raw)
            self.session_key = public_key ** private_key % p
            print(f'client session key (K): {self.session_key}')
            self.coder = Symm(self.session_key)
            self.conn.sendall(b'\r\n'.join(
                [RequestType.connect_request, public_key_raw, str(response_key).encode(), b'']))
            respond = self.conn.recv(2048)
            if respond == RespondType.ok + b'\r\n':
                return True
        return False

    def send(self, method, uri, body=None, headers=None, file_path=None, isChunk=False) -> bytearray:
        if self.conn is None:
            raise Exception()
        request = self.compile_request(
            method, uri, body, headers, file_path, isChunk)
        request = self.coder.encode(request)
        self.conn.sendall(request)
        sleep(0.1)
        response = self.coder.decode(self.conn.recv(2048))
        return response

    def disconnect(self):
        try:
            self.conn.close()
        except Exception:
            pass
        self.conn = None
        self.session_key = None
