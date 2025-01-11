
import os
import time
import uuid
import asyncio

from datetime import datetime, timedelta, timezone

from common.helpers import year_range, MakeTimedUniqueId
from .http_user import HttpUser


class TestUser(HttpUser):

    def __init__(self, app):
        super().__init__(app)

    async def sampl_api(self):
        params = {'page': 1, 'per_page': 10, 'search': 'name', 'order': 'desc'}
        resp = await self.application.send_request(self, method='GET', end_point='/api/sample/', body=params)
        return resp
