import socket
from ..http_content.header import Header
from math import log10
from .message import RequestType, RespondType
from ..server import Server as HTTPServer
from .symm import Symm

__all__ = 'Server',


class Server(HTTPServer):
    def __init__(self, addr: tuple, private_key: int, p=4179340454199820289, g=3):
        super().__init__(addr)
        self.private_key = private_key
        self.p = p
        self.g = g
        self.public_key = g**private_key % p
        self.public_key_bytes = str(self.public_key).encode()
        self.ask_respond = b'\r\n'.join([
            RespondType.ok, self.public_key_bytes, str(p).encode(), str(g).encode()])
        self.ok_respond = RespondType.ok + b'\r\n'
        self.reject_respond = RespondType.err + b'\r\n'
        self.p_len = int(log10(p))+1
        self.print(f'public key (A, g, p): {self.public_key}, {self.g}, {self.p}')
        self.print(f'private key (a): {self.private_key}')

    def handle(self, conn: socket.socket, addr: tuple):
        while True:
            try:
                conn.settimeout(5)
                try:
                    request = conn.recv(512)
                except socket.timeout:
                    return
                request_type_end = request.find(b'\r\n')
                # unrecognized request
                if request_type_end == -1:
                    raise Exception()
                request_type = request[:request_type_end]
                # ask request
                if request_type == RequestType.ask_request and request_type_end == len(request) - 2:
                    conn.sendall(self.ask_respond)
                # connect request
                elif request_type == RequestType.connect_request:
                    request_type, public_key, response_key, other = request.split(
                        b'\r\n', 3)
                    if public_key != self.public_key_bytes or other != b'' or len(response_key) > self.p_len:
                        raise Exception()
                    session_key = int(
                        response_key) ** self.private_key % self.p
                    self.print(f'server session key (K): {session_key}')
                    coder = Symm(session_key)
                    conn.sendall(self.ok_respond)
                    conn.settimeout(None)
                    temp = []
                    testComplete = 0
                    body_length = 0
                    header_class = Header()
                    header_pram_temp_in_handle=None
                    while True:
                        receive = conn.recv(2048)
                        receive = coder.decode(receive)
                        if receive == b'':
                            break
                        temp.append(receive)
                        testComplete, body_length, response,header_pram_temp_in_handle = self.handle_request(
                            temp, header_class, testComplete, body_length,header_pram_temp_in_handle)

                        if (testComplete == 2 or testComplete == 3):
                            temp = []
                            testComplete = 0
                            body_length = 0
                            header_pram_temp_in_handle =None
                            for i in response:
                                i = coder.encode(i)
                                conn.sendall(bytes(i))
                        if testComplete == 3:
                            break
                # unmatched request
                else:
                    raise Exception()

            except Exception as e:
                conn.sendall(self.reject_respond)
