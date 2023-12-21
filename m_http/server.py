import io
import os
import random
import string
import time
import socket
from .status_code import StatusCode
from .threading_tcp import ThreadingTCP
from http_content import header
from http_content.body import Body
import datetime
__all__ = 'Server',


class Server(ThreadingTCP):
    def handle(self, conn: socket.socket, addr: tuple):
        with conn:
            while self.handle_request(conn.recv(2048).decode('utf-8')) is not None:
                pass
            conn.close()

    # return None when need to close the connection
    def handle_request(self, request: str) -> str:
        method, path, version = header.Header.parse_request_line(request)
        header_pram, body = header.Header.parse_request_headers(request)
        if (method == " HEAD"):
            response = 200
        if header_pram.authorization or header_pram.cookie:
            test_cookie=False
            
            if header_pram.cookie:
                cookie_params = header_pram.cookie.split("; ")
                cookie_dict={}
                for param in cookie_params:
                    cookie_key = param.split("=")[0].lower()
                    cookie_value = param.split("=")[1].strip()
                    cookie_dict[cookie_key] = cookie_value
                if 'sid' in cookie_dict:
                    cookie_path='/cookieDatabase/'
                    cookie_path=cookie_path+cookie_dict['sid']
                    cookie_path
                    try:
                        with open(cookie_path,'r') as file:
                            cookie_content=file.read()
                            cookie_dict_local={}
                            for param in cookie_params:
                                cookie_key = param.split("=")[0].lower()
                                cookie_value = param.split("=")[1].strip()
                                cookie_dict_local[cookie_key] = cookie_value
                        ddl=cookie_dict_local.get('Expires')
                        if ddl is not None and ddl>datetime.datetime.now():
                            username=cookie_dict_local.get('username')
                            password=cookie_dict_local.get('password')
                        else:
                            test_cookie=True
                            os.remove(cookie_path)
                    except FileNotFoundError:
                        test_cookie=True
                else:
                    test_cookie=True
            
            if test_cookie and header_pram.authorization:
                if header_pram.authorization.startswith("Basic "):
                    authData = header_pram.split(" ", -1)
                    username = authData.split(':')[0]
                    password = authData.split(':')[1]
                pass                                        # 检查用户名和密码是否匹配
                    
            
        else:
            pass
            response = 401
        if method == "GET":
            response, response_data = self.__get_method(
                self, header_pram, path, username, password)

        elif method == "POST":
            response, response_data = self.__post_method(
                self, header_pram, path, username, password)
        else:
            pass
        if header_pram.connection == 'close':
            pass

    # return the status_code and response_data
    def __get_method(self, header_pram, path, username, password):
        access_path = path.split("?")[0]
        SusTech_code = path.split("?")[1]
        filePath = "/data/"+path                                # 还没处理
        if ".." in filePath:  # prevent attack
            return 403
        elif os.path.exists(filePath):
            last_modified_time = time.gmtime(os.path.getmtime(path))
            try:
                client_request_time = time.mktime(
                    time.strptime(header_pram.if_modified_since, "%a, %d %b %Y %H:%M:%S GMT"))
            except ValueError:
                pass
            if client_request_time >= last_modified_time:
                return 304
            # etag =???????????????????????????????????????????????????; how to generate etag
            # if header_pram.if_none_match == etag:
            #    return 304

            if os.path.isdir(filePath):
                if "SUSTech-HTTP=1" in SusTech_code:
                    response_data = Body.get_folder(filePath, return_html=True)
                else:
                    response_data = Body.get_folder(
                        filePath, return_html=False)
            elif os.path.isfile(filePath):
                file_content = Body.get_file(filePath)
                response_data = file_content

            return 200, response_data
        else:
            return 404

    def __post_method(self, header_pram, path, username, password):
        upload_or_del = path.split("?")[0]
        Origin_path = path.split("?")[1].strip()  # ex:path=/11912113/abc.py
        if ("path=/" in Origin_path):
            user_post = Origin_path.split("/")[1]
            if user_post == username:
                index = Origin_path.index("path=") + len("path=")
                access_path = path[index:-1]

                if os.path.exists(access_path):
                    if upload_or_del == "/upload":  # upload the document
                        Body.recv_post_file(
                            request_data, access_path, "uploaded_file")
                    elif upload_or_del == "/delete":  # delete the document
                        if os/path.exists(access_path):
                            try:
                                os.remove(access_path)
                            except Exception as e:
                                response = 500
                else:
                    response = 404
            else:
                response = 403
        else:
            response = 400
    
    def set_cookie(username,password,length=32,ttl_in_day=3):
        cookie_respond=[]
        characters = string.ascii_letters + string.digits
        sid = ''.join(random.choice(characters) for _ in range(length))
        cookie_respond.append(f'SID={sid};')
        clear_time = datetime.datetime.now()
        ttl= datetime.timedelta(days=ttl_in_day)
        clear_time=clear_time+ttl
        cookie_expires_str = clear_time.strftime("%a, %d %b %Y %H:%M:%S GMT")
        cookie_respond.append(f'Expires={cookie_expires_str};')
        cookie_respond.append(f'Path=\\;Secure;HttpOnly')
        
        cookie_path='/cookieDatabase/'
        cookie_path=cookie_path+sid
        local_info=[]
        local_info.append(f'SID={sid}')
        local_info.append(f'username={username};\r\n')
        local_info.append(f'password={password};\r\n')
        local_info.append(f'Expires={clear_time};\r\n')         # in datetime format
        
        with open(cookie_path, "w") as file:
            file.write(''.join(local_info))
        return ''.join(cookie_respond)