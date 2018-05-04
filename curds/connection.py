from collections import deque
from concurrent.futures import Future

import curio
from curio.traps import _future_wait
from curio import Queue

from curds import utils
from curds.redis_protocol import pack_redis, RESPParser


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
        self.parser = RESPParser()
        # last_multi = {'count': count, 'future': future, 'data': data}
        self.last_multi = {}
        return

    async def connect(self):
        if self.status == CONNECTION_STATUS['pending']:
            raise AsyncConnectionError('already pending! please check out what happen in last connection')
        self.status = CONNECTION_STATUS['pending']
        connect_task = await curio.spawn(curio.open_connection, self.host, self.port)
        self.sock = await connect_task.join()
        self.status = CONNECTION_STATUS['connected']
        self._wait_send_task = await curio.spawn(self._wait_send, daemon=True)
        self._wait_recv_task = await curio.spawn(self._wait_recv, daemon=True)
        return

    async def close(self):
        return

    async def send_command(self, *cmd):
        future = Future()
        cmd_name = cmd[0]
        cmd_byte = pack_redis([cmd])[0]
        await self._send_queue.put((cmd_byte, cmd_name, future))
        # wait for future notified
        await _future_wait(future)
        return future.result()

    async def send_pipeline(self, *cmd):
        future = Future()
        cmd_byte_list = pack_redis([['multi'], *cmd, ['exec']])
        cmd_bytes = b''.join(cmd_byte_list)
        await self._send_queue.put((cmd_bytes, 'multi', future))
        # wait for future notified
        await _future_wait(future)
        return future.result()

    async def _wait_send(self):
        while True:
            data_futures = await utils.wait_drain_curio_queue(self._send_queue)
            for data, cmd_name, future in data_futures:
                self._future_deque.append([cmd_name, future])
                await self.sock.sendall(data)
        return

    def handle_pipeline_resp(self, resps_iter):
        assert self.last_multi
        for resp in resps_iter:
            if resp == 'QUEUED':
                self.last_multi['count'] += 1
                continue
            self.last_multi['count'] -= 1
            self.last_multi['data'].append(resp)
            if self.last_multi['count'] == 0:
                break
        if self.last_multi['count'] == 0:
            f = self.last_multi['future']
            f.set_result()
            self.last_multi = {}
        return

    async def _wait_recv(self):
        '''
        handle pipeline response
        '''
        while True:
            resp_bytes = await self.sock.recv(SOCK_READ_SIZE)
            resps = self.parser.parse(resp_bytes)
            resps_iter = iter(resps)
            if self.last_multi:
                self.handle_pipeline_resp(resps_iter)
            for resp in resps:
                cmd_name, f = self._future_deque.popleft()
                if cmd_name == 'MULTI':
                    # we meet a pipeline, starts with OK
                    assert len(self.self.last_multi) == 0
                    assert resp == 'OK'
                    self.last_multi = {'count': 0, 'data': [], 'future': f}
                    self.handle_pipeline_resp(resps_iter)
                else:
                    f.set_result(resp)
        return


async def test_async_connection():
    ac = AsyncConnection()
    await ac.connect()
    await ac.sock.sendall(b'*1\r\n$5\r\nMULTI\r\n*2\r\n$3\r\nGET\r\n$1\r\na\r\n*2\r\n$4\r\nINCR\r\n$1\r\na\r\n*1\r\n$4\r\nEXEC\r\n')
    res = await ac.sock.recv(1024)
    parser = RESPParser()
    data = parser.parse(res)
    print(data)
    return


def main():
    '''
    for test
    '''
    curio.run(test_async_connection)
    return


if __name__ == '__main__':
    main()
