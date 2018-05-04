import curio

from curds.connection import AsyncConnection


class Curds:

    def __init__(self):
        return

    async def connect(self):
        self.connection = AsyncConnection()
        # wait connect done!
        con_task = await curio.spawn(self.connection.connect)
        await con_task.join()
        return

    async def get(self, key):
        resp = await self.connection.send_command('GET', key)
        return resp

    async def set(self, key, value):
        resp = await self.connection.send_command('SET', key, value)
        resp = True if resp == 'OK' else False
        return resp

    async def incr(self, key):
        resp = await self.connection.send_command('INCR', key)
        return resp

    async def incr_by(self, key, amount=1):
        resp = await self.connection.send_command('INCRBY', key, amount)
        return resp

    async def hset(self, key, field, value):
        resp = await self.connection.send_command('HSET', key, field, value)
        return resp

    async def hgetall(self, key):
        resp = await self.connection.send_command('HGETALL', key)
        len_resp = len(resp)
        # even len
        assert len_resp % 2 == 0
        iter_resp = iter(resp)
        clean_list = [(i, next(iter_resp)) for i in iter_resp]
        clean_dict = dict(clean_list)
        return clean_dict


async def test_client():
    cclient = Curds()
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
    return


def main():
    '''
    for test
    '''
    curio.run(test_client())
    return


if __name__ == '__main__':
    main()
