from typing import Optional

import tornado.web


class SecureFileHandler(tornado.web.StaticFileHandler):

    def initialize(self, path: str, default_filename: Optional[str] = None) -> None:

        # self.host = self.request.host
        # files_dir = self.application.get_env(self.host, 'data_storage_root')
        files_dir = self.application.files_dir
        dir_path = f'{files_dir}/{path}'

        # print('init', dir_path)

        super(SecureFileHandler, self).initialize(dir_path)

    async def prepare(self):

        # file access security disabled for now until implemented in android/ios apps

        # try:
        #     self.gdb = self.application.SessionMaker()
        # except Exception:
        #     traceback.print_exc()
        #     raise tornado.web.HTTPError(503)
        #
        # file_url = f'{self.request.path}'
        # print(file_url)

        # query = self.gdb.query(UserFile).filter(UserFile.file_url == file_url)
        # query = query.limit(1)
        # file: UserFile = query.one_or_none()
        #
        # if file is None:
        #     raise tornado.web.HTTPError(404)
        #
        # if file.is_public is True:
        #     return
        #
        # token = self.get_argument('token', None)
        #
        # self.Session = DecodeAuthSession(self, token)
        # if self.Session is None:
        #     raise tornado.web.HTTPError(401)

        return

    def on_finish(self):
        # if hasattr(self, 'gdb') and self.gdb is not None:
        #     self.gdb.close()

        super().on_finish()
