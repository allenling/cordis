######
cureds
######

Async(Curio) Redis Client

learning from `redis-py <https://github.com/andymccurdy/redis-py>`_

Usage
=========

.. code-block:: python

    async def test_client():
        # new client instance
        client = CuredsClient()

        # wait connection
        await client.connect()

        # send commands
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

        # use pipeline
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
        curio.run(test_client())
        return

How it works
================


NOTES
==========

1. SELECT: Not implemented, see redis-py`s doc

2. DEL: 'del' replace by delete, see redis-py`s doc

pack/parse
-------------

simple pack and parse layer, and you can use pack/parse module standalone.

no recursion, just iteration in parser, easy to use.

.. code-block:: python

    In [1]: from cureds import redis_protocol
    
    In [2]: redis_protocol.pack_redis_command([['get', 'a']])
    Out[2]: [b'*2\r\n$3\r\nGET\r\n$1\r\na\r\n']
    
    In [3]: redis_protocol.pack_redis_command([['incr', 'a']])
    Out[3]: [b'*2\r\n$4\r\nINCR\r\n$1\r\na\r\n']
    
    In [4]: redis_protocol.pack_redis_pipeline(['GET', 'a'], ['INCR', 'a'])
    Out[4]: 
    [b'*1\r\n$5\r\nMULTI\r\n',
     b'*2\r\n$3\r\nGET\r\n$1\r\na\r\n',
     b'*2\r\n$4\r\nINCR\r\n$1\r\na\r\n',
     b'*1\r\n$4\r\nEXEC\r\n']
    
    In [5]: response = b'*6\r\n$1\r\na\r\n$3\r\n100\r\n$1\r\nc\r\n$3\r\n101\r\n$1\r\nb\r\n$3\r\n110\r\n'
    
    In [6]: parser = redis_protocol.RESPParser()
    
    In [7]: parser.parse(response)
    Out[7]: [['a', '100', 'c', '101', 'b', '110']]

and, combined with socket:

.. code-block:: python

    parser = redis_protocol.RESPParser()
    
    for data in sock.read(1024):
    
        resps = parser.parse(data)
    
        for resp in resps:
    
            do_something(resp)


Connection/WATCH
--------------------

What if there are many tasks sending *watch* ?

Thinking about many threads sending *watch* first.

process p1 create two threads, thread1 and thread2. and another process p2 create one thread, thread3.

1. thread1, watch a

2. thread3(p2), incr a

3. thread2, multi, incr b, exec, fail!!!!

4. thread1, multi, ..., exec, success!!!

In redis-py, there is a connection pool, and if there is no any avaliable connection, it will create a new connection.

So, redis-py will create a new connection for thread2, because thread1 do not release old connection yet

So, *watch a* in thread1 would have no effect on *multi* in thread2 when thread3 modify watched key(sending *incr a*)

But, should we create new connection for every task?

Consider that we would have hundreds, maybe thousands, tasks in our async app, creating new connection for every task is a good idea?


TODO
======


