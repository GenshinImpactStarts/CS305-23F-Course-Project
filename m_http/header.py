from .status_code import StatusCode
import datetime

__all__ = 'Header',


class Header:
    # only parse the Request-Line!
    def parse_request_line(request):
        lines = request.split('\r\n')
        request_line = lines[0]
        method, path, version = request_line.split(' ')
        return method, path, version
    
    # parse the others!
    def parse_request_headers(request):
            lines = request.split('\r\n')
            header_lines = lines[1:]
            headers = {}
            for line in header_lines:
                if line:
                    key, value = line.split(': ', 1)
                    headers[key] = value

            return headers
    
    def generate_response_header(method, path):
        header = ''
        if method == 'GET' or method == 'HEAD':
            header += 'HTTP/1.1 200 OK\r\n'
            header += 'Content-Type: text/html; charset=utf-8\r\n'
        elif method == 'POST':
            header += 'HTTP/1.1 200 OK\r\n'
            header += 'Content-Type: text/html; charset=utf-8\r\n'
        else:
            header += 'HTTP/1.1 405 Method Not Allowed\r\n'
            header += 'Content-Type: text/html; charset=utf-8\r\n'

        header += 'Connection: close\r\n'
        header += '\r\n'
        return header
    


    def generate_response_headers(status_code, server_name=None, content_type=None, keep_alive=None, connection=None, age=None, date=None, x_cache_info=None, content_length=None):

        response_headers = f"HTTP/1.1 {status_code} {StatusCode.get_description(status_code)}\r\n"

        if server_name is not None:
            response_headers += f"Server: {server_name}\r\n"
        else: response_headers += f"Server: GenShinImpactStarts\r\n"

        if content_type is not None:
            response_headers += f"Content-Type: {content_type}\r\n" # maybe 'text/html; charset=utf-8'
        else: response_headers += f"Content-Type: text/html; charset=utf-8\r\n"

        if keep_alive is not None:
            response_headers += f"Keep-Alive: timeout={keep_alive[0]}, max={keep_alive[1]}\r\n" # like 'timeout=5, max=1000'
        else: pass # Who cares?

        if connection is not None:
            if connection==0:
                response_headers += f"Connection: close\r\n"
            if connection==1:
                response_headers += f"Connection: Keep-Alive\r\n"
        else: response_headers += f"Connection: Keep-Alive\r\n"

        if age is not None:
            response_headers += f"Age: {age}\r\n"
        else: pass # I don't know :(
        
        if date is not None:
            response_headers += f"Date: {date}\r\n"
        else: 
            current_datetime = datetime.datetime.now()
            http_date = current_datetime.strftime("%a, %d %b %Y %H:%M:%S GMT") # Not Sure!
            response_headers += f"Date: {http_date}"


        if x_cache_info is not None:
            response_headers += f"X-Cache-Info: {x_cache_info}\r\n"
        else: response_headers += f"X-Cache-Info: caching\r\n" #not sure

        if content_length is not None:
            response_headers += f"Content-Length: {content_length}\r\n"
        else: response_headers += f"Content-Length: 0\r\n"

        return response_headers

