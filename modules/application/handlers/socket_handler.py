import json
import os
import time

import jwt
import tornado.web
import tornado.websocket
from tornado.ioloop import PeriodicCallback

from common.database_v2 import make_connection
from common.exceptions import GeneralException
from common.gdb_helper_v2 import GDBHelper
from common.helpers import make_uuid4
from modules.application.helper_functions import fetch_session
from modules.application.models import Settings

HEARTBEAT_TIME = 7  # seconds


class SocketHandler(tornado.websocket.WebSocketHandler):

    application: any
    session_id: str
    session: any
    uuid: str
    activeViews: list
    last_heartbeat_time: int
    heartbeat_thread: any
    gdb: [GDBHelper, None]
    base_url: str
    files_dir: str
    
    def check_origin(self, origin):
        return True

    async def get_token(self):
        token = self.get_argument('token', None)
        return token

    async def decode_session(self, _raise=True):

        encoded_jwt = await self.get_token()

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

    async def prepare(self):
        self.gdb = None
        self.session = None

        self.heartbeat_thread = None
        self.activeViews = []

        self.base_url = self.application.base_url
        self.files_dir = self.application.files_dir

        self.session_id = await self.decode_session(_raise=False)
        self.gdb = await self.make_application_gdb()

        try:
            self.session = await fetch_session(self.gdb, self.session_id)
            # await self.gdb.commit()
        except Exception as ex:
            # await self.gdb.rollback()
            print(f'Websocket: DB Exception {ex}')
        finally:
            await self.gdb.close()

        if self.session is None:
            print('WebSocket: session is None')
            return

        self.uuid = make_uuid4()

        await self.RegisterSession()

        self.last_heartbeat_time = int(time.time())

        self.heartbeat_thread = PeriodicCallback(lambda: self.CheckHeartbeat(), 1 * 3 * 1000)
        self.heartbeat_thread.start()

    async def open(self, *args, **kwargs):
        if self.session is None:
            await self.PostMessage(payload=dict(event='SessionExpired'))
            raise GeneralException(401, 'Session Expired')

        print(f'WebSocket: Opened: {self.session["profile"]["name"]}')

    def CheckHeartbeat(self):
        current_time = int(time.time())
        if (current_time - self.last_heartbeat_time) > HEARTBEAT_TIME:
            ActiveSessions = self.application.ActiveSessions
            if ActiveSessions is not None:
                sess = ActiveSessions.get(self.session_id, None)
                if sess is not None:
                    if sess.uuid == self.uuid:
                        sess.Cleanup()
                    else:
                        print('This should not happen ....!')

            self.ForceClose()

        return

    async def on_message(self, data):
        # print('on_message', data)
        payload = json.loads(data)

        event = payload.get('event', 'Heartbeat')
        data = payload.get('data', {})

        if event == 'Heartbeat':
            self.last_heartbeat_time = int(time.time())
            # print('KeepAlive--------------> ', event)
            await self.PostMessage(payload=dict(event='Heartbeat', data=int(time.time())))

        else:
            data = payload['data']

            # await self.some_method(data)

            await self.PostMessage(payload=dict(event=event, data=data))

            return

    async def PostMessage(self, payload):

        try:
            await self.write_message(json.dumps(payload))

        except Exception as e:
            print(f'WebSocket: unable to write ....{payload}')
            # print(e)

    def on_close(self):
        print('WebSocket: Closed')

        if self.heartbeat_thread is not None:
            self.heartbeat_thread.stop()

        if self.session is not None:
            self.UnregisterSession()

    def ForceClose(self):
        print('WebSocket: Force Closed ======== ')

        if self.heartbeat_thread is not None:
            self.heartbeat_thread.stop()

        self.session = None

        self.close()

        return

    def Cleanup(self):
        ActiveSessions = self.application.ActiveSessions
        # ActiveUsers = self.application.ActiveUsers

        ActiveSessions.pop(self.session_id)

        # user_info = ActiveUsers.get(self.user_id)
        # user_sessions = user_info.get('sessions', set())
        # if self.session_id in user_sessions:
        #     user_sessions.remove(self.session_id)

        # if len(user_sessions) == 0:
        #     ActiveUsers.pop(self.user_id)

    async def RegisterSession(self):

        ActiveSessions = self.application.ActiveSessions
        # if ActiveSessions is None:
        #     ActiveSessions = {}
        #     self.application.ActiveSessions[self.sitecode] = ActiveSessions
        #
        # ActiveUsers = self.application.ActiveUsers
        # if ActiveUsers is None:
        #     ActiveUsers = {}
        #     self.application.ActiveUsers[self.sitecode] = ActiveUsers

        sess = ActiveSessions.get(self.session_id, None)
        if sess is not None:
            print(f'RegisterSession: Force Close Dangling Session {sess.session["profile"]["name"]}')
            sess.Cleanup()
            sess.ForceClose()

        # if self.user_id not in ActiveUsers:
        #     ActiveUsers[self.user_id] = dict(sessions=set())

        # user_info = ActiveUsers.get(self.user_id)
        # user_sessions = user_info.get('sessions', set())
        # user_sessions.add(self.session_id)

        ActiveSessions[self.session_id] = self

        return

    def UnregisterSession(self):
        ActiveSessions = self.application.ActiveSessions
        # ActiveUsers = self.application.ActiveUsers

        # if ActiveSessions is None or ActiveUsers is None:
        #     print(f'UnregisterSession: ActiveSessions or ActiveUsers None {ActiveSessions} {ActiveUsers}')
        #     return

        sess = ActiveSessions.pop(self.session_id, None)
        if sess is None:
            print('UnregisterSession: session not found!')
            return

        # will come back later ...
        # user_info = ActiveUsers.get(self.user_id)
        # user_sessions = user_info.get('sessions', set())
        # if self.session_id in user_sessions:
        #     user_sessions.remove(self.session_id)
        #
        # if len(user_sessions) == 0:
        #     ActiveUsers.pop(self.user_id)
