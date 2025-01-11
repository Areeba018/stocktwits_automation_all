
from tornado.web import HTTPError


class GeneralException(HTTPError):

    def __init__(self, code=400, message=''):
        self.code = code
        self.message = message
        super().__init__(code, message)
