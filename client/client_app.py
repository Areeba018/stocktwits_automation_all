import time


class ClientApplication:

    def __init__(self):

        pass

    async def send_request(self, user, end_point, method='POST', body=None):

        t1 = time.time()

        resp = None

        try:
            if method == 'GET':
                resp = await user.client.get(end_point, headers=user.headers, params=body)
            elif method == 'POST':
                resp = await user.client.post(end_point, headers=user.headers, body=body)
            elif method == 'PATCH':
                resp = await user.client.patch(end_point, headers=user.headers, body=body)
            elif method == 'DELETE':
                resp = await user.client.remove(end_point, headers=user.headers, body=body)

        except Exception as ex:
            print(f'api error: ({end_point})', ex)

        t2 = time.time()

        duration = t2 - t1
        print(f'{end_point} -> {round(duration * 1000, 3)} ms')

        return resp
