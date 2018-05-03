from redis.connection import Token, SYM_EMPTY, SYM_STAR, SYM_CRLF, SYM_DOLLAR
from redis._compat import b as rcb, imap


class ParseResponseError(Exception):
    pass


def encode(value):
    if isinstance(value, Token):
        return rcb(value.value)
    elif isinstance(value, bytes):
        return value
    elif isinstance(value, (int)):
        value = rcb(str(value))
    elif isinstance(value, float):
        value = rcb(repr(value))
    elif isinstance(value, str):
        value = value.encode('utf-8')
    return value


def pack_command(*args):
    output = []
    command = args[0]
    if ' ' in command:
        args = tuple([Token(s) for s in command.split(' ')]) + args[1:]
    else:
        args = (Token(command),) + args[1:]

    buff = SYM_EMPTY.join(
        (SYM_STAR, rcb(str(len(args))), SYM_CRLF))

    for arg in imap(encode, args):
        # to avoid large string mallocs, chunk the command into the
        # output list if we're sending large values
        if len(buff) > 6000 or len(arg) > 6000:
            buff = SYM_EMPTY.join(
                (buff, SYM_DOLLAR, rcb(str(len(arg))), SYM_CRLF))
            output.append(buff)
            output.append(arg)
            buff = SYM_CRLF
        else:
            buff = SYM_EMPTY.join((buff, SYM_DOLLAR, rcb(str(len(arg))),
                                   SYM_CRLF, arg, SYM_CRLF))
    output.append(buff)
    return output


def parse_redis_resp(redis_resp):
    return


async def wait_drain_curio_queue(curio_que):
    '''
    get all data of curio queue once
    return: list
    '''
    res = []
    data = await curio_que.get()
    res.append(data)
    if curio_que.empty() is False:
        for d in curio_que._queue:
            res.append(d)
        curio_que._task_count = 0
        curio_que._queue.clear()
    return res


def main():
    '''
    for test
    '''
    cmds = [['GET', 'a'], ['GET', 'b'], ['LRANGE', 'mlist', 0, -1],
            ['HMGET', 'mhash', 'name', 'height'],
            ['LLEN', 'mlist'],
            ['GET', 'aa']
            ]
    for cmd in cmds:
        cmd_data = pack_command(*cmd)
        print(cmd_data[0])
#     res = b'$1\r\n1\r\n$1\r\n2\r\n*4\r\n$1\r\n8\r\n$1\r\n7\r\n$1\r\n6\r\n$1\r\n5\r\n'
#     print(parse_redis_resp(res))
    return


if __name__ == '__main__':
    main()
