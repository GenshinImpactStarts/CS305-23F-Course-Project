import socket
from threading import Thread, Condition, Lock, current_thread
from .status_code import StatusCode

__all__ = 'Server',


class Server:
    def __init__(self, addr: tuple):
        self.addr = addr

        self.__running = False
        self.__conns = set()
        self.__threads = set()
        self.__list_maintainer = self.ListMaintainer(
            self.__threads, self.__conns)

        self.__listen_thread = None
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__sock.bind(addr)

        self.__print_lock = Lock()

    def start_server(self):
        # function to be run in the listen thread
        def listen(self: Server):
            while self.__running:
                try:
                    conn, addr = self.__sock.accept()
                    thread = Thread(
                        target=self.__request_handle, args=(conn, addr))
                    thread.start()
                    self.__conns.add(conn)
                    self.__threads.add(thread)
                    self.__print(f'receive new request from {addr}')
                except Exception:
                    # TODO
                    self.__running = False
            self.__print('listen thread exit')

        # start listen socket and thread
        try:
            self.__sock.listen()
            self.__running = True
            self.__listen_thread = Thread(target=listen, args=(self,))
            self.__listen_thread.start()
            self.__print(f"Server listening on http://{self.addr}/")
        except Exception as e:
            self.__print(f'Fail to start server')
            self.stop_server()
            raise e

    def stop_server(self):
        # stop listen sock and thread
        try:
            self.__sock.close()
        except Exception:
            pass
        try:
            self.__listen_thread.join()
            self.__listen_thread = None
        except Exception:
            pass
        # stop request-handling sock and thread
        for conn in self.__conns:
            try:
                conn.close()
            except Exception:
                pass
        for thread in self.__threads:
            try:
                thread.join()
            except Exception:
                pass
        # recover variable
        self.__conns = set()
        self.__threads = set()
        self.__running = False

    # print with lock
    def __print(self, *values: object, sep: str = " ", end: str = "\n", file: str = None, flush: bool = False) -> None:
        with self.__print_lock:
            print(*values, sep=sep, end=end, file=file, flush=flush)

    def __request_handle(self, conn: socket.socket, addr: tuple):
        self.__request_close(conn, addr)
        return
        with conn:
            while True:
                request = conn.recv(1024).decode('utf-8')
                lines = request.split('\n')
                request_line = lines[0].strip().split()
                method = request_line[0]
                url = request_line[1]
                http_version = request_line[2]
                messageHeader = {}
                for line in lines:
                    parts = line.split(':')
                    if parts.length > 2:
                        messageHeader[parts[0]] = parts[1]

                authHeader = messageHeader.get('Authorization', None)  # 检查授权
                if authHeader:
                    decodedAuth = authHeader.decode('utf-8')
                    username = decodedAuth.split(':')[0]
                    password = decodedAuth.split(':')[1]
                    pass                                        # 检查用户名和密码是否匹配
                else:
                    response = self.respond_header_builder(http_version, "401")
                    # conn.sendall(response.encode('utf-8'))

                if method == "GET":
                    filePath = url  # 还没处理呢
                    try:
                        with io.open(filePath, 'r', encoding='utf-8') as file:
                            data = file.read
                    except FileNotFoundError:
                        response = self.respond_header_builder(
                            http_version, "404")
                        # conn.sendall(response.encode('utf-8'))
                elif method == "POST":
                    pass
                elif method == "HEAD":
                    pass
                else:
                    pass

                if messageHeader['Connection'] == 'close':
                    conn.close()
                    break

    def __respond_header_builder(self, version, code) -> str:
        statusLine = f"{version} {code} {StatusCode.get_description(code)}\r\n"
        contentType = "Content-Type: text/html; charset=utf-8"
        return statusLine

    class ListMaintainer:
        def __init__(self, threads: set, conns: set):
            self.__tasks = []
            self.__running = True
            self.__threads = threads
            self.__conns = conns
            self.__maintainer_cv = Condition()
            self.__maintainer_thread = Thread(target=self.__start)
            self.__maintainer_thread.start()

        # should be called just before the thread exit to avoid long blocking time when join the thread
        def remove(self, thread: Thread, conn: socket.socket):
            with self.__maintainer_cv:
                self.__tasks.append((thread, conn))
                self.__maintainer_cv.notify()

        def join(self):
            self.__running = False
            with self.__maintainer_cv:
                self.__maintainer_cv.notify()
            self.__maintainer_thread.join()

        def __start(self):
            while True:
                # block when have no task
                with self.__maintainer_cv:
                    if len(self.__tasks) == 0:
                        self.__maintainer_cv.wait()
                        # if notifed by join()
                        if not self.__running:
                            return
                thread, conn = self.__tasks.pop()
                self.__threads.remove(thread)
                self.__conns.remove(conn)
                thread.join()

    # should be called just before the thread exit to avoid long blocking time of ListMaintainer
    def __request_close(self, conn: socket.socket, addr: tuple):
        try:
            conn.close()
        except Exception:
            pass
        self.__print(f'close request from {addr}')
        self.__list_maintainer.remove(current_thread(), conn)
