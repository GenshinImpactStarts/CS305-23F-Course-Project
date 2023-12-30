from m_http.dh.server import Server
from m_http.dh.client import Client
import base64

USER_NAME = 'client1'
USER_PWD = '123'


def input_with_quit(text: str) -> str:
    line = input(text)
    if line == 'q' or line == 'Q':
        raise Exception()
    return line


if __name__ == "__main__":
    server = Server(("127.0.0.1", 8000), 9999)
    server.start()
    client = Client("127.0.0.1", 8000)
    client.connect()
    try:
        while True:
            method = input_with_quit('method(GET, POST):').upper()
            url = input_with_quit('url:')
            body = None
            headers = None
            if input_with_quit('with authorization:') in ['y', 'Y']:
                headers = {'Authorization': 'Basic ' +
                            base64.b64encode(f'{USER_NAME}:{USER_PWD}'.encode()).decode()}
            file_path = None
            is_chunk = False
            client.send(method, url, body, headers, file_path, is_chunk)
    finally:
        server.stop()
