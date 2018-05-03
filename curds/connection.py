from collections import deque
from concurrent.futures import Future

import curio
from curio.traps import _future_wait
from curio import Queue

from curds import utils


CONNECTION_STATUS = {'initial': 0, 'pending': 1, 'connected': 2}

SOCK_READ_SIZE = 1024


class AsyncConnectionError(Exception):
    pass


class AsyncConnection:

    def __init__(self, host='127.0.0.1', port=6379):
        self.host, self.port = host, port
        self.status = CONNECTION_STATUS['initial']
        self._buffer = []
        self._send_queue = Queue()
        self._future_deque = deque()
        return

    async def connect(self):
        if self.status == CONNECTION_STATUS['pending']:
            raise AsyncConnectionError('already in connecting status!')
        self.status = CONNECTION_STATUS['pending']
        connect_task = await curio.spawn(curio.open_connection, self.host, self.port)
        self.sock = await connect_task.join()
        self.status = CONNECTION_STATUS['connected']
        self._wait_send_task = await curio.spawn(self._wait_send, daemon=True)
        self._wait_recv_task = await curio.spawn(self._wait_recv, daemon=True)
        return

    async def close(self):
        return

    async def send(self, data):
        future = Future()
        await self._send_queue.put((data, future))
        # wait for future notified
        await _future_wait(future)
        return future.result()

    async def _wait_send(self):
        while True:
            data_fus = await utils.wait_drain_curio_queue(self._send_queue)
            for data, future in data_fus:
                self._future_deque.append(future)
                await self.sock.sendall(data)
        return

    async def _wait_recv(self):
        while True:
            resps = await self.sock.recv(2048)
            f = self._future_deque.popleft()
            f.set_result(resps)
            continue
            # TODO: unpack_response
            for resp in resps:
                f = self._future_deque.popleft()
                # do not need await
                # other side, __future_await__ is fine
                f.set_result(resp)
        return


async def test_async_connection():
    ac = AsyncConnection()
    await ac.connect()
    cmds = [['GET', 'none'],
            ['INCR', 'intkey'],
            ['GET', 'a'], ['GET', 'b'], ['LRANGE', 'mlist', 0, -1],
            ['HMGET', 'mhash', 'name', 'height'],
            ['HGETALL', 'mobj'],
            ['MULTI'],
            ['LLEN', 'mlist'],
            ['GET', 'a'],
            ['EXEC'],
            ['ZRANGE', 'mss', 0, -1, 'withscores'],
            ['GEORADIUS', 'Sicily', 15, 37, 200, 'km', 'WITHCOORD']
            ]
    for cmd in cmds:
        cmd_data = utils.pack_command(*cmd)
        print(cmd_data)
        res = await ac.send(cmd_data[0])
        print(res)
        print('---------------')
    pipeline_cmd = b'*1\r\n$5\r\nMULTI\r\n*2\r\n$3\r\nGET\r\n$1\r\na\r\n*2\r\n$4\r\nLLEN\r\n$5\r\nmlist\r\n*1\r\n$4\r\nEXEC\r\n'
    res = await ac.send(pipeline_cmd)
    print(res)
    return


def main():
    '''
    for test
    '''
    import redis
    redis.StrictRedis
    curio.run(test_async_connection)
    return


if __name__ == '__main__':
    main()
