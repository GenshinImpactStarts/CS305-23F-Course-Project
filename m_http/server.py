import socket
from .status_code import StatusCode
from .threading_tcp import ThreadingTCP

__all__ = 'Server',


class Server(ThreadingTCP):
    # return None when need to close the connection
    def hendle_http_request(self, request: str) -> str:
        return None
        lines = request.split('\n')
        request_line = lines[0].strip().split()
        method = request_line[0]
        url = request_line[1]
        http_version = request_line[2]
        messageHeader = {}
        for line in lines:
            parts = line.split(':')
            if parts.length > 2:
                messageHeader[parts[0]] = parts[1]

        authHeader = messageHeader.get('Authorization', None)  # 检查授权
        if authHeader:
            decodedAuth = authHeader.decode('utf-8')
            username = decodedAuth.split(':')[0]
            password = decodedAuth.split(':')[1]
            pass                                        # 检查用户名和密码是否匹配
        else:
            response = self.respond_header_builder(http_version, "401")
            # conn.sendall(response.encode('utf-8'))

        if method == "GET":
            filePath = url  # 还没处理呢
            try:
                with io.open(filePath, 'r', encoding='utf-8') as file:
                    data = file.read
            except FileNotFoundError:
                response = self.respond_header_builder(
                    http_version, "404")
                # conn.sendall(response.encode('utf-8'))
        elif method == "POST":
            pass
        elif method == "HEAD":
            pass
        else:
            pass

        if messageHeader['Connection'] == 'close':
            return None

    def handle(self, conn: socket.socket, addr: tuple):
        with conn:
            while self.hendle_http_request(conn.recv(1024).decode('utf-8')) is not None:
                pass
            conn.close()

    def __respond_header_builder(self, version, code) -> str:
        statusLine = f"{version} {code} {StatusCode.get_description(code)}\r\n"
        contentType = "Content-Type: text/html; charset=utf-8"
        return statusLine
