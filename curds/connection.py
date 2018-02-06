from collections import deque
from concurrent.futures import Future

import curio
from curio.traps import _future_wait
from curio import Queue


class AsyncConnection:

    def __init__(self):
        self._buffer = []
        self._send_queue = Queue()
        self._future_deque = deque()
        return

    async def connect(self):
        # TODO: connect redis server
        self._wait_send_task = await curio.spawn(self._wait_send, daemon=True)
        self._wait_recv_task = await curio.spawn(self._wait_recv, daemon=True)
        return

    async def close(self):
        return

    async def send(self, data):
        future = Future()
        self._future_deque.append(future)
        await self._send_queue.put(data)
        # wait for future notified
        await _future_wait(future)
        return future.result()

    async def _wait_send(self):
        while True:
            # send command one by one, good enough?
            # TODO: drain _send_queue data
            data = await self._send_queue.get()
            await self.sock.send_all(data)
        return

    async def _wait_recv(self):
        while True:
            resps = await self.sock.read()
            # TODO: unpack_response
            for resp in resps:
                f = self._future_deque.popleft()
                # do not need await
                # other side, __future_await__ is fine
                f.set_result(resp)
        return


def main():
    '''
    for test
    '''
    return


if __name__ == '__main__':
    main()
