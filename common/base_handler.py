import asyncio
import json
import os
import time
import jwt
import traceback

import tornado.web
import tornado.escape

from sqlalchemy.exc import DatabaseError, IntegrityError

from common import MakeTimedUniqueId
from common.exceptions import GeneralException
from common.database_v2 import make_connection
from common.gdb_helper_v2 import GDBHelper


class BaseHandler(tornado.web.RequestHandler):

    def set_default_headers(self):
        # print("setting headers!!!")
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, PUT, DELETE, OPTIONS')
        self.set_header("Access-Control-Allow-Headers", "accept,access-control-allow-origin,authorization,content-type")

    def options(self, *args):
        # no body
        # `*args` is for route with `path arguments` supports
        self.set_status(204)
        self.finish()

    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)

        self.cookie_name = self.application.cookie_name
        self.base_url = self.application.base_url
        self.files_dir = self.application.files_dir

        self.gdb = None
        self.files = []
        self.data = {}
        self.session = None
        self.log_id = None

        # API Logging
        self.start_time = time.time()
        # self.response_body = None
        self.error_message = []
        self.error_description = []
        self.error_traceback = []
        self.response_status = None

    def initialize(self):
        pass

    async def prepare(self):
        await self.decode_body()
        # await asyncio.sleep(2)

    async def decode_body(self):

        if hasattr(self.request, 'files') and len(self.request.files) > 0:
            self.files = self.request.files

        if len(self.request.arguments.keys()) > 0:
            for key in self.request.arguments.keys():
                self.data[key] = self.get_argument(key)

        try:
            if hasattr(self.request, 'body') and (len(self.request.body) > 0):
                body_data = tornado.escape.json_decode(self.request.body)
                for key in body_data:
                    self.data[key] = body_data[key]
        except Exception:
            # traceback.print_exc()
            print('unable to decode body ...')
            # raise GeneralException(code=400, message='invalid request params / body')

    async def decode_session(self, _raise=True):

        # encoded_jwt = self.get_secure_cookie(self.cookie_name)
        auth_header = self.request.headers.get('Authorization')
        chunks = auth_header.split(' ') if auth_header is not None else []
        if len(chunks) != 2:
            if _raise:
                raise GeneralException(401, 'Unauthorized')
            else:
                return None

        encoded_jwt = chunks[1]

        try:
            session_data = jwt.decode(encoded_jwt, os.getenv('AUTH_COOKIE_SECRET'), algorithms=["HS256"])
        except:
            if _raise:
                raise GeneralException(401, 'Unauthorized')
            else:
                return None

        # print(session_data)
        if session_data is None:
            if _raise:
                raise GeneralException(401, 'Unauthorized')
            else:
                return None

        if time.time() > session_data['exp']:
            if _raise:
                raise GeneralException(401, 'Session Expired')
            else:
                return None

        return session_data['session_id']

    async def make_application_gdb(self):
        session = make_connection(self.application.engine)
        gdb = GDBHelper(session)
        return gdb

    async def get(self, *args, **kwargs):
        try:
            await self.get_api(*args, **kwargs)
        except Exception as err:
            await self.handle_error(err)

    async def post(self, *args, **kwargs):
        try:
            await self.post_api(*args, **kwargs)
        except Exception as err:
            await self.handle_error(err)

    # async def patch(self, *args, **kwargs):
    #     try:
    #         await self.patch_api(*args, **kwargs)
    #     except Exception as err:
    #         await self.handle_error(err)

    async def put(self, *args, **kwargs):
        try:
            await self.patch_api(*args, **kwargs)
        except Exception as err:
            await self.handle_error(err)

    async def delete(self, *args, **kwargs):
        try:
            await self.delete_api(*args, **kwargs)
        except Exception as err:
            await self.handle_error(err)

    async def get_api(self, *args, **kwargs):
        pass

    async def post_api(self, *args, **kwargs):
        pass

    async def patch_api(self, *args, **kwargs):
        pass

    async def delete_api(self, *args, **kwargs):
        pass

    def on_finish(self):
        return

    async def data_received(self, chunk: bytes):
        pass

    async def send_response(self, data=None):

        if self.gdb is not None:
            await self.gdb.commit()
            await self.gdb.close()

        self.set_header("Content-Type", "application/json")
        self.set_status(200)
        if data is None:
            data = {}

        # self.response_body = json.dumps(data)
        self.response_status = 'Success'
        self.write(data)

        try:
            await self.finish()
        except Exception:
            print('client has closed connection after request: {}'.format(self.request.uri))

    async def send_response_v2(self, message, data=None):

        if self.gdb is not None:
            await self.gdb.commit()
            await self.gdb.close()

        self.set_header("Content-Type", "application/json")
        self.set_status(200)
        if data is None:
            data = {}

        data['success'] = True
        data['message'] = message

        self.write(data)

        # self.response_body = json.dumps(data)
        self.response_status = 'Success'

        try:
            await self.finish()
        except Exception:
            print('client has closed connection after request: {}'.format(self.request.uri))

    async def handle_error(self, err: Exception):
        err_code = 400
        log_message = 'Unknown error occurred, Please contact support'

        if self.gdb is not None:
            await self.gdb.rollback()
            await self.gdb.close()

        if isinstance(err, tornado.web.HTTPError):
            err_code = err.status_code
            log_message = err.log_message
        if isinstance(err, GeneralException):
            err_code = err.status_code
            log_message = err.message
        elif isinstance(err, DatabaseError):
            err_code = 500
            err_message = err.args[0]
            log_message = err_message
        elif isinstance(err, IntegrityError):
            err_code, err_message = err.args[0].split(':')
            log_message = err_message
        elif isinstance(err, AttributeError):
            log_message = err.args[0]
        elif isinstance(err, KeyError):
            log_message = f'required key: {err.args[0]} missing'
        elif isinstance(err, ValueError):
            log_message = f'Error: {err.args[0]}'

        elif isinstance(err, Exception):
            log_message = f'Error: {err.args[0]}'

        if 'Unknown database' in log_message:
            self.clear_cookie(self.cookie_name)
            # self.redirect('/')

        print('handle write_error --> ', err_code, log_message)
        print(traceback.print_exc())

        resp = {
            'message': log_message,
            'error': {
                'message': log_message,
            }
        }

        self.set_status(err_code)
        self.write(resp)

        self.response_status = 'Error'
        # self.response_body = json.dumps(resp)
        self.error_message.append(log_message)
        self.error_description.append(f'{err}')
        self.error_traceback.append(traceback.format_exc())

        await self.finish()
        # except KeyError as err:
        #     log_message = f'required key: {err.args[0]} missing'
        # except AttributeError as err:
        #     log_message = err.args[0]
        # except IntegrityError as err:
        #     err_code, err_message = err.args[0].split(':')
        #     log_message = err_message
        # except DatabaseError as err:
        #     err_code = 500
        #     err_message = err.args[0]
        #     log_message = err_message
        # except GeneralException as err:
        #     log_message = err.message
        # except tornado.web.HTTPError as err:
        #     log_message = err.log_message

    def write_error(self, status_code, **kwargs):

        # self.gdb.close()  todo: need to close db connection

        log_message = 'unknown error'
        err = None
        if 'exc_info' in kwargs:
            err = kwargs['exc_info'][1]
            if isinstance(err, tornado.web.HTTPError):
                log_message = err.log_message
            if isinstance(err, GeneralException):
                log_message = err.message
            elif isinstance(err, DatabaseError):
                err_code = 500
                err_message = err.args[0]
                log_message = err_message
            elif isinstance(err, IntegrityError):
                err_code, err_message = err.args[0].split(':')
                log_message = err_message
            elif isinstance(err, AttributeError):
                log_message = err.args[0]
            elif isinstance(err, KeyError):
                log_message = f'required key: {err.args[0]} missing'

        if 'Unknown database' in log_message:
            self.clear_cookie(self.cookie_name)
            # self.redirect('/')

        print('write_error --> ', status_code, log_message)

        resp = {
            'message': log_message
        }

        self.response_status = 'Error'
        # self.response_body = json.dumps(resp)
        self.error_message.append(log_message)
        self.error_description.append(err)
        self.error_traceback.append(traceback.format_exc())

        self.set_status(status_code)
        self.write(resp)
        self.finish()

    # async def log_api(self):
    #     if not self.log_enabled:
    #         return
    #
    #     log_db = None
    #     try:
    #         session = make_connection(log_db=True)
    #         log_db = GDBHelper(session)
    #
    #         if self.log_id is None:
    #             api_log_id = MakeTimedUniqueId()
    #             insert = {
    #                 'api_log_id': api_log_id,
    #                 'ip_address': self.request.remote_ip,
    #                 'user_agent': self.request.headers.get('User-Agent'),
    #                 'request_uri': self.request.uri.split('?')[0],
    #                 'request_method': self.request.method,
    #                 'request_headers': str(self.request.headers),
    #                 'request_body': json.dumps(self.data),
    #             }
    #             await log_db.create(APILog, insert)
    #             self.log_id = api_log_id
    #         else:
    #             update = {
    #                 'response_status': self.response_status,
    #                 'response_status_code': self.get_status(),
    #                 # 'response_body': self.response_body,
    #                 'error_message': json.dumps(self.error_message) if len(self.error_message) > 0 else None,
    #                 'error_description': json.dumps(self.error_description) if len(self.error_description) > 0 else None,
    #                 'error_traceback': json.dumps(self.error_traceback) if len(self.error_traceback) > 0 else None,
    #                 'execution_time': round(time.time() - self.start_time, 5),
    #                 'user_id': self.session['data']['id'] if self.session is not None else None,
    #                 'user_name': self.session['data']['displayName'] if self.session is not None else 'Public API',
    #             }
    #             await log_db.update(APILog, APILog.api_log_id == self.log_id, update)
    #
    #         await log_db.commit()
    #         await log_db.close()
    #     except Exception as e:
    #         print('Error Logging API Request')
    #         print(f'{e}')
    #         if log_db is not None:
    #             await log_db.rollback()
    #             await log_db.close()
