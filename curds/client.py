import curio

from curds.connection import AsyncConnection
from curds.utils import pack_command


class CurdsPipeline:
    def __init__(self, curds):
        self.curds = curds


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
        command = pack_command('GET', key)
        resp = await self.connection.send(command)
        return resp

    async def incr(self, key, count=1):
        command = pack_command('INCR', key, count)
        resp = await self.connection.send(command)
        return resp

    async def pipeline(self):
        return CurdsPipeline(self)


def main():
    '''
    for test
    '''
    return


if __name__ == '__main__':
    main()
