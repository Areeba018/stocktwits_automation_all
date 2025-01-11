import os
import signal

import tornado.ioloop
import tornado.web
from dotenv import load_dotenv

from common.database_v2 import make_engine
from common.file_handler import SecureFileHandler
from modules.application.handlers import HealthHandler, AuthHandler, WebHandler, UserApiHandler, RoleApiHandler
from modules.application.handlers import (SocketHandler, VerificationHandler, SettingApiHandler, ProfileApiHandler,
                                          AccountApiHandler)


class Application(tornado.web.Application):

    def __init__(self):
        self.version = os.getenv('DEPLOYMENT_VERSION')
        self.ListenPort = int(os.getenv('LISTEN_PORT'))
        self.cookie_name = os.getenv('AUTH_COOKIE_NAME')
        self.base_url = os.getenv('BASE_URL')
        self.files_dir = os.getenv('DATA_STORAGE_ROOT')

        self.engine = make_engine()

        self.ActiveSessions = {}
        self.ActiveProfiles = {}

        settings = {
            'debug': False,
            'serve_traceback': False,
            'compress_response': True,
            'template_path': 'templates/',
            'static_url_prefix': '/assets/',
            'static_path': 'assets',  # STATIC_PATH,
            # 'xsrf_cookies': False,
            'cookie_secret': os.getenv('AUTH_COOKIE_SECRET'),
            # 'static_path': STATIC_PATH,
            # 'autoreload': bool(os.environ.get('AUTO_RELOAD', 0))
        }

        handlers = [
            (r"/health", HealthHandler),

            (r"/api/auth/(.*)", AuthHandler),
            (r"/api/users/(.*)", UserApiHandler),
            (r"/api/roles/(.*)", RoleApiHandler),
            (r"/api/profiles/(.*)", ProfileApiHandler),
            (r"/api/accounts/(.*)", AccountApiHandler),

            (r"/api/settings/(.*)", SettingApiHandler),

            (r'/socket', SocketHandler),

            (r"/files/(.*)", SecureFileHandler, {
                "path": ''
            }),

            (r"/verification/(.*)", VerificationHandler),
            (r"/(.*)", WebHandler),
        ]

        super(Application, self).__init__(handlers, **settings)

    def start(self):
        event_loop = tornado.ioloop.IOLoop.current()

        if os.name != 'nt':
            signal.signal(signal.SIGTERM, self.sig_handler)
            signal.signal(signal.SIGINT, self.sig_handler)

        listen_port = self.ListenPort
        print('Web Api Server is ready @ {}'.format(listen_port))

        self.listen(listen_port, address='0.0.0.0')

        event_loop.start()

    def shut_down(self):
        tornado.ioloop.IOLoop.instance().stop()

    def sig_handler(self, sig, frame):
        print('Got SIG %s, Server is stopping' % sig)
        tornado.ioloop.IOLoop.instance().add_callback_from_signal(self.shut_down)


if __name__ == "__main__":

    load_dotenv(override=True)

    app = Application()
    app.start()
