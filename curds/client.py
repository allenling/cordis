import curio

from curds.connection import AsyncConnection
from curds.redis_protocol import resp_ok_to_bool, resp_list_to_dict

RESP_CALLBACK = {'SET': resp_ok_to_bool,
                 'HGETALL': resp_list_to_dict,
                 }


class RedisAuthError(Exception):
    pass


class SelectDBError(Exception):
    pass


class CurdsClient:

    def __init__(self, host='127.0.0.1', port=6379, db=0, password=None, read_size=1024):
        self.host, self.port = host, port
        self.db, self.password = db, password
        self.read_size = read_size
        return

    async def connect(self):
        self.connection = AsyncConnection(self.host, self.port, self.read_size)
        # wait connect done!
        con_task = await curio.spawn(self.connection.connect)
        await con_task.join()
        # send auth command
        if self.password is not None:
            resp = await self.auth(self.password)
            if resp != 'OK':
                raise RedisAuthError(resp)
        # send select command
        if self.db > 0:
            resp = await self.select(self.db)
            if resp != 'OK':
                raise SelectDBError(resp)
        return

    async def execute_command(self, *cmd):
        cmd_name = cmd[0]
        resp = await self.connection.send_command(*cmd)
        callback = RESP_CALLBACK.get(cmd_name, None)
        if callback is not None:
            resp = callback(resp)
        return resp

    async def auth(self, password):
        '''
        auth password
        '''
        resp = await self.execute_command('AUTH', password)
        return resp

    async def select(self, db_name):
        '''
        select db
        '''
        resp = await self.execute_command('SELECT', db_name)
        return resp

    async def get(self, key):
        resp = await self.execute_command('GET', key)
        return resp

    async def set(self, key, value):
        resp = await self.execute_command('SET', key, value)
        return resp

    async def incr(self, key):
        resp = await self.execute_command('INCR', key)
        return resp

    async def incr_by(self, key, amount=1):
        resp = await self.execute_command('INCRBY', key, amount)
        return resp

    async def hset(self, key, field, value):
        resp = await self.execute_command('HSET', key, field, value)
        return resp

    async def hgetall(self, key):
        resp = await self.execute_command('HGETALL', key)
        return resp

    def pipeline(self):
        return CurdsPipeline(self.connection)


class CurdsPipeline(CurdsClient):
    '''
    duplicate define redis operation, what should we do?
    '''

    def __init__(self, connection):
        self.connection = connection
        self.cmds = []
        return

    def execute_command(self, *cmd):
        self.cmds.append(cmd)
        return self

    def get(self, key):
        resp = self.execute_command('GET', key)
        return resp

    def set(self, key, value):
        resp = self.execute_command('SET', key, value)
        return resp

    def incr(self, key):
        resp = self.execute_command('INCR', key)
        return resp

    def incr_by(self, key, amount=1):
        resp = self.execute_command('INCRBY', key, amount)
        return resp

    def hset(self, key, field, value):
        resp = self.execute_command('HSET', key, field, value)
        return resp

    def hgetall(self, key):
        resp = self.execute_command('HGETALL', key)
        return resp

    async def execute(self):
        resps = await self.connection.send_pipeline(*self.cmds)
        clean_resp = []
        for cmd, resp in zip(self.cmds, resps):
            callback = RESP_CALLBACK.get(cmd[0], None)
            if callback is None:
                clean_resp.append(resp)
            else:
                clean_resp.append(callback(resp))
        return clean_resp

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        del self.connection
        self.cmds = []
        return


async def test_client():
    cclient = CurdsClient(read_size=10)
    await cclient.connect()
    data = await cclient.set('a', 1)
    print(data)
    for _ in range(10):
        data = await cclient.incr('a')
        print('incr:', data)
        data = await cclient.get('a')
        print('get:', data)
    data = await cclient.hset('cclient_hash', 'first_name', 'allen')
    print(data)
    data = await cclient.hset('cclient_hash', 'last_name', 'ling')
    print(data)
    data = await cclient.hgetall('cclient_hash')
    print(data)
    with cclient.pipeline() as p:
        p.set('a', 1)
        p.get('a')
        p.incr('a')
        p.hgetall('cclient_hash')
        p.get('a')
        res = await p.execute()
    print(res)
    return


def main():
    '''
    for test
    '''
    curio.run(test_client())
    return


if __name__ == '__main__':
    main()
