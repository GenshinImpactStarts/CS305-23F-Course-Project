__all__ = 'Server',

import base64
import socket
import threading
from status_code import StatusCode


class Server:
    def __init__(self,host,port) -> None:
        self.host=host
        self.port=port
    
    def requestHandle(self, conn: socket, addr):
        with conn:
            while True:
                request = conn.recv(1024).decode('utf-8')
                lines = request.split('\n')
                request_line = lines[0].strip().split()
                method = request_line[0]
                url = request_line[1]
                http_version = request_line[2]
                messageHeader ={}
                for line in lines:
                    parts=line.split(':')
                    if parts.length>2:
                        messageHeader[parts[0]]=parts[1]
                
                authHeader = messageHeader.get('Authorization', None)       #检查授权
                if authHeader:
                    decodedAuth = authHeader.decode('utf-8')
                    username =decodedAuth.split(':')[0]
                    password =decodedAuth.split(':')[1]
                    pass                                        # 检查用户名和密码是否匹配
                else:
                    response = self.respondHeaderBuilder(http_version, "401")
                    #conn.sendall(response.encode('utf-8'))
                
                if method == "GET":
                    filePath=url    #还没处理呢
                    try:
                        with io.open(filePath,'r',encoding= 'utf-8') as file:
                            data=file.read
                    except FileNotFoundError:
                        response = self.respondHeaderBuilder(http_version, "404")
                        #conn.sendall(response.encode('utf-8'))
                elif method == "POST":
                    pass
                elif method == "HEAD":
                    pass
                else :
                    pass
                
                if messageHeader['Connection']=='close':
                    conn.close()
                    break
            

    def respondHeaderBuilder(self, version, code) -> str:
        statusLine = f"{version} {code} {StatusCode.get_description(code)}\r\n"
        contentType="Content-Type: text/html; charset=utf-8"
        return statusLine

    def start_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((self.host, self.port))
            server_socket.listen()
            print(f"Server listening on http://{host}:{port}/")
            while True:
                conn, addr = server_socket.accept()
                thread = threading.Thread(target=self.requestHandle, args=(conn, addr))
                thread.start()
