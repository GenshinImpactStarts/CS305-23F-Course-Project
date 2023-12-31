# In order to help you use my code easily, I add this explanatory note in the very Beginning.
# The only class you need to pay attention to is [class Header]
# For a new special server, you need to use TODO"Header(your_server_name)" to initialize the header server.
# If you want to get msg in request_line,
#   please use TODO"parse_request_line(request)". It will return method, path, version.
# If you want to get msg in other part of header,
#   please use TODO"parse_request_headers(request)".The return value is a special construct, and its member variables may be None. Moreover, body_part may be returned.
# If you want to "generate_response_headers",
#   please use TODO"get_headbuilder()"first.Then, fill as many member variables as possible in it.Finally,use TODO"generate_response_headers()",it will return a string for response header.
# Attention! "generate_response_headers()"
#   will initialize the headerbuilder,
#   make sure you use TODO"get_headbuilder()" every time you want to generate a response header.
# Have fun!

from ..status_code import StatusCode
import datetime

__all__ = ("Header",)


# No need for you to call
class HeadBuilder:
    def __init__(self):
        # the fields you must give
        self.status_code = None
        self.server_name = None
        self.content_type = None
        self.content_length = None
        self.connection = None
        self.x_cache_info = None
        self.date = None
        self.age = None
        self.keep_alive = None
        self.set_cookie = None
        self.transfer_encoding = None
        self.location = None
        self.accept_charset = None
        self.boundary = None #not used in the header
        # optional fields


class Headers:
    class AcceptLanguage:
        def __init__(self, header):
            if header == None:
                return
            self.top_priority = None
            self.possible_options = (
                []
            )  # [(lang, weight),(lang, weight),and so on] by weight DESC
            languages = header.split(",")

            for language in languages:
                parts = language.strip().split(";")
                lang = parts[0].strip()
                if len(parts) > 1:
                    weight = float(parts[1].split("=")[1])
                else:
                    weight = 1.0

                if self.top_priority is None or weight > self.top_priority[1]:
                    self.top_priority = (lang, weight)
                self.possible_options.append((lang, weight))
            self.possible_options.sort(key=lambda x: x[1], reverse=True)

    def __init__(self):
        self.accept = None
        self.accept_charset = None
        self.accept_encoding = None
        self.accept_language = Headers.AcceptLanguage(None)
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
        self.transfer_encoding = None
        self.range = None
        self.content_disposition = None #返回字典，分为type，name，filename


def http_header_to_python(header):
    return header.lower().replace("-", "_")


class Header:
    server_name = None

    def initialize_headbuilder(self):
        self.head_builder = HeadBuilder()
        self.head_builder.server_name = self.server_name
        pass

    def __init__(self, server_name="GenShinImpactStarts"):
        self.server_name = server_name
        self.initialize_headbuilder()
        pass

    def get_headbuilder(self):
        return self.head_builder

    # only parse the Request-Line!
    def parse_request_line(request):
        if isinstance(request, bytes):
            request = request.decode('utf-8')
        lines = request.split("\r\n")
        request_line = lines[0]
        method, path, version = [v.strip() for v in request_line.split(" ")]
        return method, path, version

    # parse the others!

    def parse_request_headers(request):
        if b"\r\n\r\n" in request:
            header_part, body_part = request.split(b"\r\n\r\n", 1)
            if isinstance(header_part, bytes):
                header_part = request.decode('utf-8')
        else:
            if isinstance(request, bytes):
                header_part = request.decode('utf-8')
            body_part = b""
        lines = header_part.split("\r\n")
        headers = Headers()
        for line in lines[1:]:
            if line == "":
                break
            key, value = line.split(": ", 1)
            key = http_header_to_python(key.strip())
            if key == "accept_charset":
                headers.accept_charset = [v.strip() for v in value.split(",")]
            elif key == "accept_language":
                headers.accept_language = Headers.AcceptLanguage(value.strip())
            elif key == "range":
                ranges = value.strip().replace("bytes=", "").split(",")
                range_tuples = []
                for r in ranges:
                    start, end = r.split("-")
                    if end==None:
                        raise StatusCode(416)
                    if start == "":
                        range_tuples.append((-int(end), None))
                    elif end == "":
                        range_tuples.append((int(start), None))
                    else:
                        if int(start)>int(end):
                            raise StatusCode(416)
                        range_tuples.append((int(start), int(end)))
                headers.range = range_tuples
            elif key == "content_disposition":
                parts = [part.strip() for part in value.split(";")]
                disposition_info = {"type": parts[0]}
                for part in parts[1:]:
                    key, val = part.split("=", 1)
                    disposition_info[key.strip()] = val.strip(' "')
                headers.content_disposition = disposition_info
            else:
                setattr(headers, key, value.strip())

        return headers, body_part

    # before you use this method, please edit the headbuilder correctly!
    def generate_response_headers(self):
        string_builder = []
        string_builder.append(f"HTTP/1.1 {self.head_builder.status_code} {StatusCode.get_description(self.head_builder.status_code)}\r\n")
        string_builder.append(f"Server: {self.head_builder.server_name}\r\n")

        if self.head_builder.content_type is not None:
            string_builder.append(
                f"Content-Type: {self.head_builder.content_type}\r\n"
            )  # maybe 'text/html; charset=utf-8'
        else:
            # string_builder.append(f"Content-Type: text/html; charset=utf-8\r\n")
            pass

        if self.head_builder.keep_alive is not None:
            string_builder.append(
                f"Keep-Alive: timeout={self.head_builder.keep_alive[0]}, max={self.head_builder.keep_alive[1]}\r\n"
            )  # like 'timeout=5, max=1000'
        else:
            pass  # Who cares?

        if self.head_builder.connection is not None:
            if self.head_builder.connection == "close":
                string_builder.append(f"Connection: close\r\n")
            if self.head_builder.connection == "Keep-Alive":
                string_builder.append(f"Connection: Keep-Alive\r\n")
        else:
            pass  # string_builder.append(f"Connection: Keep-Alive\r\n")

        if self.head_builder.age is not None:
            string_builder.append(f"Age: {self.head_builder.age}\r\n")
        else:
            pass  # I don't know :(

        if self.head_builder.date is not None:
            string_builder.append(f"Date: {self.head_builder.date}\r\n")
        else:
            current_datetime_utc = datetime.datetime.utcnow()
            http_date = current_datetime_utc.strftime(
                "%a, %d %b %Y %H:%M:%S GMT")
            string_builder.append(f"Date: {http_date}\r\n")

        if self.head_builder.set_cookie is not None:
            string_builder.append(
                f"Set-Cookie: {self.head_builder.set_cookie}\r\n")
        else:
            pass

        if self.head_builder.x_cache_info is not None:
            string_builder.append(
                f"X-Cache-Info: {self.head_builder.x_cache_info}\r\n")
        else:
            pass  # response_headers += f"X-Cache-Info: caching\r\n" #not sure

        if self.head_builder.content_length is not None:
            string_builder.append(
                f"Content-Length: {self.head_builder.content_length}\r\n"
            )
        else:
            pass  # response_headers += f"Content-Length: 0\r\n"

        if self.head_builder.transfer_encoding is not None:
            string_builder.append(
                f"Transfer-Encoding: {self.head_builder.transfer_encoding}\r\n")

        if self.head_builder.accept_charset is not None:
            string_builder.append(
                f"Accept-Charset: {self.head_builder.accept_charset}\r\n")
            
        if self.head_builder.location is not None:
            string_builder.append(f"Location: {self.head_builder.location}")

        self.initialize_headbuilder()  # reset the headbuilder
        return "".join(string_builder)
