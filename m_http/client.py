__all__ = ("Client",)

import mimetypes
import socket
import os

class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.cookies = {}

    def compile_request(self, method, uri, body=None, headers=None, file_path=None, isChunk=False):
        
        if file_path:
            mime_type, _ = mimetypes.guess_type(file_path)
            if headers is None:
                headers = {}
            headers['Content-Type'] = mime_type or 'application/octet-stream'


        request = f"{method} {uri} HTTP/1.1\r\nHost: {self.host}\r\n"
        if self.cookies:
            request += f"Cookie: {self.format_cookies()}\r\n"
        if headers:
            for header, value in headers.items():
                request += f"{header}: {value}\r\n"    
            

        if isChunk and file_path:
            
            request += "Transfer-Encoding: chunked\r\n\r\n"
            temp = []
            temp.append(request.encode())
            with open(file_path, 'rb') as file:
                while True:
                    chunk = file.read(4096)
                    if not chunk:
                        break
                    temp.append(f"{len(chunk):X}\r\n".encode() + chunk + b"\r\n") 
            temp.append(b"0\r\n\r\n")
            
            return b''.join(temp) # here TODO
        
        else:
            temp = []
            if body:
                request += f"Content-Length: {len(body)}\r\n\r\n"
                temp.append(request.encode)
                if isinstance(body, str):
                    body = body.encode()
                temp.append(request.encode() + body)
            else:
                temp.append(b"\r\n")
                
            return b''.join(temp) # here TODO    
                
                
        # receive the response
        try:
            response_in_bytes = self.receive_response_bytes(s) 
        except socket.error as e:
            print(f"Error receiving response: {e}")
            return
        # handle the response
        
        #TODO decode
        self.handle_response(response_in_bytes,method,uri)

    
    def send_request(self, method, uri, body=None, headers=None, file_path=None, isChunk=False):
        request = self.compile_request(method, uri, body, headers, file_path, isChunk)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.connect((self.host, self.port))
                except socket.timeout:
                    print(f"Connection to {self.host}:{self.port} timed out.")
                    return
                except socket.gaierror:
                    print(f"Address-related error connecting to {self.host}:{self.port}")
                    return
                s.sendall(request)
                
                try:
                    response_headers,response_body = self.receive_response(s)
                    print("Response:\n", response_headers+response_body)
                except socket.error as e:
                    print(f"Error receiving response: {e}")
                    return

                # 处理响应
                
                status_code, header_dict, body = self.parse_response(response_headers)
                if method == "GET":
                    self.handle_get_response(status_code, uri, body)
                if "Set-Cookie" in header_dict:
                    self.store_cookies(header_dict["Set-Cookie"])
                
                
                
                
                
        except socket.error as e:
            print(f"Socket error: {e}")
            
                    
                
    def receive_response_bytes(self,sock):        
        response=b''
        while True:
            data = sock.recv(4096)
            if not data:
                break
            response += data
        return response
            
    def handle_response(self,response,method,uri=None):
        response = response.decode() # ?
        print("Response:\n", response)
        status_code, header_dict, body = self.parse_response(response)
        if method == "GET":
            self.handle_get_response(status_code, uri, body)
        if "Set-Cookie" in header_dict:
            self.store_cookies(header_dict["Set-Cookie"])
        
    def format_cookies(self):
        return "; ".join(f"{key}={value}" for key, value in self.cookies.items())

    def store_cookies(self, cookie_header):
        cookies = cookie_header.split("; ")
        for cookie in cookies:
            key, value = cookie.split("=", 1)
            self.cookies[key] = value

    def receive_response(self, sock):
        response_headers = ''
        while True:
            line = sock.recv(4096).decode()
            if not line or line == '\r\n':
                break
            response_headers += line

        # check chunk
        if 'transfer-encoding' in response_headers.lower() and 'chunked' in response_headers.lower():
            return response_headers,self.receive_chunked_response(sock)
        else:
            response_body = ''
            while True:
                data = sock.recv(4096).decode()
                if not data:
                    break
                response_body += data
            return response_headers,response_body
        
    def receive_chunked_response(self, sock):
        response_body = ''
        while True:
            chunk_size_str = sock.recv(4096).decode().split('\r\n')[0]
            try:
                chunk_size = int(chunk_size_str, 16)
            except ValueError:
                print("Invalid chunk size received.")
                break
            if chunk_size == 0:
                sock.recv(4096)  # 读取最后的空行?
                break
            chunk = sock.recv(chunk_size).decode(errors='ignore')  # 处理非 UTF-8 编码?
            response_body += chunk
            sock.recv(4096)  # 读取块后的空行?
        return response_body

    def handle_get_response(self, status_code, uri, body):
        if status_code == "200":
            file_name = os.path.basename(uri)  # 防止路径遍历攻击?
            with open(file_name, "w") as file:
                file.write(body)
            print(f"Data from {uri} saved to {file_name}")
        else:
            print(f"GET request failed with status code: {status_code}")

    def parse_response(self, response):
        headers, _, body = response.partition("\r\n\r\n")
        status_line, _, header_lines = headers.partition("\r\n")
        status_code = status_line.split(" ")[1]
        
        header_dict = {}
        for line in header_lines.split("\r\n"):
            key, value = line.split(": ", 1)
            header_dict[key] = value

        return status_code, header_dict, body


if __name__ == "__main__":
    client = Client("127.0.0.1", 65432)

    client.send_request("GET", "/")

    client.send_request("HEAD", "/")

    client.send_request("POST", "/", "Really want to play Genshin Impact",file_path="D:\Genshin Impact\laucher.txt")
