
import asyncio
import time


class ScheduleTask:
    def __init__(self, task_id, context, start, stop=None):
        self._name = task_id
        self._context = context
        self._start = start
        self._stop = stop
        self._task = asyncio.ensure_future(self._job())

    async def _job(self):
        await self._start(self._name, self._context, self)

    def cancel(self):
        print('cancel task: ', self._name)
        if self._stop:
            self._stop(self._name, self._context, self)
        self._task.cancel()
        print('cancel done: ')


class Timer:
    def __init__(self, delay, interval, timer_name, context, callback):
        self._interval = interval
        self._name = timer_name
        self._context = context
        self._callback = callback
        # self._is_first_call = True
        self._task = None
        self._ok = True
        asyncio.get_event_loop().call_later(delay, self.start)
        print(timer_name + " init done")

    def start(self):
        self._task = asyncio.ensure_future(self._job())

    async def _job(self):
        try:

            # while self._ok:
            #     t1 = time.time()
            #     await self._callback(self._name, self._context, self)
            #     t2 = time.time()
            #     sleep_time = self._interval - (t2 - t1)
            #     if sleep_time < 0:
            #         sleep_time = 0
            #     await asyncio.sleep(sleep_time)

            sleep_interval = 5
            remaining_time = 0

            while self._ok:
                if remaining_time <= 0:
                    t1 = time.time()
                    await self._callback(self._name, self._context, self)
                    t2 = time.time()

                    remaining_time = self._interval - (t2 - t1)
                    if remaining_time < 0:
                        remaining_time = 0

                else:
                    remaining_time -= sleep_interval

                await asyncio.sleep(sleep_interval)

        except Exception as ex:
            print(ex)

    def cancel(self):
        self._ok = False
        if self._task is not None:
            self._task.cancel()
