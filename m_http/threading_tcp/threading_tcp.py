import socket
from threading import Thread, Lock, current_thread
from .list_maintainer import ListMaintainer

__all__ = 'ThreadingTCP'


class ThreadingTCP:
    def __init__(self, addr: tuple):
        self.addr = addr

        self.__running = False
        self.__conns = set()
        self.__threads = set()
        self.__running_lock = Lock()
        self.__list_maintainer = ListMaintainer((self.__threads, self.__conns), self.__running_lock)

        self.__listen_thread = None
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__sock.bind(addr)

        self.print_lock = Lock()

    # need be override
    def handle(self, conn: socket.socket, addr: tuple):
        pass

    def start(self):
        # function to be run in the listen thread
        def listen():
            try:
                while True:
                    conn, addr = self.__sock.accept()
                    if not self.__running:
                        break
                    with self.__running_lock:
                        if not self.__running:
                            break
                        thread = Thread(
                            target=self.__handle, args=(conn, addr))
                        thread.start()
                        self.__conns.add(conn)
                        self.__threads.add(thread)
                        self.print(
                            f'receive new request from {addr}. now connections: {self.connection_cnt()}')
            except Exception as e:
                # TODO
                self.__running = False
            self.print('listen thread exit')

        # start listen socket and thread
        try:
            self.__sock.listen()
            self.__running = True
            self.__listen_thread = Thread(target=listen)
            self.__listen_thread.start()
            self.print(f"Server listening on http://{self.addr}/")
        except Exception as e:
            self.print(f'Fail to start server')
            self.stop()
            raise e
        # start list_maintainer
        self.__list_maintainer.start()

    def stop(self):
        # stop listen sock and thread
        with self.__running_lock:
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
        # stop list_maintainer
        self.__list_maintainer.stop()

    def connection_cnt(self) -> int:
        return len(self.__conns)

    # print with lock
    def print(self, *values: object, sep: str = " ", end: str = "\n", file: str = None, flush: bool = False) -> None:
        with self.print_lock:
            print(*values, sep=sep, end=end, file=file, flush=flush)

    def __handle(self, conn: socket.socket, addr: tuple):
        try:
            self.handle(conn, addr)
        finally:
            try:
                conn.close()
            except Exception:
                pass
            self.__list_maintainer.remove((current_thread(), conn))
            self.print(
                f'close request from {addr}. connections will be: {self.connection_cnt()-1}')
