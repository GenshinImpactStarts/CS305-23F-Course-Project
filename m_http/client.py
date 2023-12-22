__all__ = ("Client",)

import socket
import os


class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.cookies = {}

    def send_request(self, method, uri, body=None, headers=None):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host, self.port))

            # Header_line
            request = f"{method} {uri} HTTP/1.1\r\nHost: {self.host}\r\n"

            if self.cookies:
                request += f"Cookie: {self.format_cookies()}\r\n"

            # additional header
            if headers:
                for header, value in headers.items():
                    request += f"{header}: {value}\r\n"

            # handele POST
            if body and method == "POST":
                request += f"Content-Length: {len(body)}\r\n\r\n{body}"
            else:
                request += "\r\n"

            try:
                s.sendall(request.encode()) # send msg
            except socket.error as e:
                print(f"Error sending request: {e}")
                return

            # handle response
            response = self.receive_response(s)
            print("Response:\n", response)

            if method == "GET":
                self.handle_get_response(response, uri)
            else: status_code, header_dict, body = self.parse_response(response)
                  # not complete yet!
            if "Set-Cookie" in header_dict:
                self.store_cookies(header_dict["Set-Cookie"])
            
    def format_cookies(self):
        return "; ".join(f"{key}={value}" for key, value in self.cookies.items())

    def store_cookies(self, cookie_header):
        cookies = cookie_header.split("; ")
        for cookie in cookies:
            key, value = cookie.split("=", 1)
            self.cookies[key] = value        
            
    def receive_response(self, socket):
        response = ""
        try:
            while True:
                data = socket.recv(4096)
                if not data:
                    break
                response += data.decode()
        except socket.error as e:
            print(f"Error receiving response: {e}")
        return response

    def handle_get_response(self, response, uri):
        status, headers, body = self.parse_response(response)
        if status == "200":
            file_name = uri.strip("/").split("/")[-1]
            with open(file_name, "w") as file:
                file.write(body)
            print(f"Data from {uri} saved to {file_name}")
        else:
            print(f"GET request failed with status code: {status}")

    def parse_response(self, response):
        headers, aba, body = response.partition("\r\n\r\n")
        status_line, aba, header_lines = headers.partition("\r\n")
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

    client.send_request("POST", "/", "Really want to play Genshin Impact")
