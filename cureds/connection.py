from collections import deque
from concurrent.futures import Future

import curio
from curio.traps import _future_wait
from curio import Queue

from cureds import utils
from cureds.redis_protocol import pack_redis_command, pack_redis_pipeline, RESPParser, RESP_CALLBACK


CONNECTION_STATUS = {'initial': 0, 'pending': 1, 'connected': 2}


class AsyncConnectionError(Exception):
    pass


class AsyncConnection:
    SOCK_READ_SIZE = 1024

    def __init__(self, host='127.0.0.1', port=6379, read_size=1024):
        self.host, self.port = host, port
        self.status = CONNECTION_STATUS['initial']
        self._buffer = []
        self._send_queue = Queue()
        self._future_deque = deque()
        self.parser = RESPParser()
        # last_multi = {'count': count, 'cmd_name': cmd_name, 'future': future, 'data': data}
        self.last_multi = {}
        self.SOCK_READ_SIZE = read_size
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
        cmd_byte = pack_redis_command([cmd])[0]
        await self._send_queue.put((cmd_byte, cmd_name, future))
        # wait for future notified
        await _future_wait(future)
        return future.result()

    async def send_pipeline(self, *cmd):
        future = Future()
        cmd_names = ','.join(['MULTI'] + [i[0] for i in cmd])
        cmd_byte_list = pack_redis_pipeline(*cmd)
        cmd_bytes = b''.join(cmd_byte_list)
        await self._send_queue.put((cmd_bytes, cmd_names, future))
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
        op = False
        for resp in resps_iter:
            op = True
            if resp == 'QUEUED':
                self.last_multi['count'] += 1
                continue
            if self.last_multi['count'] != len(resp):
                # watch return *-1
                assert type(resp) is list and len(resp) == 0
            self.last_multi['count'] = 0
            self.last_multi['data'] = resp
            break
        if op is True and self.last_multi['count'] == 0:
            f = self.last_multi['future']
            clean_data = []
            # clean multi data
            for cname, d in zip(self.last_multi['cmd_name'], self.last_multi['data']):
                cdata = self.clean_resp(cname, d)
                clean_data.append(cdata)
            f.set_result(clean_data)
            self.last_multi = {}
        return

    def clean_resp(self, cmd_name, resp):
        callback = RESP_CALLBACK.get(cmd_name, None)
        if callback is not None:
            resp = callback(resp)
        return resp

    async def _wait_recv(self):
        '''
        handle pipeline response
        '''
        while True:
            resp_bytes = await self.sock.recv(self.SOCK_READ_SIZE)
            resps = self.parser.parse(resp_bytes)
            if not resps:
                continue
            resps_iter = iter(resps)
            if self.last_multi:
                self.handle_pipeline_resp(resps_iter)
            for resp in resps_iter:
                cmd_name, f = self._future_deque.popleft()
                if cmd_name.startswith('MULTI'):
                    # we meet a pipeline, starts with OK
                    assert len(self.last_multi) == 0
                    assert resp == 'OK'
                    self.last_multi = {'count': 0, 'data': [], 'cmd_name': cmd_name.split(',')[1:], 'future': f}
                    self.handle_pipeline_resp(resps_iter)
                else:
                    resp = self.clean_resp(cmd_name, resp)
                    f.set_result(resp)
        return


async def test_async_connection():
    ac = AsyncConnection()
    await ac.connect()
    res = await ac.send_command('GET', 'b')
    print(res)
    res = await ac.send_pipeline(['SET', 'a', 2], ['GET', 'a'], ['INCR', 'a'])
    print(res)
    return


def main():
    '''
    for test
    '''
    curio.run(test_async_connection)
    return


if __name__ == '__main__':
    main()
