
import os
import math
from common.exceptions import GeneralException
from common import MakeTimedUniqueId
from sqlalchemy import asc, desc, func


class CrudController:

    def __init__(self, ctx):
        self.gdb = None
        self.data = {}
        self.context = ctx

        self.gdb = getattr(ctx, 'gdb', None)
        self.data = getattr(ctx, 'data', {})
        self.files = getattr(ctx, 'files', [])

        self.PublicMethods = []

    # Crud Functions
    async def insert(self, model, data, make_udid=True):
        if data is None:
            raise GeneralException(f'insert: unable to insert record: None')

        rec = model()

        for k, v in data.items():
            if isinstance(v, str) and v == '':
                v = None
            if v == 'null' or v == 'undefined':
                v = None

            attr = getattr(model, k, None)
            if attr is not None:
                setattr(rec, k, v)

        row_id = getattr(rec, model.__primary_key__)
        if row_id is None and make_udid:
            setattr(rec, model.__primary_key__, MakeTimedUniqueId())

        await self.gdb.add(rec)

        if not make_udid:
            await self.gdb.flush()

        row_id = getattr(rec, model.__primary_key__)

        return row_id

    async def upgrade(self, model, data):
        if data is None:
            raise GeneralException(f'update: unable to update record: None')

        row_id = data.get('id', None)
        rec = await self.single(model, row_id)

        if rec is None:
            raise GeneralException(f'update: existing record ({row_id}) not found!')

        for k, v in data.items():
            # if k == model.__primary_key__:
            #     continue

            if isinstance(v, str) and v == '':
                v = None

            if v == 'null' or v == 'undefined':
                v = None

            attr = getattr(model, k, None)
            if attr is not None:
                setattr(rec, k, v)

        row_id = getattr(rec, model.__primary_key__)
        return row_id

    async def single(self, model, row_id):
        if row_id is None:
            raise GeneralException(f'single: unable to fetch record: {row_id}')

        data = await self.gdb.get(model, row_id)
        return data

    async def all(self, model, query=None):

        per_page = int(self.data['limit']) if 'limit' in self.data and self.data['limit'].isdigit() else 10
        page = int(self.data['page']) if 'page' in self.data and self.data['page'].isdigit() else 1
        limit = per_page
        offset = 0 if page == 1 else (per_page * (page - 1))
        order_by = self.data.get('order_by', model.__primary_key__)
        order_value = self.data.get('order_value', 'desc')
        order_value = asc if order_value.lower() == 'asc' else desc
        # is_active = self.data.get('is_active', None)

        if query is None:
            query = self.gdb.query(model)

        # if is_active is not None:
        #     col = getattr(model, 'is_active', None)
        #     if col is not None:
        #         if is_active == 'active':
        #             query = query.filter(col.is_(True))
        #         if is_active == 'inactive':
        #             query = query.filter(col.is_(False))

        count = await self.gdb.count(model, query)

        col = getattr(model, order_by, None)
        if col is not None:
            query = query.order_by(order_value(col))

        query = query.limit(limit)
        query = query.offset(offset)

        records = await self.gdb.all(query)

        pages = 0
        if count > 0:
            if limit > count:
                limit = count
            pages = math.ceil(count / limit)

        return records, pages, count

    async def in_active(self, model, row_id):

        rec = await self.single(model, row_id)
        if rec is None:
            raise GeneralException(f'in_active: existing record ({row_id}) not found!')

        col = getattr(model, 'is_active', None)
        if col is not None:
            rec.is_active = False

        return row_id

    async def remove(self, model, row_id):

        rec = await self.single(model, row_id)
        if rec is None:
            raise GeneralException(message=f'delete: existing record ({row_id}) not found!')

        await self.gdb.delete(rec)
        await self.gdb.flush()

        return row_id

    # Utility Functions
    async def delete_file(self, file_url, dir_name='common'):
        if file_url is None:
            return

        df = os.path.join(os.getenv('UPLOAD_DIR'), dir_name)
        f_name = file_url.split('/')[-1]
        d_file = os.path.join(df, f_name)

        if os.path.isfile(d_file):
            os.unlink(d_file)

    async def upload_file(self, allowed_ext=None, dir_name='common', file_key='UserFile'):
        # files = self.files
        if file_key not in self.files:
            return

        up_file = self.files[file_key][0]
        file_only_name, file_extension = os.path.splitext(up_file['filename'])
        file_ext = file_extension.lower()

        if allowed_ext is not None and len(allowed_ext) > 0 and file_ext not in allowed_ext:
            raise GeneralException(f'This System only accept these {", ".join(allowed_ext)} extensions')

        df = os.path.join(self.context.files_dir, dir_name)
        if not os.path.exists(df):
            os.makedirs(df)

        f_name = f'{MakeTimedUniqueId()}{file_ext}'
        d_file = os.path.join(df, f_name)
        with open(d_file, 'wb') as f:
            f.write(up_file['body'])

        data = {
            'file_id': f_name,
            'file_name': up_file['filename'],
            'file_ext': file_ext,
            'file_size': len(up_file['body']),
            'content_type': up_file['content_type'],
            'file_path': d_file,
            'file_url': f'/files/{dir_name}/{f_name}'
        }

        return data

    def assert_data(self, *keys):
        for key in keys:
            if key not in self.data or self.data[key] is None:
                raise KeyError(key)
        return
