import os
import json
import time
import jwt
import tornado.web
import tornado.escape

from sqlalchemy.exc import DatabaseError, IntegrityError

from common import MakeTimedUniqueId
from common.base_handler import BaseHandler
from common.email_sender import send_email_background
from common.exceptions import GeneralException
from modules.application.helper_functions import welcome_email, make_profile_data
from modules.application.models import VerificationCode, User, Role, UserSession


class VerificationHandler(BaseHandler):

    async def prepare(self):
        await super().prepare()

        self.set_header("Content-Type", "text/html;charset=utf-8")

        for key in self.request.arguments.keys():
            self.data[key] = self.get_argument(key)

        # print(self.data)

    async def get(self, *args):
        print(args)
        end_point = args[0]

        if end_point == 'confirm-email':

            self.gdb = await self.make_application_gdb()
            platform_url = os.getenv('PLATFORM_URL')

            try:
                sd = await self.confirm_email(platform_url)

                # send email: account activation
                print('email confirmed, redirecting...', sd)

                period = sd['period']
                subscription_id = sd['subscription_id']
                user_id = sd['user_id']
                token = await self.login_user(user_id)
                await self.gdb.commit()

                if subscription_id is not None:
                    self.redirect(f'{platform_url}/redirect?period={period}&subscription={subscription_id}&token={token}')
                else:
                    self.redirect(f'{platform_url}/redirect?token={token}')

            except GeneralException as err:
                await self.gdb.rollback()
                await self.show_error_page(err.code, message=err.message)

            except Exception as err:
                await self.gdb.rollback()
                await self.show_error_page(400, message='Unable to verify your email')

            finally:
                await self.gdb.close()

        else:
            await self.show_error_page(404, message='Page not found!')

    async def confirm_email(self, platform_url):

        token = self.data.get('token')

        gdb = self.gdb

        sd = await self.decode_token(token)
        vc_code = sd['session_id']
        if vc_code is None:
            raise GeneralException(401, 'Invalid verification token')

        query = gdb.query(VerificationCode).filter(
            VerificationCode.code == vc_code)
        vc = await gdb.one_or_none(query)

        if vc is not None:
            if vc.expiry_time < int(time.time()):
                raise GeneralException(401, 'Verification code expired')

            query = gdb.query(User).filter(User.user_id == vc.user_id)
            user: User = await gdb.one_or_none(query)
            user.email_verified = True

            # send welcome email
            subject, email_body = welcome_email({'name': user.name, 'base_url': f'{platform_url}/sign-in'})
            send_email_background(user.email, subject, email_body)

            # delete verification code on use
            await gdb.delete(vc)

        return sd

    async def decode_token(self, token):

        encoded_jwt = token

        try:
            token_data = jwt.decode(encoded_jwt, os.getenv('AUTH_COOKIE_SECRET'), algorithms=["HS256"])
        except:
            return None

        # print(session_data)
        if token_data is None:
            return None

        if time.time() > token_data['exp']:
            return None

        return token_data

    async def show_error_page(self, code, title='Error', message=''):
        await self.render('error.html', Code=code, Title=title, Message=message)

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

    async def login_user(self, user_id):
        query = self.gdb.query(User).filter(User.user_id == user_id)
        user: User = await self.gdb.one_or_none(query)

        user.last_login = int(time.time())
        user.last_used_ip = self.request.remote_ip

        role = await self.gdb.get(Role, user.role_id)
        profile = make_profile_data(user, role)

        sid = MakeTimedUniqueId()

        ss = UserSession()
        ss.user_id = user.user_id
        ss.session_id = sid
        ss.session_data = json.dumps(profile)
        await self.gdb.add(ss)

        sd = {
            'exp': time.time() + 86400,
            'session_id': sid,
        }

        # make jwt token
        encoded_jwt = jwt.encode(sd, os.getenv('AUTH_COOKIE_SECRET'), algorithm="HS256")

        return encoded_jwt
