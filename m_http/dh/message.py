__all__ = 'RequestType', 'RespondType'


class RequestType:
    ask_request = b'ask'
    connect_request = b'connect'
    request_list = [ask_request, connect_request]


class RespondType:
    ok = b'ok'
    err = b'err'
    respond_list = [ok, err]
