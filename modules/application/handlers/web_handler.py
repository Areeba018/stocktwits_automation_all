import os
import time
import jwt
import asyncio
import tornado.web
import tornado.escape
import traceback

from sqlalchemy.exc import DatabaseError, IntegrityError

from common.base_handler import BaseHandler
from modules.application.helper_functions import fetch_session


class WebHandler(BaseHandler):

    async def prepare(self):
        await super().prepare()

        self.set_header("Content-Type", "text/html;charset=utf-8")

        for key in self.request.arguments.keys():
            self.data[key] = self.get_argument(key)

        # print(self.data)

    async def get(self, *args):
        # print(args)

        self.set_status(200)
        self.write('Ok')
        await self.finish()

    def write_error(self, status_code, **kwargs):

        log_message = 'unknown error'
        if 'exc_info' in kwargs:
            err = kwargs['exc_info'][1]
            if isinstance(err, tornado.web.HTTPError):
                log_message = err.log_message
            elif isinstance(err, DatabaseError):
                log_message = err.args[0]
            elif isinstance(err, IntegrityError):
                log_message = err.args[0]
            elif isinstance(err, AttributeError):
                log_message = err.args[0]
            elif isinstance(err, KeyError):
                log_message = err.args[0]

        self.render('error.html', Code=status_code, Title='Error', Message=log_message)
