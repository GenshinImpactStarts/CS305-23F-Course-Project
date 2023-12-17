import io
import os
import time
import socket
from .status_code import StatusCode
from .threading_tcp import ThreadingTCP
import html.header
from  html.body import Body

__all__ = 'Server',


class Server(ThreadingTCP):
    def GetMethod(self,header_pram,path,username,password) :  #return the status_code and response_data
        access_path =path.split("?")[0]
        SusTech_code =path.split("?")[1]
        filePath = "/data/"+path                        # 还没处理
        if  ".." in filePath:                              #prevent attack
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
            #etag =???????????????????????????????????????????????????; how to generate etag 
            #if header_pram.if_none_match == etag:
            #    return 304
            
            if os.path.isdir(filePath):
                if "SUSTech-HTTP=1" in SusTech_code:
                    response_data = Body.get_folder(filePath, return_html=True)
                else:
                    response_data = Body.get_folder(filePath, return_html=False)
            elif os.path.isfile(filePath):
                file_content = Body.get_file(filePath)
                response_data = file_content

            return 200,response_data
        else :
            return 404

    def PostMethod(self,header_pram,path,username,password):
        upload_or_del =path.split("?")[0]
        Origin_path =path.split("?")[1].strip();            #ex:path=/11912113/abc.py
        if ("path=/" in Origin_path):
            user_post = Origin_path.split("/")[1]
            if user_post==username :
                index= Origin_path.index("path=") + len("path=")
                access_path = path[index:-1]
                if os.path.exists(access_path):  
                    if upload_or_del =="/upload":                   #upload the document
                            Body.recv_post_file(request_data, access_path, "uploaded_file")
                    elif upload_or_del=="/delete":                  #delete the document
                        if os/path.exists(access_path):
                            try:
                                os.remove(access_path)
                            except Exception as e:
                                response = 500
                else :
                    response= 404   
            else :
                response =403
        else:
            response = 400
    
    def handle(self, conn: socket.socket, addr: tuple,):
        with conn:
            while True:
                request = conn.recv(1024).decode('utf-8')
                method, path, version =html.header.Header.parse_request_line(request)
                header_pram , body=html.header.Header.parse_request_headers(request)
                if (method ==" HEAD"):
                    response =200
                
                if header_pram.authorization:
                    if header_pram.authorization.startswith("Basic "):
                        authData=header_pram.split(" ",-1)
                        username = authData.split(':')[0]
                        password = authData.split(':')[1]
                    pass                                        # 检查用户名和密码是否匹配
                else:
                    pass
                    response = 401
                
                if method == "GET":
                    response , response_data =self.GetMethod(self,header_pram,path,username,password)

                elif method == "POST":
                    response , response_data =self.PostMethod(self,header_pram,path,username,password)
                else:
                    pass
                if header_pram.connection == 'close':
                    conn.close()
                    break

