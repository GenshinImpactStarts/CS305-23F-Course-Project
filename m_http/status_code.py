__all__ = 'StatusCode',


class StatusCode(Exception):
    __code = {2: 'Success',
             3: 'Redirection',
             4: 'Client Error',
             5: 'Server Error',
             200: 'OK',
             206: 'Partial Content',
             301: 'Redirect',
             400: 'Bad Request',
             401: 'Unauthorized',
             403: 'Forbidden',
             404: 'Not Found',
             405: 'Method Not Allowed',
             416: 'Range Not Satisfiable',
             502: 'Bad Gateway',
             503: 'Service Temporarily Unavailable'}
    
    def __init__(self, code: int):
        self.code = code

    def get_description(code: int) -> str:
        return StatusCode.__code[code]

    def simplify(code: int) -> int:
        return code//100
