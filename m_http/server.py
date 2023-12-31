import base64
import mimetypes
import os
import random
import re
import shutil
import string
import time
import socket
from .threading_tcp import ThreadingTCP
import datetime
from .http_content import header
from .http_content.body import Body
from .status_code import StatusCode

__all__ = 'Server',


class Server(ThreadingTCP):
    class cookie_class:
        def __init__(self, username: str, password: str, expire, sid):
            self.sid = sid
            self.username = username
            self.password = password
            self.expire = expire

    cookie_set = {}
    current_file_path = '.'

    def handle(self, conn: socket.socket, addr: tuple):
        temp = []
        testComplete = 0
        body_length = 0
        header_class = header.Header()
        while True:
            receive = conn.recv(2048)
            if receive == b'':
                break
            temp.append(receive)
            testComplete, body_length, response = self.handle_request(
                temp, header_class, testComplete, body_length)

            if (testComplete == 2 or testComplete == 3):
                temp = []
                testComplete = 0
                body_length = 0
                for i in response:
                    conn.sendall(i)
            if testComplete == 3:
                break

    # the first pram is {0(header not complete),1(body not complete),2(keep alive),3(close)}
    def handle_request(self, request: bytes, header_class: header.Header, handle_state: int, body_length: int):
        if (handle_state == 0 and request[-1].find(b'\r\n\r\n') == -1):
            return 0, 0, None
        if (handle_state == 0):
            join_req = b''.join(request)
            temp_req = join_req.split(b'\r\n\r\n', 1)
            tempHeader = temp_req[0]
            rest = None
            if (len(temp_req) > 1):
                rest = temp_req[1]
            request = [tempHeader, rest]
            try:
                method, path, version = header.Header.parse_request_line(
                    join_req)
                header_pram, body = header.Header.parse_request_headers(
                    join_req)
            except StatusCode as e:
                header_class.get_headbuilder().status_code = e.code

        body_length += len(request[-1])
        if (header_pram.content_length != 0):
            if (header_pram.content_length is not None) or (header_pram.transfer_encoding is not None and header_pram.transfer_encoding.lower() == 'chunked'):
                if (header_pram.content_length is not None):
                    if body_length < int(header_pram.content_length):
                        return 1, body_length, None
                else:
                    if (body.find(b'\r\n\r\n') == -1):
                        return 1, body_length, None
        else:
            header_pram.content_length = 0

        if (header_class.get_headbuilder().status_code == None or
                header_class.get_headbuilder().status_code // 100 != 4):
            need_chunk = ('chunked=1' in path.replace(' ', ''))
            response_body = b''

            header_class.get_headbuilder().status_code, username, password = self.__load_handle(
                header_pram, header_class.get_headbuilder())
            if header_class.get_headbuilder().status_code // 100 != 4:
                if method == "GET" or method == "HEAD":
                    response_body = self.__get_method(
                        header_pram, path, header_class.get_headbuilder(), need_chunk)
                elif method == "POST":
                    response_body = self.__post_method(
                        header_pram, body, path, username, password, header_class.get_headbuilder(),
                        header_pram.transfer_encoding is not None and header_pram.transfer_encoding.lower() == 'chunked')
                else:
                    header_class.get_headbuilder().status_code = 405

        if (not need_chunk):
            if (response_body is not None):
                header_class.get_headbuilder().content_length = len(response_body)
            else:
                response_body = b''
                header_class.get_headbuilder().content_length = 0
        else:
            header_class.get_headbuilder().transfer_encoding = 'chunked'

        if (header_pram.range):
            if len(header_pram.range) != 1 and header_class.get_headbuilder().self_boundary:
                header_class.get_headbuilder().content_type = 'multipart/byteranges; boundary=' + \
                    header_class.get_headbuilder().self_boundary

        header_class.get_headbuilder().connection = header_pram.connection

        response = []
        response.append(
            header_class.generate_response_headers().encode('utf-8')+b'\r\n')
        if (method != "HEAD"):
            response.append(response_body)
        if header_pram.connection == 'close':
            return 3, 0, response
        return 2, 0, response

    # return the status_code and response_data
    def __get_method(self, header_pram: header.Headers, path, header_builder: header.HeadBuilder,
                     need_chunk: bool):
        if (path[:13] == 'upload?path=') or (path[:13] == 'delete?path='):
            header_builder.status_code = 405
            return
        path_part = path.split('?')
        access_path = path_part[0].lstrip('/')
        SusTech_code = ''
        response_body = b''
        if (len(path_part) > 1):
            SusTech_code = path_part[1]
        if (access_path.startswith('/')):
            access_path.replace('/', '', 1)
        filePath = os.path.join(self.current_file_path, "data", access_path)
        filePath = filePath.replace('\\', '/')
        try:

            if ".." in filePath:  # prevent attack
                header_builder.status_code = 403
            elif os.path.exists(filePath):
                if header_pram.if_modified_since is not None:
                    last_modified_timestamp = os.path.getmtime(filePath)
                    last_modified_time = datetime.datetime.utcfromtimestamp(
                        last_modified_timestamp)
                    try:
                        client_request_time = datetime.datetime.strptime(
                            header_pram.if_modified_since, "%a, %d %b %Y %H:%M:%S GMT")
                    except ValueError:
                        pass  # i choose to ignore
                    else:
                        if client_request_time >= last_modified_time:
                            header_builder.status_code = 304
                            return None
                if header_pram.range is None:
                    if os.path.isdir(filePath):
                        if filePath[-1] != '/':
                            header_builder.status_code = 301
                            header_builder.location = os.path.basename(
                                access_path)+'/'
                            return None
                        else:
                            if (("SUSTech-HTTP=1" in SusTech_code)):
                                header_builder.content_type = 'text/plain'
                            else:
                                header_builder.content_type = 'text/html'

                            response_body = Body.get_folder(
                                filePath, return_html=("SUSTech-HTTP=1" not in SusTech_code), chunked=need_chunk)
                    elif os.path.isfile(filePath):
                        header_builder.content_type, _ = mimetypes.guess_type(
                            filePath)
                        file_content = Body.get_file(
                            filePath, chunked=need_chunk)
                        response_body = file_content
                    header_builder.status_code = 200
                else:
                    if os.path.isdir(filePath):
                        if filePath[-1] != '/':
                            header_builder.status_code = 301
                            header_builder.location = os.path.basename(
                                access_path)+'/'
                            return None
                        else:
                            if (("SUSTech-HTTP=0" not in SusTech_code)):
                                header_builder.content_type = 'html'
                            else:
                                header_builder.content_type = 'txt'
                            if len(header_pram.range) == 1:
                                response_body = Body.get_part_folder(
                                    filePath, range=header_pram.range[0], return_html=("SUSTech-HTTP=0" not in SusTech_code), chunked=need_chunk)
                                total_len=os.path.getsize(filePath)
                                header_builder.content_range = Body.normailize_range(range=header_pram.range[0],
                                                                                     total_len=total_len)+'/'+total_len
                            else:
                                characters = string.ascii_letters + string.digits
                                self_boundary = ''.join(random.choice(
                                    characters) for i in range(30))
                                response_body = Body.get_multi_part_folder(
                                    filePath, range=header_pram.range, boundary=self_boundary, return_html=("SUSTech-HTTP=0" not in SusTech_code), chunked=need_chunk)
                    elif os.path.isfile(filePath):
                        header_builder.content_type, _ = mimetypes.guess_type(
                            filePath)
                        if len(header_pram.range) == 1:
                            file_content = Body.get_part_file(
                                filePath, range=header_pram.range[0], chunked=need_chunk)
                        else:
                            characters = string.ascii_letters + string.digits
                            self_boundary = ''.join(random.choice(
                                characters) for i in range(30))
                            file_content = Body.get_multi_part_file(
                                filePath, boundary=self_boundary, ranges=header_pram.range, chunked=need_chunk)
                        response_body = file_content
                    if (header_pram.range):
                        header_builder.status_code = 206
                    else:
                        header_builder.status_code = 200
            else:
                header_builder.status_code = 404
        except StatusCode as e:
            header_builder.status_code = e.code
        return response_body

    def __post_method(self, header_pram: header.Headers, body: bytes, path, username, password,
                      header_builder: header.HeadBuilder, is_chunk: bool):
        p_s = path.split('?', 1)
        header_builder.status_code = 200
        if (len(p_s) > 1):
            upload_or_del = p_s[0]
            Origin_path = p_s[1].strip()  # ex:upload?path=/11912113/abc.py
        else:
            header_builder.status_code = 405
            return None
        pattern = r'path=(\S+)'
        match = re.search(pattern, Origin_path)
        try:
            if match:
                result = match.group(1)

                user_post = result.split("/")[0]
                if user_post == username:
                    access_path = os.path.join(
                        self.current_file_path, 'data', result)
                    access_path = access_path.replace('\\', '/')
                    if os.path.exists(access_path):
                        if upload_or_del == "/upload":          # upload the document
                            if header_pram.content_type.find('multipart/form-data') != -1:
                                if (header_pram.boundary is not None):
                                    Body.recv_post_multi_part_file(
                                        body, access_path, header_pram.boundary)
                                else:
                                    header_builder.status_code = 405
                            else:
                                if (header_pram.content_disposition and "filename" in header_pram.content_disposition):
                                    Body.recv_post_file(
                                        body, access_path, header_pram.content_disposition["filename"], chunked=is_chunk)
                                else:
                                    header_builder.status_code = 405
                        elif upload_or_del == "/delete":        # delete the document
                            if os.path.exists(access_path):
                                try:
                                    if os.path.isdir(access_path):
                                        if (access_path == '/'):
                                            header_builder.status_code = 400
                                        else:
                                            shutil.rmtree(access_path)
                                    if os.path.isfile(access_path):
                                        os.remove(access_path)
                                except Exception as e:
                                    header_builder.status_code
                        else:
                            header_builder.status_code = 405
                    else:
                        header_builder.status_code = 404
                else:
                    header_builder.status_code = 403
            else:
                header_builder.status_code = 400
        except StatusCode as e:
            header_builder.status_code = e.code
        return None

    def __load_handle(self, header_pram: header.Headers, header_builder: header.HeadBuilder):
        response = 200
        username = None
        password = None
        if header_pram.authorization or header_pram.cookie:
            test_cookie = False
            if header_pram.cookie:
                cookie_params = header_pram.cookie.split("; ")
                cookie_dict = {}

                for param in cookie_params:
                    cookie_part = param.split("=")
                    if len(cookie_part) > 1:
                        cookie_key = cookie_part[0].lower()
                        cookie_value = cookie_part[1].strip()
                        cookie_dict[cookie_key] = cookie_value
                if 'session-id' in cookie_dict:
                    if cookie_dict['session-id'] in self.cookie_set:
                        cookie = self.cookie_set[cookie_dict['session-id']]
                        ddl = cookie.expire
                        if ddl is not None and ddl > datetime.datetime.now():
                            username = cookie.username
                            password = cookie.password
                        else:
                            test_cookie = True
            else:
                test_cookie = True
            if test_cookie:
                if header_pram.authorization:
                    if header_pram.authorization.startswith("Basic "):
                        try:
                            authData = base64.b64decode(
                                header_pram.authorization.split(" ")[-1]).decode('utf-8')
                        except (UnicodeDecodeError, IndexError):
                            response = 401
                            return response, username, password

                        username, password = authData.split(':', 1)
                        with open(os.path.join(self.current_file_path, 'user_data\\userDatabase.txt'), 'r') as file:
                            file_contents = file.read()
                            search_string = username+'/'+password+';'
                            if search_string in file_contents:
                                response = 200
                                header_builder.set_cookie = self.__set_cookie(
                                    username, password)
                            else:
                                response = 401
                    else:
                        response = 401                               # 检查用户名和密码是否匹配
                else:
                    response = 401
        else:
            response = 401
        if (username == None):
            response = 401
        return response, username, password

    def __set_cookie(self, username, password, length=32, ttl_in_day=3):
        cookie_respond = []
        characters = string.ascii_letters + string.digits
        sid = ''.join(random.choice(characters) for i in range(length))
        cookie_respond.append(f'session-id={sid};')

        clear_time = datetime.datetime.utcnow()
        ttl = datetime.timedelta(days=ttl_in_day)
        clear_time = clear_time+ttl
        # cookie_expires_str = clear_time.strftime("%a, %d %b %Y %H:%M:%S GMT")
        # cookie_respond.append(f'Expires={cookie_expires_str};')
        # cookie_respond.append(f'Path=\\;Secure;HttpOnly')
        new_cookie = self.cookie_class(
            username=username, password=password, expire=clear_time, sid=sid)
        self.cookie_set[sid] = new_cookie

        set_cookie = ''.join(cookie_respond)
        return set_cookie
