
import os
import time
import uuid
import asyncio

from datetime import datetime, timedelta, timezone

from .api_client import ApiClient


class HttpUser:

    def __init__(self, app):
        self.application = app

        self.client = ApiClient(os.getenv('REMOTE_URL'))

        self.token = None
        self.headers = None

        self.config = None
        self.uuid = str(uuid.uuid4()).replace('-', '')

    async def health(self):
        resp = await self.application.send_request(self, method='GET', end_point='/health', body={'version': '1'})
        return resp

    async def signup(self, email, password, name, company):
        body = {
            "email": email,
            "password": password,
            "full_name": name,
            "company_name": company,
            "company_type_id": "SOLE_PROPRIETOR",
            "industry_type_id": "62"
        }
        resp = await self.application.send_request(self, method='POST', end_point='/auth/signup', body=body)
        return resp

    async def login(self, email, password, device_id, device_type='Web', app_type='Web'):
        req = {
            "email": email, "password": password, "device_id": device_id,
            "device_name": "SIM-001", "device_model": "SIM-001",
            "device_type": device_type, "os_name": device_type, "os_version": "0.0.0",
            "pn_type": "Firebase", "pn_token": "", "app_version": "0.0.0-000",
            "app_type": app_type, "is_patient": True if app_type == 'Patient' else False,
            "lang": "en"
        }

        resp = await self.client.post("/auth/Login", body=req)

        self.token = resp['auth_token']
        self.config = resp['user']

        self.headers = {'Authorization': '' + self.token}
        print('login successful ....!')
