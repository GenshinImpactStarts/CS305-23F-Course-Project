import os
import mimetypes
from ..status_code import StatusCode

__all__ = 'Body',


class Body:
    CHUNK_UNIT_SIZE = 0x400
    UNSAFE_CHAR = [i > 0x7f or chr(i) in
                   [' ', ':', '?', '#', '[', ']', '@', '!',
                   '$', '&', ',', '(', ')', '*', '+', ',', ';', '=', '%']
                   for i in range(0x100)]

    def get_file(path: str, chunked: bool = False) -> bytes:
        try:
            with open(path, 'rb') as f:
                result = f.read()
        except Exception:
            raise StatusCode(404)

        if chunked:
            result = Body.__get_chunked_content(result)
        return result

    # range: (start: int, end: int)
    # only check out of range
    def get_part_file(path: str, range: tuple, chunked: bool = False) -> bytes:
        start, end = Body.normailize_range(range, os.path.getsize(path))
        try:
            with open(path, 'rb') as f:
                f.seek(start)
                result = f.read(end-start+1)
        except Exception:
            raise StatusCode(404)

        if chunked:
            result = Body.__get_chunked_content(result)
        return result

    # ranges: [(start: int, end: int), (start,end), ...] start or end is None when not provided
    # only check out of range
    def get_multi_part_file(path: str, ranges: list, boundary: str, chunked: bool = False) -> bytes:
        class FileWrapper:
            def __init__(self, path):
                self.path = path

            def begin_func(self): self.f = open(self.path, 'rb')

            def get_func(self, start, end):
                self.f.seek(start)
                return self.f.read(end-start)

            def exit_func(self): self.f.close()

        f = FileWrapper(path)
        try:
            result = Body.__get_multi_parts(boundary, mimetypes.guess_type(path)[0], os.path.getsize(
                path), (f.begin_func, f.get_func, f.exit_func), ranges, chunked)
        except Exception:
            raise StatusCode(404)
        return result

    def get_folder(path: str, return_html: bool = False, chunked: bool = False) -> bytes:
        if return_html:
            html_list = []
            html_list.append(
                b'<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">')
            html_list.append(b'<html>')
            html_list.append(b'<head>')
            html_list.append(
                b'<meta http-equiv="Content-Type" content="text/html; charset=utf-8">')
            html_list.append(
                f'<title>Directory listing for {path}</title>'.encode())
            html_list.append(b'</head>')
            html_list.append(b'<body>')
            html_list.append(f'<h1>Directory listing for {path}</h1>'.encode())
            html_list.append(b'<hr>')
            html_list.append(b'<ul>')
            html_list.append(f'<li><a href="./">./</a></li>'.encode())
            html_list.append(f'<li><a href="../">../</a></li>'.encode())
            for file_name in sorted(os.listdir(path)):
                if os.path.isdir(os.path.join(path, file_name)):
                    file_name = file_name+'/'
                link_name = Body.encode_url(file_name)
                file_name = file_name.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                html_list.append(
                    f'<li><a href="{link_name}">{file_name}</a></li>'.encode())
            html_list.append(b'</ul>')
            html_list.append(b'<hr>')
            html_list.append(b'</body>')
            html_list.append(b'</html>')
            html_list.append(b'')
            result = b'\n'.join(html_list)
        else:
            result = str(['./', '../'] + sorted([name + '/' if os.path.isdir(name)
                         else name for name in os.listdir(path)])).encode()
        if chunked:
            result = Body.__get_chunked_content(result)
        return result

    # range: (start: int, end: int)
    # only check out of range
    def get_part_folder(path: str, range: tuple, return_html: bool = False, chunked: bool = False) -> bytes:
        result = Body.get_folder(path, return_html)
        start, end = Body.normailize_range(range, len(result))
        result = result[start:end+1]
        if chunked:
            result = Body.__get_chunked_content(result)
        return result

    # ranges: [(start: int, end: int), (start,end), ...] start or end is None when not provided
    # only check out of range
    def get_multi_part_folder(path: str, ranges: list, boundary: str, return_html: bool = False, chunked: bool = False) -> bytes:
        complete_html = Body.get_folder(path, return_html)
        def begin_func(): return
        def get_func(start, end): return complete_html[start, end]
        def exit_func(): return
        return Body.__get_multi_parts(boundary, 'text/html', len(complete_html), (begin_func, get_func, exit_func), ranges, chunked)

    # dispose file from GET
    # only will be used by client
    def recv_file(data: bytes, chunked: bool = False) -> bytes:
        if chunked:
            data = Body.__decode_chunked_content(data)
        return data

    # dispose file from GET
    # only will be used by client
    def recv_multi_part_file(data: bytes, boundary: str, chunked: bool = False) -> list:
        mid_boundary = f'\r\n--{boundary}\r\n'.encode()
        last_boundary = f'\r\n--{boundary}--'.encode()
        boundary_len = len(mid_boundary)
        start = end = data.find(f'--{boundary}\r\n'.encode()) - 2
        result = []
        while True:
            start = end + boundary_len
            end = data.find(mid_boundary, start)
            if end == -1:
                if chunked:
                    result.append(Body.__decode_chunked_content(
                        data[start:data.find(last_boundary, start)]))
                else:
                    result.append(data[start:data.find(last_boundary, start)])
                break
            if chunked:
                result.append(Body.__decode_chunked_content(data[start:end]))
            else:
                result.append(data[start:end])
        return result

    def recv_post_file(data: bytes, dir_path: str, file_name: str, chunked: bool = False) -> None:
        if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
            raise StatusCode(404)
        if chunked:
            data = Body.__decode_chunked_content(data)
        with open(os.path.join(dir_path, file_name), 'wb') as f:
            f.write(data)

    def recv_post_multi_part_file(data: bytes, dir_path: str, boundary: str) -> None:
        if not os.path.exists(dir_path):
            raise StatusCode(404)
        mid_boundary = f'\r\n--{boundary}\r\n'.encode()
        last_boundary = f'\r\n--{boundary}--'.encode()
        boundary_len = len(mid_boundary)
        start = end = data.find(f'--{boundary}\r\n'.encode()) - 2
        if start == -3:
            raise StatusCode(400)
        while True:
            is_file = False
            file_name = None
            chunked = False
            start = end + boundary_len
            end = data.find(b'\r\n', start)
            # check header
            while start != end:
                if end == -1:
                    raise StatusCode(400)
                header = data[start:end].decode().split(':')
                header_key = header[0].strip()
                header_value = header[1].strip()
                if header_key == 'Content-Disposition':
                    if file_name is not None:
                        raise StatusCode(400)
                    # check whether is file and find filename
                    for description in header_value.split(';'):
                        description = description.strip()
                        if len(description) > 9 and description[:8] == 'filename' and description[8] == ' ' or description[8] == '=':
                            file_name_start = description.find('\"') + 1
                            file_name_end = description.find(
                                '\"', file_name_start)
                            if file_name_start == -1 or file_name_end == -1:
                                raise StatusCode(400)
                            file_name = description[file_name_start:file_name_end]
                            break
                        if len(description) > 5 and description[:4] == 'name' and description[4] == ' ' or description[4] == '=' and description.find('\"file\"'):
                            is_file = True
                if header_key == 'Transfer-Encoding' and header_value.strip() == 'chunked':
                    chunked = True
                start = end + 2
                end = data.find(b'\r\n', start)
            # dispose data
            if is_file:
                if file_name is None:
                    raise StatusCode(400)
                start = end + 2
                end = data.find(mid_boundary, start)
                if end == -1:
                    end = data.find(last_boundary, start)
                    if end == -1:
                        raise StatusCode(400)
                    content = data[start:end]
                    if chunked:
                        content = Body.__decode_chunked_content(content)
                    try:
                        with open(os.path.join(dir_path, file_name), 'wb') as f:
                            f.write(content)
                    except Exception:
                        raise StatusCode(400)
                    break
                content = data[start:end]
                if chunked:
                    content = Body.__decode_chunked_content(content)
                try:
                    with open(os.path.join(dir_path, file_name), 'wb') as f:
                        f.write(content)
                except Exception:
                    raise StatusCode(400)

    def normailize_range(range: tuple, total_len: int) -> tuple:
        start, end = range
        if end == None:
            if start < 0:
                start = total_len + start
                end = total_len - 1
            else:
                end = total_len - 1
        if start < 0 or end < 0 or start >= total_len or end >= total_len or start > end:
            raise StatusCode(416)
        return (start, end)

    def encode_url(url: str) -> str:
        input_bytes = url.encode()
        output_bytes = bytearray(len(input_bytes)*3)
        idx = 0
        for i in input_bytes:
            if Body.UNSAFE_CHAR[i]:
                tmp = hex(i)[2:].upper()
                output_bytes[idx] = 37  # ord('%') = 37
                output_bytes[idx+1] = ord(tmp[0])
                output_bytes[idx+2] = ord(tmp[1])
                idx += 3
            else:
                output_bytes[idx] = i
                idx += 1
        return output_bytes[:idx].decode()

    def decode_url(url: str) -> str:
        input_bytes = url.encode()
        output_bytes = bytearray(len(input_bytes))
        input_idx = 0
        output_idx = 0
        input_end = len(input_bytes)
        while input_idx < input_end:
            if input_bytes[input_idx] == 37:
                output_bytes[output_idx] = int(
                    input_bytes[input_idx+1:input_idx+3], 16)
                input_idx += 3
                output_idx += 1
            else:
                output_bytes[output_idx] = input_bytes[input_idx]
                input_idx += 1
                output_idx += 1
        return output_bytes[:output_idx].decode()

    def __get_chunked_content(content: bytes) -> bytes:
        idx = 0
        total_len = len(content)
        chunk_list = []
        while total_len - idx > Body.CHUNK_UNIT_SIZE:
            chunk_list.append(hex(Body.CHUNK_UNIT_SIZE).encode())
            chunk_list.append(content[idx:idx+Body.CHUNK_UNIT_SIZE])
            idx += Body.CHUNK_UNIT_SIZE
        chunk_list.append(hex(total_len-idx).encode())
        chunk_list.append(content[idx:])
        chunk_list.append(b'0')
        chunk_list.append(b'\r\n')
        return b'\r\n'.join(chunk_list)

    # func: (begin_func, get_func, exit_func)
    def __get_multi_parts(boundary: str, content_type: str, total_len: int, func: list, ranges: list, chunked: bool) -> bytes:
        # prepare for each parts' header
        boundary_bytes = f'--{boundary}'.encode()
        content_type_bytes = f'Content-Type: {content_type}'.encode()
        # get each parts of file
        parts = []
        func[0]()
        for range in ranges:
            start, end = Body.normailize_range(range, total_len)
            parts.append((func[1](start, end+1), start, end))
        func[2]()
        # generate the body
        body_list = []
        for part, start, end in parts:
            body_list.append(boundary_bytes)
            body_list.append(content_type_bytes)
            if chunked:
                body_list.append(b'Transfer-Encoding: chunked')
                body_list.append(b'')
                body_list.append(Body.__get_chunked_content(part))
            else:
                body_list.append(
                    f'Content-Range: bytes {start}-{end}/{total_len}'.encode())
                body_list.append(b'')
                body_list.append(part)
        body_list.append(f'--{boundary}--'.encode())
        return b'\r\n'.join(body_list)

    def __decode_chunked_content(data: bytes) -> bytes:
        try:
            now_start = 0
            now_end = data.find(b'\r\n')
            chunk_len = int(data[now_start:now_end].decode(), 16)
            result_list = []
            while chunk_len != 0:
                now_start = now_end + 2
                now_end = now_start + chunk_len
                result_list.append(data[now_start:now_end])
                if data[now_end:now_end+2] != b'\r\n':
                    raise Exception()
                now_start = now_end + 2
                now_end = data.find(b'\r\n', now_start)
                chunk_len = int(data[now_start:now_end].decode(), 16)
            result = b''.join(result_list)
        except Exception:
            raise StatusCode(400)
        return result
