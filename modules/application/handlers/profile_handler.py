import os
import json
import hashlib
import time

import jwt
import pyotp
from sqlalchemy import func, or_

from common.exceptions import GeneralException
from common.helpers import make_uuid4, MakeTimedUniqueId
from common.timer import ScheduleTask
from modules.application.helper_functions import fetch_session
from modules.application.models import Profile, Settings
from common.base_handler import BaseHandler
from common.crud import CrudController
from stocktwits import stocktwits_main


class ProfileApiHandler(BaseHandler):

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
        query = self.gdb.query(Profile).filter(Profile.is_active.is_(active))

        if search not in ['', 'null', None]:
            query = query.filter(or_(
                Profile.name.contains(search),
            ))

        records, pages, count = await ctrl.all(Profile, query)

        data = []
        rec: Profile
        for rec in records:
            row = {
                'id': rec.profile_id,
            }
            row.update(rec.toJSON())
            data.append(row)

        page = self.data.get('page', 1)
        limit = self.data.get('limit', 30)
        resp = {'page': page, 'limit': limit, 'pages': pages, 'records': data, 'total': count}
        return resp

    async def fetch_single(self, rec_id):
        ctrl = CrudController(self)
        rec: Profile = await ctrl.single(Profile, rec_id)
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

        await self.send_response_v2('Profiles fetched successfully', data=resp)

    async def post_api(self, *args, **kwargs):

        ctrl = CrudController(self)
        row_id = await ctrl.insert(Profile, self.data)

        resp = {'id': row_id}
        await self.send_response_v2('Profile added successfully', data=resp)

    async def patch_api(self, *args, **kwargs):

        resp = {}
        endpoint = args[0] if len(args) > 0 else ''
        
        # api/profiles/start
        if endpoint == 'start':
            ctrl = CrudController(self)
            rec: Profile = await ctrl.single(Profile, self.data['id'])
            if rec is None:
                raise GeneralException(404, 'Record not found')

            # instantiate profile            
            context = {
                'application': self.application,
                'profile': rec.toJSON(),
            }

            task = ScheduleTask(rec.profile_id, context, stocktwits_main)
            self.application.ActiveProfiles[rec.profile_id] = task
            
            row_id = await ctrl.upgrade(Profile, {
                'id': row_id,
                'status': 'Active',
            })
            resp = {'id': row_id}
            await self.send_response_v2('Profile activated successfully', data=resp)
            return

        elif endpoint == 'stop':
            ctrl = CrudController(self)
            rec: Profile = await ctrl.single(Profile, self.data['id'])
            if rec is None:
                raise GeneralException(404, 'Record not found')

            if rec.status in ['Inactive']:
                raise GeneralException(400, 'Profile is already inactive')

            # stop process with id
            task = self.application.ActiveProfiles.get(rec.profile_id)
            task and task.cancel()

            row_id = await ctrl.upgrade(Profile, {
                'id': row_id,
                'status': 'Inactive',
            })

            resp = {'id': row_id}
            await self.send_response_v2('Profile stopped successfully', data=resp)
            return

        ctrl = CrudController(self)
        rec: Profile = await ctrl.single(Profile, self.data['id'])
        if rec is None:
            raise GeneralException(404, 'Record not found')

        row_id = await ctrl.upgrade(Profile, self.data)
        resp = {'id': row_id}

        await self.send_response_v2('Profile updated successfully', data=resp)

    async def delete_api(self, *args, **kwargs):
        if len(args) != 1:
            raise GeneralException(404)

        row_id = args[0]
        ctrl = CrudController(self)
        rec: Profile = await ctrl.single(Profile, row_id)
        if rec is None:
            raise GeneralException(404, 'Record not found')

        await ctrl.in_active(Profile, row_id)
        resp = {}

        await self.send_response_v2('Profile deleted successfully')
