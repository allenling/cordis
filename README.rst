#####
curds
#####

curio redis client

learn from `redis-py <https://github.com/andymccurdy/redis-py>`_

Usage
=========

.. code-block:: python

    async def test_client():
        client = CurdsClient()
        await client.connect()
        data = await client.set('a', 1)
        print(data)
        for _ in range(10):
            data = await client.incr('a')
            print('incr:', data)
            data = await client.get('a')
            print('get:', data)
        data = await client.hset('client_hash', 'first_name', 'allen')
        print(data)
        data = await client.hset('client_hash', 'last_name', 'ling')
        print(data)
        data = await client.hgetall('client_hash')
        print(data)
        with client.pipeline() as p:
            p.set('a', 1)
            p.get('a')
            p.incr('a')
            p.hgetall('client_hash')
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

TODO
======

1. more redis command implementation

2. more test

