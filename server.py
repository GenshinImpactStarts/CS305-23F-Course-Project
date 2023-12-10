from m_http import server
from time import sleep

if __name__ == '__main__':
    s = server.Server(('127.0.0.1', 65432))
    s.start_server()
    sleep(5)
    print(len(s._Server__conns))
    print(len(s._Server__threads))
    s.stop_server()
    print(len(s._Server__conns))
    print(len(s._Server__threads))
