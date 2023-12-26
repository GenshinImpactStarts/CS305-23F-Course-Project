import m_http
import argparse
import threading

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--ip', help='IP address')
    parser.add_argument('-p', '--port', type=int, help='Port number')
    args = parser.parse_args()
    addr = (args.ip, args.port)

    try:
        s = m_http.Server(addr)
        s.start()
        threading.Event().wait()
    except KeyboardInterrupt:
        s.stop()
    print(s.connection_cnt())
