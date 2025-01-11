from sqlalchemy import select, insert, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession


class GDBHelper:

    def __init__(self, dbs):
        self.db_session: AsyncSession = dbs

    def query(self, *models):
        return select(*models)

    async def get(self, model, p_key):
        """Return an instance of model for given primary key,
        """
        if p_key is None:
            return None

        res = await self.db_session.get(model, p_key)
        return res

    async def execute(self, query):
        """Return iterator for given query
        should be attributes, bundles, etc.
        """
        res = await self.db_session.execute(query)
        return res

    async def first(self, query):
        """Return first record for given query
        should be model
        """
        query = query.limit(1)
        res = await self.db_session.execute(query)
        res = res.scalars().one_or_none()
        return res

    async def one_or_none(self, query):
        """Return one record for given query
        should be model
        """
        res = await self.db_session.execute(query)
        res = res.scalars().one_or_none()
        return res

    async def all(self, query):
        """Return one record for given query
        should be model
        """
        res = await self.db_session.execute(query)
        res = res.scalars().all()
        return res

    async def scalar(self, query):
        """Return scalar value for given query
        should be model
        """
        res = await self.db_session.execute(query)
        res = res.scalar()
        return res

    async def count(self, model, query):
        p_key_col = getattr(model, model.__primary_key__)
        # p_key_col = getattr(model, '__primary_key__')
        count_query = query.with_only_columns(func.count(p_key_col))
        res = await self.db_session.execute(count_query)
        return res.scalar_one()

    async def add(self, instance):
        self.db_session.add(instance)

    async def create(self, model, data):
        stmt = insert(model).values(**data)
        res = await self.execute(stmt)
        return res

    async def update(self, model, criteria, data):
        stmt = update(model).where(criteria).values(**data)
        res = await self.execute(stmt)
        return res

    async def delete(self, instance):
        res = await self.db_session.delete(instance)
        return res

    # async def delete(self, model, criteria):
    #     stmt = delete(model).where(criteria)
    #     res = await self.execute(stmt)
    #     await res
    async def bulk_insert(self, model, records):
        res = await self.db_session.run_sync(lambda gdb: gdb.bulk_insert_mappings(model, records))
        return res

    async def bulk_update(self, model, records):
        res = await self.db_session.run_sync(lambda gdb: gdb.bulk_update_mappings(model, records))
        return res

    async def run_sync(self, sync_func):
        await self.db_session.run_sync(sync_func)

    async def flush(self):
        await self.db_session.flush()

    async def commit(self):
        await self.db_session.commit()

    async def rollback(self):
        await self.db_session.rollback()

    async def close(self):
        await self.db_session.close()
