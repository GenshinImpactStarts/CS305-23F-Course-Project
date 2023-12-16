# In order to help you use my code easily, I add this explanatory note in the very Beginning.
# The only class you need to pay attention to is [class Header]
# For a new special server, you need to use TODO"Header(your_server_name)" to initialize the header server.
# If you want to get msg in request_line, please use TODO"parse_request_line(request)". It will return method, path, version.
# If you want to get msg in other part of header, please use TODO"parse_request_headers(request)".The return value is a special construct, and its member variables may be None. Moreover, body_part may be returned.
# If you want to "generate_response_headers",please use TODO"get_headbuilder()"first.Then, fill as many member variables as possible in it.Finally,use TODO"generate_response_headers()",it will return a string for response header.
# Attention! "generate_response_headers()" will initialize the headerbuilder,make sure you use TODO"get_headbuilder()" every time you want to generate a response header.
# Have fun!

from ..status_code import StatusCode
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
        self.x_cache_info=None
        self.date=None
        self.age=None
        self.keep_alive=None
        # optional fields

class Headers:
    def __init__(self):
        self.accept = None
        self.accept_charset = None
        self.accept_encoding = None
        self.accept_language = None
        self.authorization = None
        self.cache_control = None
        self.connection = None
        self.content_length = None
        self.content_type = None
        self.cookie = None
        self.host = None
        self.if_modified_since = None
        self.if_none_match = None
        self.referer = None
        self.user_agent = None

def http_header_to_python(header):
    return header.lower().replace("-", "_")


class Header:

    server_name=None

    def initialize_headbuilder(self):
        self.head_builder=HeadBuilder()
        self.head_builder.server_name=self.server_name
        pass

    
    def __init__(self, server_name="GenShinImpactStarts"):
        self.server_name=server_name
        self.initialize_headbuilder()
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
        if '\r\n\r\n' in request:
            header_part, body_part = request.split('\r\n\r\n', 1)
        else:
            header_part = request
            body_part = '' 
        lines = header_part.split('\r\n')
        headers = Headers()
        for line in lines[1:]:
            if line == '':
                break
            key, value = line.split(': ', 1)
            setattr(headers, http_header_to_python(key.strip()), value.strip())

        return headers,body_part
    
    # before you use this method, please edit the headbuilder correctly!
    def generate_response_headers(self):
        string_builder=[]
        string_builder.append(f"HTTP/1.1 {self.head_builder.status_code} {StatusCode.get_description(self.head_builder.status_code)}\r\n") 
        string_builder.append(f"Server: {self.head_builder.server_name}\r\n")

        if self.head_builder.content_type is not None:
            string_builder.append(f"Content-Type: {self.head_builder.content_type}\r\n") # maybe 'text/html; charset=utf-8'
        else: string_builder.append(f"Content-Type: text/html; charset=utf-8\r\n")

        if self.head_builder.keep_alive is not None:
            string_builder.append(f"Keep-Alive: timeout={self.head_builder.keep_alive[0]}, max={self.head_builder.keep_alive[1]}\r\n") # like 'timeout=5, max=1000'
        else: pass # Who cares?

        if self.head_builder.connection is not None:
            if self.head_builder.connection==0:
                string_builder.append(f"Connection: close\r\n")
            if self.head_builder.connection==1:
                string_builder.append(f"Connection: Keep-Alive\r\n")
        else: string_builder.append(f"Connection: Keep-Alive\r\n")

        if self.head_builder.age is not None:
            string_builder.append(f"Age: {self.head_builder.age}\r\n")
        else: pass # I don't know :(
        
        if self.head_builder.date is not None:
            string_builder.append(f"Date: {self.head_builder.date}\r\n")
        else: 
            current_datetime = datetime.datetime.now()
            http_date = current_datetime.strftime("%a, %d %b %Y %H:%M:%S GMT") # Not Sure!
            string_builder.append(f"Date: {http_date}\r\n")


        if self.head_builder.x_cache_info is not None:
            string_builder.append(f"X-Cache-Info: {self.head_builder.x_cache_info}\r\n")
        else: pass #response_headers += f"X-Cache-Info: caching\r\n" #not sure

        if self.head_builder.content_length is not None:
            string_builder.append(f"Content-Length: {self.head_builder.content_length}\r\n")
        else: pass #response_headers += f"Content-Length: 0\r\n"

        self.initialize_headbuilder()# reset the headbuilder
        return ''.join(string_builder)

