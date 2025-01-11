
import os

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from decimal import Decimal

DBBase = declarative_base()


DEFAULT_TABLE_ARGS = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8', 'mysql_collate': 'utf8_general_ci'}


def make_engine(db=None):
    debug_db = True if os.environ.get('DB_DEBUG') == '1' else False

    db_config = {
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'host': os.getenv('DB_HOST_MAIN'),
        'database': db or os.getenv('DB_NAME')
    }

    # db_url = 'mysql+asyncmy://{user}:{password}@{host}/{database}'.format(**db_config)
    # db_url = 'mysql+aiomysql://{user}:{password}@{host}/{database}'.format(**db_config)
    db_url = 'sqlite+aiosqlite:///database/selenium.db'
    # print('DB =', db_config['database'])

    db_engine = create_async_engine(
        db_url, echo=debug_db,
        # pool_size=50,
        # pool_recycle=3600
    )

    return db_engine


def make_connection(db_engine=None):

    db_engine = make_engine() if db_engine is None else db_engine

    session_maker = sessionmaker(
        bind=db_engine,
        expire_on_commit=False,
        class_=AsyncSession
    )

    return session_maker()


def toJSON(self):
    obj = {}
    for c in self.__table__.columns:
        val = getattr(self, c.name)

        if isinstance(val, Decimal):
            val = float(val)

        obj[c.name] = val

    return obj


setattr(DBBase, 'toJSON', toJSON)
