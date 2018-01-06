curds
=========

curio redis


模型
--------------

如何读写
~~~~~~~~~~

多个coroutine同时recv是不好的, 如果一次recv了多个命令的返回, 丢弃还是? 并且curio中会报read busy异常

然后一般多个线程读取同一个socket的话是加锁, 一般的做法是加锁, 拿锁, send, recv, 解锁

但是这样就限制了一次只能send一次, recv一次, 浪费recv的size大小, 比如每次recv都只能拿到1kb, 就是send不加锁,
recv加锁, 如果recv一次拿到了多个命令返回, 那么当前的coroutine需要唤醒其他coroutine, 通知它们结果已经回来了么, 还是丢弃?

可以spawn一个专门recv的corotine, 这样send不受限制, 然后可以一次拿到多个命令的返回:

1. 每次send之前, 把自己的event加入带等待唤醒的queue中(加入list不太好?), 然后send, 然后等待event被唤醒

   .. code-block:: python

       ev, ev_id = get_ev()
       await ev_queue.put((ev_id, ev))
       await send(cmd)
       # 等待event
       await ev.wait()

2. 然后当调度到recv的时候, 有可能recv多个命令的返回:

   .. code-block:: python

       # 以resps的长度为准, 因为担心有可能有一个coroutine发送了命令, 但是这一次的recv没有获取到, 此时ev_queue的长度就大于resps
       while resps:
           for resp in resps:
               # 拿到event的对象和id
               ev, ev_id = ev_queue.get
               # 存储结果
               res[ev_id] = resp
               # 唤醒event
               await ev.set()

3. event受信, 那么说明结果返回了

   .. code-block:: python

       await ev.wait()
       res = res[ev_id]
       del res[ev_id]

该任务最好设置为daemon, 因为我们没办法去主动join它(在__del__中join?), 然后curio结束的时候, 此时该任务

是非daemon, 并且没有被cancel, 没有join的, 所以会报never joined的warning

