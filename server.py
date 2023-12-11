from m_http import server
from time import sleep

if __name__ == '__main__':
    s = server.Server(('127.0.0.1', 65432))
    s.start()
    sleep(5)
    print(s.connection_cnt())
    s.stop()
    print(s.connection_cnt())
