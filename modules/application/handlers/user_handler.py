import os
import json
import hashlib
import time

import jwt
import pyotp
from sqlalchemy import func, or_, exists

from common.email_sender import send_email_background
from common.exceptions import GeneralException
from common.helpers import make_string, MakeTimedUniqueId
from modules.application.helper_functions import fetch_session, set_password_email
from modules.application.models import User, Role, Settings, UserSession, VerificationCode
from common.base_handler import BaseHandler
from common.crud import CrudController


class UserApiHandler(BaseHandler):

    async def prepare(self):
        await super().prepare()
        self.set_header("Content-Type", "application/json")
        # await self.decode_body()
        
        if self.request.method != 'OPTIONS':
            session_id = await self.decode_session()
            self.gdb = await self.make_application_gdb()
            self.session = await fetch_session(self.gdb, session_id)

    async def fetch_all(self, active=True):
        ctrl = CrudController(self)
        search = self.data.get('search')
        query = self.gdb.query(User).filter(User.is_active.is_(active))

        if search not in ['', 'null', None]:
            query = query.filter(or_(
                User.name.contains(search),
                User.phone.contains(search),
                User.email.contains(search)
            ))

        records, pages, count = await ctrl.all(User, query)

        roles_records = await self.gdb.all(self.gdb.query(Role))
        roles_dict = {role.role_id: role.name for role in roles_records}

        data = []
        rec: User
        for rec in records:
            row = {
                'id': rec.user_id,
                'role': roles_dict.get(rec.role_id),
            }
            row.update(rec.toJSON())
            data.append(row)

        page = self.data.get('page', 1)
        limit = self.data.get('limit', 30)
        resp = {'page': page, 'limit': limit, 'pages': pages, 'records': data, 'total': count}
        return resp

    async def fetch_single(self, rec_id):
        ctrl = CrudController(self)
        rec: User = await ctrl.single(User, rec_id)
        if rec is None:
            raise GeneralException(404, 'Record not found')

        resp = rec.toJSON()
        resp['password'] = 'encrypted'
        return {'record': resp}

    async def get_api(self, *args, **kwargs):

        resp = {}
        endpoint = args[0] if len(args) > 0 else ''

        if endpoint == 'inactive':
            resp = await self.fetch_all(active=False)

        elif endpoint != '':
            resp = await self.fetch_single(args[0])
        else:
            resp = await self.fetch_all()

        await self.send_response_v2('Users fetched successfully', data=resp)

    async def post_api(self, *args, **kwargs):

        query = self.gdb.query(User.email)
        query = query.filter(User.email == self.data['email'])
        email = await self.gdb.one_or_none(query)

        if email is not None:
            raise GeneralException(message=f'Email is already used')

        self.data['password'] = func.md5(self.data['password'])

        ctrl = CrudController(self)
        row_id = await ctrl.insert(User, self.data)

        row_id = await ctrl.insert(Settings, {
            'setting_id': row_id,
            'setting_key': row_id,
            'setting_json': json.dumps({})
        })

        resp = {'id': row_id}

        await self.send_response_v2('User added successfully', data=resp)

    async def patch_api(self, *args, **kwargs):

        ctrl = CrudController(self)
        rec: User = await ctrl.single(User, self.data['id'])
        if rec is None:
            raise GeneralException(404, 'Record not found')

        query = self.gdb.query(User.email).filter(User.user_id != self.data['id'])
        query = query.filter(User.email == self.data['email'])
        user_email = await self.gdb.one_or_none(query)

        if user_email is not None:
            raise GeneralException(code=403, message=f'Email is already used')

        password = self.data.pop('password', None)
        if password != 'encrypted':
            self.data['password'] = func.md5(password)

        row_id = await ctrl.upgrade(User, self.data)
        resp = {'id': row_id}

        await self.send_response_v2('User updated successfully', data=resp)

    async def delete_api(self, *args, **kwargs):
        if len(args) != 1:
            raise GeneralException(404)

        row_id = args[0]
        ctrl = CrudController(self)
        rec: User = await ctrl.single(User, row_id)
        if rec is None:
            raise GeneralException(404, 'Record not found')

        await ctrl.in_active(User, row_id)
        resp = {}

        await self.send_response_v2('User deleted successfully')

    async def send_email(self, user_id):
        vc_code = make_string(6)

        sd = {
            'exp': time.time() + 86400,
            'session_id': vc_code,
        }
        token = jwt.encode(sd, os.getenv('AUTH_COOKIE_SECRET'), algorithm="HS256")

        vc = VerificationCode()
        vc.code_id = MakeTimedUniqueId()
        vc.user_id = user_id
        vc.code = vc_code
        vc.expiry_time = int(time.time()) + (5 * 60)
        await self.gdb.add(vc)

        query = self.gdb.query(Role.name)
        query = query.filter(Role.role_id == self.data['role_id'])
        role = await self.gdb.one_or_none(query)

        # send forgot password email
        portal_link = os.getenv('PLATFORM_URL')
        subject, email_body = set_password_email({
            'name': self.data['name'],
            'base_url': portal_link,
            'token': token,
            'role': role
        })
        send_email_background(self.data['email'], subject, email_body)
