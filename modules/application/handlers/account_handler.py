import os
import json
import hashlib
import time

import jwt
import pyotp
from sqlalchemy import or_

from common.exceptions import GeneralException
from common.timer import ScheduleTask
from modules.application.models import Account
from common.base_handler import BaseHandler
from common.crud import CrudController
from stocktwits import stocktwits_main


class AccountApiHandler(BaseHandler):

    async def prepare(self):
        await super().prepare()
        self.set_header("Content-Type", "application/json")
        # await self.decode_body()
        
        if self.request.method != 'OPTIONS':
            # session_id = await self.decode_session()
            self.gdb = await self.make_application_gdb()
            # self.session = await fetch_session(self.gdb, session_id)

    async def fetch_all(self, active=True):
        ctrl = CrudController(self)
        search = self.data.get('search')
        query = self.gdb.query(Account)

        if search not in ['', 'null', None]:
            query = query.filter(or_(
                Account.fullname.contains(search),
            ))

        records, pages, count = await ctrl.all(Account, query)

        data = []
        rec: Account
        for rec in records:
            row = {
                'id': rec.account_id,
            }
            row.update(rec.toJSON())
            data.append(row)

        page = self.data.get('page', 1)
        limit = self.data.get('limit', 30)
        resp = {'page': page, 'limit': limit, 'pages': pages, 'records': data, 'total': count}
        return resp

    async def fetch_single(self, rec_id):
        ctrl = CrudController(self)
        rec: Account = await ctrl.single(Account, rec_id)
        if rec is None:
            raise GeneralException(404, 'Record not found')

        resp = rec.toJSON()
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

        await self.send_response_v2('Accounts fetched successfully', data=resp)

    async def post_api(self, *args, **kwargs):

        ctrl = CrudController(self)
        row_id = await ctrl.insert(Account, self.data)

        resp = {'id': row_id}
        await self.send_response_v2('Account added successfully', data=resp)

    async def patch_api(self, *args, **kwargs):

        ctrl = CrudController(self)
        rec: Account = await ctrl.single(Account, self.data['id'])
        if rec is None:
            raise GeneralException(404, 'Record not found')

        query = self.gdb.query(Account.username).filter(Account.account_id != self.data['id'])
        query = query.filter(Account.username == self.data['username'])
        account_username = await self.gdb.one_or_none(query)

        if account_username is not None:
            raise GeneralException(code=403, message=f'Account username is already used')

        row_id = await ctrl.upgrade(Account, self.data)
        resp = {'id': row_id}

        await self.send_response_v2('Account updated successfully', data=resp)

    async def delete_api(self, *args, **kwargs):
        if len(args) != 1:
            raise GeneralException(404)

        row_id = args[0]
        ctrl = CrudController(self)
        rec: Account = await ctrl.single(Account, row_id)
        if rec is None:
            raise GeneralException(404, 'Record not found')

        await ctrl.in_active(Account, row_id)
        resp = {}

        await self.send_response_v2('Account deleted successfully')
