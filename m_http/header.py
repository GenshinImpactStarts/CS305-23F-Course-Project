from .status_code import StatusCode
import datetime

__all__ = 'Header',

# No need for you to call
class HeadBuilder:
    def __init__(self):
        # the fields you must give
        self.status_code=None
        self.server_name=None
        self.content_type=None
        self.content_length=None
        self.connection=None

        # optional fields

class Headers:
    def __init__(self):
        pass

class Header:

    head_builder=HeadBuilder()
    server_name=None

    def initialize_headbuilder(self):
        self.head_builder=HeadBuilder()
        pass

    
    def __init__(self, server_name="GenShinImpactStarts"):
        self.initialize_headbuilder()
        self.server_name=server_name
        pass


    def get_headbuilder(self):
        return self.head_builder
    
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
        headers = Headers()
        for line in header_lines:
            if line:
                key, value = line.split(': ', 1)
                
                setattr(headers, key.strip(), value.strip())

        return headers
    
    # before you use this method, please edit the headbuilder correctly!
    def generate_response_headers(self):
        string_builder=[]
        string_builder.extend(f"HTTP/1.1 {self.head_builder.status_code} {StatusCode.get_description(self.head_builder.status_code)}\r\n") 
        
        string_builder.extend(f"Server: {self.head_builder.server_name}\r\n")

        if string_builder.content_type is not None:
            string_builder.extend(f"Content-Type: {self.head_builder.content_type}\r\n") # maybe 'text/html; charset=utf-8'
        else: response_headers += f"Content-Type: text/html; charset=utf-8\r\n"

        if string_builder.keep_alive is not None:
            response_headers += f"Keep-Alive: timeout={self.head_builder.keep_alive[0]}, max={self.head_builder.keep_alive[1]}\r\n" # like 'timeout=5, max=1000'
        else: pass # Who cares?

        if string_builder.connection is not None:
            if string_builder.connection==0:
                response_headers += f"Connection: close\r\n"
            if string_builder.connection==1:
                response_headers += f"Connection: Keep-Alive\r\n"
        else: response_headers += f"Connection: Keep-Alive\r\n"

        if string_builder.age is not None:
            response_headers += f"Age: {string_builder.age}\r\n"
        else: pass # I don't know :(
        
        if string_builder.date is not None:
            response_headers += f"Date: {string_builder.date}\r\n"
        else: 
            current_datetime = datetime.datetime.now()
            http_date = current_datetime.strftime("%a, %d %b %Y %H:%M:%S GMT") # Not Sure!
            response_headers += f"Date: {http_date}"


        if string_builder.x_cache_info is not None:
            response_headers += f"X-Cache-Info: {string_builder.x_cache_info}\r\n"
        else: pass #response_headers += f"X-Cache-Info: caching\r\n" #not sure

        if string_builder.content_length is not None:
            response_headers += f"Content-Length: {string_builder.content_length}\r\n"
        else: pass #response_headers += f"Content-Length: 0\r\n"

        self.initialize_headbuilder()# reset the headbuilder
        return response_headers

