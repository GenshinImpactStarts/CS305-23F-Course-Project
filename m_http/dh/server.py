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

    def handle(self, conn: socket.socket, addr: tuple):
        try:
            request = conn.recv(512)
            request_type_end = request.find(b'\r\n')
            # unrecognized request
            if request_type_end == -1:
                raise Exception()
            request_type = request[:request_type_end]
            # ask request
            if request_type == RequestType.ask_request and request_type_end == len(request) - 2:
                conn.send(self.ask_respond)
            # connect request
            elif request_type == RequestType.connect_request:
                request_type, public_key, session_key, other = request.split(
                    b'\r\n', 3)
                if public_key != self.public_key_bytes or other != '' or len(session_key) > self.p_len:
                    raise Exception()
                session_key = int(session_key).to_bytes(Symm.KEY_LEN, 'big')
                conn.send(self.ok_respond)
                temp = b''
                header_class = Header()
                while True:
                    receive = conn.recv(2048)
                    receive = Symm.decode(receive, session_key)
                    if receive == b'':
                        break
                    temp += receive
                    testComplete, response = self.handle_request(
                        temp, header_class)
                    if (testComplete != 0):
                        temp = b''
                        response = Symm.encode(response)
                        conn.send(response)
                    if (testComplete == 2):
                        break
            # unmatched request
            else:
                raise Exception()

        except Exception:
            try:
                conn.send(self.reject_respond)
            except Exception:
                pass
