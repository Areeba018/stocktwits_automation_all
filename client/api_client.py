
import json
import urllib.parse
from tornado.httpclient import AsyncHTTPClient, HTTPRequest


class ApiClient:

    def __init__(self, url=None):
        self.base_url = url

    def set_url(self, url):
        self.base_url = url

    async def get(self, url, headers=None, params=None):
        headers = headers if headers is not None else {}
        # headers['Content-Type'] = 'application/json'
        # body = json.dumps(body) if body is not None else '{}'
        http_client = AsyncHTTPClient()
        aa = urllib.parse.urlencode(params)
        req_url = f'{self.base_url}{url}?{aa}'
        req = HTTPRequest(url=req_url, method='GET', headers=headers, request_timeout=120.0)
        http_resp = await http_client.fetch(request=req, raise_error=True)
        http_resp = http_resp.body.decode('utf-8')

        http_client.close()

        return http_resp

    async def post(self, url, headers=None, body=None):
        headers = headers if headers is not None else {}
        headers['Content-Type'] = 'application/json'
        body = json.dumps(body) if body is not None else '{}'
        http_client = AsyncHTTPClient()

        req = HTTPRequest(url=f'{self.base_url}{url}', method='POST', headers=headers, body=body, request_timeout=120.0)
        http_resp = await http_client.fetch(request=req, raise_error=True)
        http_resp = http_resp.body.decode('utf-8')
        http_resp = json.loads(http_resp)

        http_client.close()

        return http_resp

    async def patch(self, url, headers=None, body=None):
        headers = headers if headers is not None else {}
        headers['Content-Type'] = 'application/json'
        body = json.dumps(body) if body is not None else '{}'
        http_client = AsyncHTTPClient()

        req = HTTPRequest(url=f'{self.base_url}{url}', method='PATCH', headers=headers, body=body, request_timeout=120.0)
        http_resp = await http_client.fetch(request=req, raise_error=True)
        http_resp = http_resp.body.decode('utf-8')
        http_resp = json.loads(http_resp)

        http_client.close()

        return http_resp

    async def remove(self, url, headers=None, body=None):
        headers = headers if headers is not None else {}
        headers['Content-Type'] = 'application/json'
        body = json.dumps(body) if body is not None else '{}'
        http_client = AsyncHTTPClient()

        req = HTTPRequest(url=f'{self.base_url}{url}', method='DELETE', headers=headers, body=body, request_timeout=120.0)
        http_resp = await http_client.fetch(request=req, raise_error=True)
        http_resp = http_resp.body.decode('utf-8')
        http_resp = json.loads(http_resp)

        http_client.close()

        return http_resp
