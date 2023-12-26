import m_http
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--ip', help='IP address')
    parser.add_argument('-p', '--port', type=int, help='Port number')
    args = parser.parse_args()
    addr = (args.ip, args.port)

    s = m_http.Server(addr)
    s.start()
    q = input('Enter (q) to quit:')
    while q != 'q' and q != 'Q':
        q = input('Enter (q) to quit:')
    s.stop()
    print(s.connection_cnt())
