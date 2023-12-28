import os
import random
import re
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
        with conn:
            temp = b''
            header_class = header.Header()
            while True:
                receive = conn.recv(2048)
                if receive == b'':
                    break
                temp += receive
                testComplete, response = self.handle_request(
                    temp, header_class)
                if (testComplete != 0):
                    temp = b''
                    conn.send(response)
                if (testComplete == 2):
                    break
            conn.close()

    # the first pram is {0(not complete),1(keep alive),2(close)}
    def handle_request(self, request: bytes, header_class: header.Header):
        if (not request.find(b'\r\n\r\n')):
            return 0
        else:
            method, path, version = header.Header.parse_request_line(
                request.decode('utf-8'))
            header_pram, body = header.Header.parse_request_headers(
                request.decode('utf-8'))
            if (header_pram.content_length is not None) or (path.find('chunked=') and not path.find('chunked=0')):
                if (header_pram.content_length is not None):
                    if len(body) < int(header_pram.content_length):
                        return 0
                else:
                    if (not body.find(b'\r\n')):
                        return 0
            else:
                header_pram.content_length = 0

            response_body = b''
            if (method == " HEAD"):
                header_class.get_headbuilder().status_code = 200
                # response=header_class.generate_response_headers()
            else:
                # check identity
                if method == "GET":
                    response_body = self.__get_method(
                        header_pram, path, header_class.get_headbuilder())
                elif method == "POST":
                    header_class.get_headbuilder().status_code, username, password = self.__load_handle(
                        header_pram, header_class)
                    if header_class.get_headbuilder().status_code // 100 != 4:
                        response_body = self.__post_method(
                            header_pram, body, path, username, password, password, header_class.get_headbuilder())
                else:
                    header.get_headbuilder().status_code = 405

            header_class.get_headbuilder().content_length = len(response_body)
            response = header_class.generate_response_headers().encode('utf-8') + \
                b'\r\n'+response_body
            if header_pram.connection == 'close':
                return 2, response
            return 1, response

    # return the status_code and response_data
    def __get_method(self, header_pram, path, header_builder: header.HeadBuilder):
        path_part = path.split('?')
        access_path = path_part[0].strip('/')
        SusTech_code = ''
        response_body = b''
        if (len(path_part) > 1):
            SusTech_code = path_part[1]

        filePath = os.path.join(self.current_file_path, "data", access_path)
        filePath = filePath.replace('\\', '/')
        try:
            if ".." in filePath:  # prevent attack
                header_builder.status_code = 403
            elif os.path.exists(filePath):
                last_modified_time = time.gmtime(os.path.getmtime(filePath))
                if (header_pram.if_modified_since is not None):
                    try:
                        client_request_time = time.mktime(
                            time.strptime(header_pram.if_modified_since, "%a, %d %b %Y %H:%M:%S GMT"))
                    except ValueError:
                        pass
                    if client_request_time >= last_modified_time:
                        header_builder.status_code = 403
                if os.path.isdir(filePath):
                    if path[-1] != '/':
                        header_builder.status_code = 301
                        header_builder.location = path+'/'
                    else:
                        response_body = Body.get_folder(
                            filePath, return_html=("SUSTech-HTTP=0" not in SusTech_code))
                elif os.path.isfile(filePath):
                    file_content = Body.get_file(filePath)
                    response_body = file_content

                header_builder.status_code = 200
            else:
                header_builder.status_code = 400
        except StatusCode as e:
            header_builder.status_code = e.code
        return response_body

    def __post_method(self, header_pram, body, path, username, password, header_builder: header.HeadBuilder):
        upload_or_del = path.split("?")[0]
        Origin_path = path.split("?")[1].strip()  # ex:path=/11912113/abc.py
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
                            Body.recv_post_file(
                                body, access_path, "uploaded_file")
                        elif upload_or_del == "/delete":        # delete the document
                            if os.path.exists(access_path):
                                try:
                                    os.remove(access_path)
                                except Exception as e:
                                    header_builder.status_code
                    else:
                        header_builder.status_code = 404
                else:
                    header_builder.status_code = 403
            else:
                header_builder.status_code = 400
        except StatusCode as e:
            header_builder.status_code = e.code
        return None

    def __load_handle(self, header_pram, header_builder):
        response = 200
        username = None
        password = None
        if header_pram.authorization or header_pram.cookie:
            test_cookie = False
            if header_pram.cookie:
                cookie_params = header_pram.cookie.split("; ")
                cookie_dict = {}
                for param in cookie_params:
                    cookie_key = param.split("=")[0].lower()
                    cookie_value = param.split("=")[1].strip()
                    cookie_dict[cookie_key] = cookie_value
                if 'sid' in cookie_dict:
                    if cookie_dict['sid'] in self.cookie_set:
                        cookie = self.cookie_set[cookie_dict['sid']]
                        ddl = cookie.expire
                        if ddl is not None and ddl > datetime.datetime.now():
                            username = cookie.username
                            password = cookie.password
                        else:
                            test_cookie = True
                else:
                    test_cookie = True
                if test_cookie and header_pram.authorization:
                    if header_pram.authorization.startswith("Basic "):
                        authData = header_pram.split(" ", -1)
                        username = authData.split(':')[0]
                        password = authData.split(':')[1]

                        with open(os.path.join(self.current_file_path, 'user_data/user_info/userDatabase.txt'), 'r') as file:
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
                    pass
                    response = 401
        else:
            response = 401

        return response, username, password

    def __set_cookie(self, username, password, length=32, ttl_in_day=3):
        cookie_respond = []
        characters = string.ascii_letters + string.digits
        sid = ''.join(random.choice(characters) for _ in range(length))
        cookie_respond.append(f'SID={sid};')
        clear_time = datetime.datetime.now()
        ttl = datetime.timedelta(days=ttl_in_day)
        clear_time = clear_time+ttl
        cookie_expires_str = clear_time.strftime("%a, %d %b %Y %H:%M:%S GMT")
        cookie_respond.append(f'Expires={cookie_expires_str};')
        cookie_respond.append(f'Path=\\;Secure;HttpOnly')
        new_cookie = self.cookie_class(
            username=username, password=password, expire=clear_time, sid=sid)
        self.cookie_set[sid] = new_cookie
