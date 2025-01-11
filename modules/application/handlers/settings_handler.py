import json

from common.constants import SystemConstants
from common.exceptions import GeneralException
from modules.application.helper_functions import fetch_session
from modules.application.models import Settings
from common.base_handler import BaseHandler
from common.crud import CrudController


class SettingApiHandler(BaseHandler):

    async def prepare(self):
        await super().prepare()
        self.set_header("Content-Type", "application/json")
        # await self.decode_body()

        if self.request.method != 'OPTIONS':
            session_id = await self.decode_session()
            self.gdb = await self.make_application_gdb()
            self.session = await fetch_session(self.gdb, session_id)

    async def fetch_single(self, rec_id):
        ctrl = CrudController(self)
        rec: Settings = await ctrl.single(Settings, rec_id)
        if rec is None:
            raise GeneralException(404, 'Record not found')
        resp = rec.toJSON()
        resp['setting_json'] = json.loads(rec.setting_json)
        return {'record': resp}

    async def get_api(self, *args, **kwargs):
        resp = await self.fetch_single(SystemConstants.Setting.SYSTEM_SETTINGS)
        await self.send_response_v2('Settings Fetched Successfully', data=resp)

    async def post_api(self, *args, **kwargs):
        raise GeneralException(404)

    async def patch_api(self, *args, **kwargs):

        setting = await self.gdb.get(Settings, SystemConstants.Setting.SYSTEM_SETTINGS)
        if setting is None:
            raise GeneralException(code=400, message=f'Setting not found!')

        update_data = {
            'id': SystemConstants.Setting.SYSTEM_SETTINGS,
            'setting_json': json.dumps(self.data)
        }
        ctrl = CrudController(self)
        await ctrl.upgrade(Settings, update_data)

        await self.send_response_v2('Settings Updated Successfully')

    async def delete_api(self, *args, **kwargs):
        raise GeneralException(404)
