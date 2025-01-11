import asyncio
import os
import time
import json
import jwt
import hashlib
import aiohttp


from sqlalchemy import func
# from google.oauth2 import id_token
# from google.auth.transport import requests

from common.email_sender import send_email_background
from common.exceptions import GeneralException
from common.helpers import make_string, make_uuid4
from common.base_handler import BaseHandler
from modules.application.helper_functions import make_profile_data, confirmation_email, reset_link_email, \
    reset_successful_email
from modules.application.models import User, UserSession, VerificationCode, Role, Settings

from common import MakeTimedUniqueId
# from common.stripe_helper import create_stripe_customer

# if os.path.isfile('credentials.json') is False:
#     sys.exit('credentials.json not found.')

# credentials = json.loads(open('credentials.json', 'r').read())
# ClientID = credentials['web']['client_id']
ClientID = ''


class AuthHandler(BaseHandler):

    async def prepare(self):
        await super().prepare()
        self.set_header("Content-Type", "application/json")
        # await self.decode_body()
        self.gdb = await self.make_application_gdb()

    async def get_api(self, *args, **kwargs):

        if len(args) == 0:
            raise GeneralException(code=404)

        resp = None
        endpoint = args[0].lower()
        if endpoint == 'logout':
            await self.logout()
        elif endpoint == 'whop-callback':
            resp = await self.whop_callback()
        else:
            raise GeneralException(code=404)
        
        await self.send_response(data=resp)

    async def post_api(self, *args, **kwargs):

        if len(args) == 0:
            raise GeneralException(code=404)

        endpoint = args[0]

        if endpoint == 'sign-in-with-google':
            await self.login_with_google()
        elif endpoint == 'sign-up':
            await self.signup()
        elif endpoint == 'validate':
            await self.validate()
        elif endpoint == 'login':
            await self.login()
        elif endpoint == 'loginWithToken':
            await self.login_with_token()
        elif endpoint == 'loginWithProvidedToken':
            await self.login_with_provided_token()
        elif endpoint == 'forgotPassword':
            await self.forgot_password()
        elif endpoint == 'resetPassword':
            await self.reset_password()
        else:
            raise GeneralException(code=404)

    async def call_api(self, method, url, access_token=None, params=None, data=None):
        
        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        session = aiohttp.ClientSession()
        
        res = None
        response = None
        if method == 'GET':
            response = await session.get(url, headers=headers, params=params)
            res = await response.text()
        elif method == 'POST':
            response = await session.post(url, headers=headers, data=data)
            res = await response.json()
            
        await session.close()      
        return res

    async def whop_callback(self):
        code = self.data.get('code')
        
        print('code:', code)
        
        # dev_api_key = 'VYP-H5zkbzL9dntKtF6GZGUIZgA6oke4cz-o5rcwZUU'
        client_id = 'y1k9xxVrXO0qYpXc0uCyx02SSUYLPz_9gC7TasIZDdU'
        client_secret = 'GeVuUFDR4La_ARH9qo4psq4iDPfd4ubUDBSNDnKX_GM'

        data = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": 'http://localhost:8091/api/auth/whop-callback',
        }
        
        token_url = 'https://api.whop.com/v5/oauth/token'
        res = await self.call_api('POST', token_url, data=data)
        access_token = res.get('access_token')
        print('access_token:', access_token)

        profile_url = 'https://api.whop.com/v5/me'
        res = await self.call_api('GET', profile_url, access_token)

        # print('redirecting...')
        # self.redirect('http://localhost:4000')

        return res
    
    async def logout(self):
        self.clear_cookie(self.cookie_name)
        self.redirect('/')
        return

    async def signup(self):

        name = self.data['displayName']
        email = self.data['email']
        password = self.data['password']
        subscription_id = self.data.get('subscription')
        period = self.data.get('period')

        query = self.gdb.query(User).filter(User.email == email)
        user = await self.gdb.one_or_none(query)
        if user is not None:
            return await self.send_response_v2('Email is already used', {
                'error': [{
                    'type': 'email', 'message': 'The email address is already in use'
                }]
            })

        # stripe_customer_id = create_stripe_customer(name, email)

        role = await self.gdb.get(Role, 'customer')

        user = User()
        user.user_id = MakeTimedUniqueId()
        # user.stripe_customer_id = stripe_customer_id
        user.role_id = role.role_id
        user.email = email
        user.password = func.md5(password)
        user.name = name
        # user.avatar = picture
        user.email_verified = False
        user.google_user = False
        await self.gdb.add(user)
        await self.gdb.flush()

        settings = Settings()
        settings.setting_id = user.user_id
        settings.setting_key = user.user_id
        settings.setting_json = json.dumps({

        })
        await self.gdb.add(settings)
        await self.gdb.flush()

        token = await self._create_verification_token(user.user_id, subscription_id, period)
        # confirmation_link = f'{self.base_url}/verification/confirm-email?token={token}'
        # print(confirmation_link)

        # Send confirm email
        subject, email_body = confirmation_email({'name': name, 'base_url': self.base_url, 'token': token})
        send_email_background(email, subject, email_body)

        data = {}
        await self.send_response_v2('Signup Successful', data)

    async def login_with_google(self):
        await asyncio.sleep(2)
        return

        token = self.data['credential']
        # print(token)
        id_info = id_token.verify_oauth2_token(token, requests.Request(), ClientID)
        # print(id_info)

        email = id_info['email']
        email_verified = id_info['email_verified']
        name = id_info['name']
        # picture = id_info['picture']

        query = self.gdb.query(User).filter(User.email == email)
        user = await self.gdb.one_or_none(query)
        if user is None:
            # stripe_customer_id = create_stripe_customer(name, email)

            password = make_uuid4()

            m = hashlib.md5()
            m.update(str(password).encode('utf-8'))
            hashed_password = m.hexdigest()

            user = User()
            user.user_id = MakeTimedUniqueId()
            # user.stripe_customer_id = stripe_customer_id
            user.role_id = None
            user.email = email
            user.password = hashed_password
            user.name = name
            # user.avatar = picture
            user.email_verified = email_verified
            user.google_user = True
            await self.gdb.add(user)
            await self.gdb.flush()

            settings = Settings()
            settings.setting_id = user.user_id
            settings.setting_key = user.user_id
            settings.setting_json = json.dumps({})
            await self.gdb.add(settings)
            await self.gdb.flush()

        # print('google user logging in ...........')
        # raise GeneralException(401, 'invalid username or password')
        self.data['email'] = email

        await self.login(skip_password=True)

    async def validate(self):

        gdb = self.gdb

        query = gdb.query(User).filter(User.email == self.data['email'])
        user = await gdb.one_or_none(query)
        if user is None:
            raise GeneralException(401, 'invalid username or password')

        m = hashlib.md5()
        m.update(str(self.data['password']).encode('utf-8'))
        passwd = m.hexdigest()

        if passwd != user.password:
            raise GeneralException(401, 'username and password mismatch')

        data = {'validated': True, 'two_factor_enabled': user.two_factor_enabled}
        await self.send_response(data)

    async def login(self, skip_password=False):

        gdb = self.gdb

        query = gdb.query(User).filter(User.email == self.data['email'])
        user: User = await gdb.one_or_none(query)
        if user is None:
            return await self.send_response_v2('Invalid Email or Password', {
                'error': [{
                    'type': 'email', 'message': 'Check your email address'
                }]
            })

        if not skip_password:
            m = hashlib.md5()
            m.update(str(self.data['password']).encode('utf-8'))
            passwd = m.hexdigest()

            if passwd != user.password:
                return await self.send_response_v2('Invalid Email or Password', {
                    'error': [{
                        'type': 'password', 'message': 'Check your password'
                    }]
                })

        if not user.email_verified:
            return await self.send_response_v2('Please verify your email first!', {
                'error': [{
                    'type': 'password', 'message': 'Please verify your email first'
                }]
            })

        user.last_login = int(time.time())

        # if user.last_used_ip != self.request.remote_ip:
        #     # send login email
        #     subject, email_body = email_new_login({'name': user.name})
        #     send_email_background(user.email, subject, email_body)

        user.last_used_ip = self.request.remote_ip

        role = await gdb.get(Role, user.role_id)
        profile = make_profile_data(user, role)

        sid = MakeTimedUniqueId()

        ss = UserSession()
        ss.user_id = user.user_id
        ss.session_id = sid
        ss.session_data = json.dumps(profile)
        ss.date_added = int(time.time())
        ss.date_updated = int(time.time())
        await gdb.add(ss)

        sd = {
            'exp': time.time() + (365 * 86400),
            'session_id': sid,
        }

        # make jwt token
        encoded_jwt = jwt.encode(sd, os.getenv('AUTH_COOKIE_SECRET'), algorithm="HS256")
        # self.set_secure_cookie(self.cookie_name, encoded_jwt)

        data = {
            'base_url': self.base_url,
            'access_token': encoded_jwt,
            'user': profile,
        }

        await self.send_response_v2('Login successful', data)

    async def login_with_token(self):

        gdb = self.gdb

        session_id = await self.decode_session()

        user_session: UserSession = await gdb.get(UserSession, session_id)
        if user_session is None:
            raise GeneralException(401, 'Unauthorized')

        profile = json.loads(user_session.session_data)

        user_id = user_session.user_id

        sd = {
            'exp': time.time() + 86400,
            'session_id': session_id,
        }

        # make jwt token
        encoded_jwt = jwt.encode(sd, os.getenv('AUTH_COOKIE_SECRET'), algorithm="HS256")
        # self.set_secure_cookie(self.cookie_name, encoded_jwt)

        data = {
            'base_url': self.base_url,
            'access_token': encoded_jwt,
            'user': profile,
        }

        await self.send_response_v2('Login successful', data)

    async def login_with_provided_token(self):

        token = self.data['token']
        period = self.data.get('period')
        subscription = self.data.get('subscription')

        gdb = self.gdb

        session_id = await self.decode_token(token)

        user_session: UserSession = await gdb.get(UserSession, session_id)
        if user_session is None:
            return await self.send_response_v2('Invalid Token', {
                'error': [{
                    'type': 'token', 'message': 'Invalid Token'
                }]
            })

        profile = json.loads(user_session.session_data)
        sd = {
            'exp': time.time() + 86400,
            'session_id': session_id,
        }

        # make jwt token
        encoded_jwt = jwt.encode(sd, os.getenv('AUTH_COOKIE_SECRET'), algorithm="HS256")
        # self.set_secure_cookie(self.cookie_name, encoded_jwt)

        # platform_url = os.getenv('PLATFORM_URL')

        if subscription is not None:
            profile['loginRedirectUrl'] = f'subscription?period={period}&subscription={subscription}'

        data = {
            'base_url': self.base_url,
            'access_token': encoded_jwt,
            'user': profile,
        }

        await self.send_response_v2('Login successful', data)

    async def _create_verification_token(self, user_id, subscription_id, period, valid_days=1):

        vc_code = make_string(6)

        valid_until = time.time() + (86400 * valid_days)

        sd = {
            'exp': valid_until,
            'session_id': vc_code,
            'user_id': user_id,
            'subscription_id': subscription_id,
            'period': period
        }

        token = jwt.encode(sd, os.getenv('AUTH_COOKIE_SECRET'), algorithm="HS256")

        vc = VerificationCode()
        vc.code_id = MakeTimedUniqueId()
        vc.user_id = user_id
        vc.code = vc_code
        vc.expiry_time = valid_until
        await self.gdb.add(vc)

        return token

    async def forgot_password(self):
        gdb = self.gdb

        query = gdb.query(User).filter(User.email == self.data['email'])
        user = await gdb.one_or_none(query)
        if user is None:
            return await self.send_response_v2('User with this email does not exist!', {
                'error': [{
                    'type': 'email', 'message': 'User with this email does not exist!'
                }]
            })

        vc_code = make_string(6)

        sd = {
            'exp': time.time() + 86400,
            'session_id': vc_code,
        }
        token = jwt.encode(sd, os.getenv('AUTH_COOKIE_SECRET'), algorithm="HS256")

        vc = VerificationCode()
        vc.code_id = MakeTimedUniqueId()
        vc.user_id = user.user_id
        vc.code = vc_code
        vc.expiry_time = int(time.time()) + (5 * 60)
        await gdb.add(vc)

        # send forgot password email
        portal_link = os.getenv('PLATFORM_URL')
        subject, email_body = reset_link_email({'name': user.name, 'base_url': portal_link, 'token': token})
        send_email_background(user.email, subject, email_body)

        await self.send_response_v2('Verification link sent, please check your email', {})

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

        return token_data['session_id']

    async def reset_password(self):

        gdb = self.gdb

        token = self.data['token']

        vc_code = await self.decode_token(token)
        if vc_code is None:
            return await self.send_response_v2('Invalid Token', {
                'error': [{
                    'type': 'token', 'message': 'Invalid Token'
                }]
            })

        query = gdb.query(VerificationCode).filter(
            VerificationCode.code == vc_code)
        vc = await gdb.one_or_none(query)
        if vc is not None:
            if vc.expiry_time < int(time.time()):
                return await self.send_response_v2('Verification Code Expired', {
                    'error': [{
                        'type': 'token', 'message': 'Token Expired'
                    }]
                })

            m = hashlib.md5()
            m.update(str(self.data['password']).encode('utf-8'))
            hashed_password = m.hexdigest()
            
            query = gdb.query(User).filter(User.user_id == vc.user_id)
            user = await gdb.one_or_none(query)
            user.password = hashed_password
            user.email_verified = True

            # send reset password success email
            subject, email_body = reset_successful_email({'name': user.name})
            send_email_background(user.email, subject, email_body)

            # delete verification code on use
            await gdb.delete(vc)

        await self.send_response_v2('Password reset successfully', {})
