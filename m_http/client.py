__all__ = ("Client",)

import socket
import os

class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.cookies = {}

    def send_request(self, method, uri, body=None, headers=None, file_path=None):
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

                if file_path:
                    with open(file_path, 'rb') as file:
                        body = file.read()
                    if headers is None:
                        headers = {}
                    if 'Content-Type' not in headers:
                        #default type
                        headers['Content-Type'] = 'text/plain'

                
                # Header_line
                request = f"{method} {uri} HTTP/1.1\r\nHost: {self.host}\r\n"

                if self.cookies:
                    request += f"Cookie: {self.format_cookies()}\r\n"

                # Additional headers
                if headers:
                    for header, value in headers.items():
                        request += f"{header}: {value}\r\n"

                # Handle POST
                if body and method == "POST":
                    request += f"Content-Length: {len(body)}\r\n\r\n"
                    if isinstance(body, str):
                        body = body.encode()                
                else:
                    request += "\r\n"

                try:
                    s.sendall(request.encode() + (body if body else b'')) # send msg
                except socket.error as e:
                    print(f"Error sending request: {e}")
                    return

                # Handle response
                try:
                    response = self.receive_response(s)
                    print("Response:\n", response)
                except socket.error as e:
                    print(f"Error receiving response: {e}")
                    return

                # Process response
                status_code, header_dict, body = self.parse_response(response)
                if method == "GET":
                    self.handle_get_response(status_code, uri, body)
                if "Set-Cookie" in header_dict:
                    self.store_cookies(header_dict["Set-Cookie"])

        except socket.error as e:
            print(f"Socket error: {e}")

    def format_cookies(self):
        return "; ".join(f"{key}={value}" for key, value in self.cookies.items())

    def store_cookies(self, cookie_header):
        cookies = cookie_header.split("; ")
        for cookie in cookies:
            key, value = cookie.split("=", 1)
            self.cookies[key] = value

    def receive_response(self, socket):
        response = ""
        while True:
            data = socket.recv(4096)
            if not data:
                break
            response += data.decode()
        return response

    def handle_get_response(self, status_code, uri, body):
        if status_code == "200":
            file_name = uri.strip("/").split("/")[-1]
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
