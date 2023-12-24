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

__all__ = 'Server',


class Server(ThreadingTCP):
    def handle(self, conn: socket.socket, addr: tuple):
        with conn:
            temp = ''
            header_class = header.Header
            while True:
                temp += conn.recv(2048)
                testComplete, response = self.handle_request(temp)
                if (testComplete!=0):
                    temp = ''
                if (testComplete==2):
                    break
            conn.close()

    # the first pram is {0(not complete),1(keep alive),2(close)}
    def handle_request(self, request: bytes, header_class):
        if (not request.find(b'\r\n\r\n')):
            return 0
        else:
            method, path, version = header.Header.parse_request_line(request)
            header_pram, body = header.Header.parse_request_headers(request)
            if (header_pram.content_length is not None) ^ (path.find('chunked=') and not path.find('chunked=0')):
                if (header_pram.content_length is not None):
                    if len(body) < int(header_pram.content_length):
                        return 0
                else:
                    if (not body.find(b'\r\n')):
                        return 0
            else:
                header_class.get_headbuilder(self).status_code = 400

            if (method == " HEAD"):
                header_class.get_headbuilder(self).status_code = 200
            else:
                # check identity
                header.get_headbuilder(
                    self).status_code, username, password = self.__load_handle(header_pram)
                if header_class.get_headbuilder(self).status_code / 100 != 4:
                    if method == "GET":
                        response_data = self.__get_method(
                            self, header_pram, path, username, password, header_class.get_headbuilder)

                    elif method == "POST":
                        response_data = self.__post_method(
                            self, header_pram, body, path, username, password, password, header_class.get_headbuilder)
                    else:
                        header.get_headbuilder(self).status_code = 405
                else:
                    pass
            
            if header_pram.connection == 'close':
                return 2

    # return the status_code and response_data
    def __get_method(self, header_pram, path, username, password, header_builder: header.HeadBuilder):
        access_path = path.split("?")[0]
        SusTech_code = path.split("?")[1]
        filePath = "./data/"+access_path
        if ".." in filePath:  # prevent attack
            header_builder.status_code = 403
        elif os.path.exists(filePath):
            last_modified_time = time.gmtime(os.path.getmtime(path))
            try:
                client_request_time = time.mktime(
                    time.strptime(header_pram.if_modified_since, "%a, %d %b %Y %H:%M:%S GMT"))
            except ValueError:
                pass
            if client_request_time >= last_modified_time:
                header_builder.status_code = 403
            if os.path.isdir(filePath):
                if "SUSTech-HTTP=1" in SusTech_code:
                    response_data = Body.get_folder(filePath, return_html=True)
                else:
                    response_data = Body.get_folder(
                        filePath, return_html=False)
            elif os.path.isfile(filePath):
                file_content = Body.get_file(filePath)
                response_data = file_content

            header_builder.status_code = 200
        else:
            header_builder.status_code = 400
        return response_data

    def __post_method(self, header_pram, body, path, username, password, header_builder: header.HeadBuilder):
        upload_or_del = path.split("?")[0]
        Origin_path = path.split("?")[1].strip()  # ex:path=/11912113/abc.py
        pattern = r'path=(\S+)'
        match = re.search(pattern, Origin_path)
        if match:
            result = match.group(1)
            user_post = result.split("/")[0]
            if user_post == username:
                access_path = './data'+result
                if os.path.exists(access_path):
                    if upload_or_del == "/upload":          # upload the document
                        Body.recv_post_file(
                            body, access_path, "uploaded_file")
                    elif upload_or_del == "/delete":        # delete the document
                        if os/path.exists(access_path):
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
        return None

    def __load_handle(self, header_pram, header_builder):
        response = 200
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
                    cookie_path = '/user_data/cookie'
                    cookie_path = cookie_path+cookie_dict['sid']
                    cookie_path
                    try:
                        with open(cookie_path, 'r') as file:
                            cookie_content = file.read()
                            cookie_dict_local = {}
                            for param in cookie_params:
                                cookie_key = param.split("=")[0].lower()
                                cookie_value = param.split("=")[1].strip()
                                cookie_dict_local[cookie_key] = cookie_value
                        ddl = cookie_dict_local.get('Expires')
                        if ddl is not None and ddl > datetime.datetime.now():
                            username = cookie_dict_local.get('username')
                            password = cookie_dict_local.get('password')
                        else:
                            test_cookie = True
                            os.remove(cookie_path)
                    except FileNotFoundError:
                        test_cookie = True
                else:
                    test_cookie = True
                if test_cookie and header_pram.authorization:
                    if header_pram.authorization.startswith("Basic "):
                        authData = header_pram.split(" ", -1)
                        username = authData.split(':')[0]
                        password = authData.split(':')[1]
                        with open('./user_data/user_info/userDatabase.txt', 'r') as file:
                            file_contents = file.read()
                            search_string = username+'/'+password+';'
                            if search_string in file_contents:
                                response = 200
                                header_builder.set_cookie = self.__set_cookie(
                                    username, password)
                            else:
                                response = 401
                    else:
                        response = 401                                        # 检查用户名和密码是否匹配
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

        cookie_path = '/user_data/cookie'
        cookie_path = cookie_path+sid
        local_info = []
        local_info.append(f'SID={sid}')
        local_info.append(f'username={username};\r\n')
        local_info.append(f'password={password};\r\n')
        # in datetime format
        local_info.append(f'Expires={clear_time};\r\n')

        with open(cookie_path, "w") as file:
            file.write(''.join(local_info))
        return ''.join(cookie_respond)
