import hashlib
import json
import os
import asyncio
import time

from dotenv import load_dotenv
from sqlalchemy import func

from common import MakeTimedUniqueId
from common.constants import SystemConstants
from common.database_v2 import make_engine, make_connection, DBBase
from modules.application.models import Role, User, Settings
# from common.stripe_helper import create_stripe_customer


class Application:

    def __init__(self):
        self.db_engine = make_engine()

    async def Create(self):
        DBBase.metadata.create_all(self.db_engine)
        print('done')

    async def Run(self):
        version = os.getenv('DEPLOYMENT_VERSION')
        print('version: ', version)

        async with self.db_engine.begin() as conn:
            await conn.run_sync(DBBase.metadata.create_all)

        gdb = make_connection(db_engine=self.db_engine)

        try:
            
            now = int(time.time())

            name = 'Admin'
            email = 'admin@email.com'
            password = 'Admin@1'
            # stripe_customer_id = create_stripe_customer(name, email)

            role = Role()
            role.role_id = name.lower()
            role.name = name
            role.role = name

            role.date_added = now
            role.date_updated = now
            gdb.add(role)

            m = hashlib.md5()
            m.update(str(password).encode('utf-8'))
            hashed_password = m.hexdigest()

            user = User()
            user.user_id = name.lower()
            user.role_id = role.role_id
            user.email = email
            # user.stripe_customer_id = stripe_customer_id
            user.password = hashed_password
            user.name = name
            user.email_verified = True
            
            user.date_added = now
            user.date_updated = now
            gdb.add(user)

            role = Role()
            role.role_id = 'customer'
            role.name = 'Customer'
            role.role = 'Customer'
            
            role.date_added = now
            role.date_updated = now
            gdb.add(role)

            # user settings
            settings = Settings()
            settings.setting_id = user.user_id
            settings.setting_key = user.user_id
            settings.setting_json = json.dumps({

            })

            settings.date_added = now
            settings.date_updated = now
            gdb.add(settings)

            # system settings
            settings = Settings()
            settings.setting_id = SystemConstants.Setting.SYSTEM_SETTINGS
            settings.setting_key = SystemConstants.Setting.SYSTEM_SETTINGS
            settings.setting_json = json.dumps({
            })

            settings.date_added = now
            settings.date_updated = now
            gdb.add(settings)

            await gdb.commit()

            print('done')

        except Exception as ex:
            await gdb.rollback()
            print('Error:', str(ex))

        finally:
            await gdb.close()


if __name__ == "__main__":

    load_dotenv(override=True)
    loop = asyncio.new_event_loop()

    app = Application()
    print('database -> {}'.format(app.db_engine.url))
    loop.run_until_complete(app.Run())
