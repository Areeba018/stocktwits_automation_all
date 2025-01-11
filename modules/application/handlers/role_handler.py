import json

from sqlalchemy import or_

from common.exceptions import GeneralException
from modules.application.helper_functions import fetch_session
from modules.application.models import Role
from common.base_handler import BaseHandler
from common.crud import CrudController


class RoleApiHandler(BaseHandler):

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
        query = self.gdb.query(Role).filter(Role.is_active.is_(active))

        if search not in ['', 'null', None]:
            query = query.filter(or_(
                Role.role_id.contains(search),
                Role.name.contains(search)
            ))

        records, pages, count = await ctrl.all(Role, query)

        data = []
        rec: Role
        for rec in records:
            row = {
                'id': rec.role_id,
            }
            row.update(rec.toJSON())

            row['permissions'] = json.loads(rec.permissions)

            data.append(row)

        page = self.data.get('page', 1)
        limit = self.data.get('limit', 30)
        resp = {'page': page, 'limit': limit, 'pages': pages, 'records': data, 'total': count}
        return resp

    async def fetch_single(self, rec_id):
        ctrl = CrudController(self)
        rec: Role = await ctrl.single(Role, rec_id)
        if rec is None:
            raise GeneralException(404, 'Record not found')
        resp = {'record': rec.toJSON()}
        return resp

    async def get_api(self, *args, **kwargs):

        resp = {}
        endpoint = args[0] if len(args) > 0 else ''

        if endpoint == 'inactive':
            resp = await self.fetch_all(active=False)

        elif endpoint != '':
            resp = await self.fetch_single(args[0])
        else:
            resp = await self.fetch_all()

        await self.send_response_v2('Roles fetched successfully', data=resp)

    async def post_api(self, *args, **kwargs):

        query = self.gdb.query(Role.name)
        query = query.filter(Role.name == self.data['name'])
        role_name = await self.gdb.one_or_none(query)

        if role_name is not None:
            raise GeneralException(code=403, message=f'Role Name is already used')

        self.data['permissions'] = json.dumps(self.data['permissions'])

        ctrl = CrudController(self)
        row_id = await ctrl.insert(Role, self.data)

        await self.send_response_v2('Role added successfully')

    async def patch_api(self, *args, **kwargs):

        ctrl = CrudController(self)
        rec: Role = await ctrl.single(Role, self.data['id'])
        if rec is None:
            raise GeneralException(404, 'Record not found')

        query = self.gdb.query(Role.name).filter(Role.role_id != self.data['id'])
        query = query.filter(Role.name == self.data['name'])
        role_name = await self.gdb.one_or_none(query)

        if role_name is not None:
            raise GeneralException(code=403, message=f'Role Name is already used')

        self.data['permissions'] = json.dumps(self.data['permissions'])

        row_id = await ctrl.upgrade(Role, self.data)
        # resp = {'id': row_id}

        await self.send_response_v2('Role updated successfully')

    async def delete_api(self, *args, **kwargs):
        if len(args) != 1:
            raise GeneralException(404)

        row_id = args[0]
        ctrl = CrudController(self)
        rec: Role = await ctrl.single(Role, row_id)
        if rec is None:
            raise GeneralException(404, 'Record not found')

        await ctrl.in_active(Role, row_id)
        resp = {}

        await self.send_response_v2('Role deleted successfully')
