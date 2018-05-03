'''
redis protocol(RESP)

simple pack and parse

'''
from collections import deque

from typing import List, Any

CRLF = '\r\n'

BYTE_CRLF = b'\r\n'


def pack_comand():
    return


class RESPParser:
    '''
    parser will hold truncated response
    '''

    def __init__(self):
        self.array_stack = []
        self.last_str = None
        return

    def parse(self, bdata: bytes) -> List[Any]:
        '''
        caller should yield data itself while data too large

        example:

        for data in streamer.read(1024):
            response_list = parser.parse(data)
            for response in response_list:
                do_something(response)
        '''
        res = []
        data_str = bdata.decode('utf-8')
        if self.last_str is not None:
            data_str = self.last_str + data_str if self.last_str is not None else data_str
            self.last_str = None
        data_deq = deque(data_str.split('\r\n'))
        last_str = data_deq.pop()
        if last_str != '':
            self.last_str = last_str
        # main loop, pop string only
        while True:
            try:
                resp = data_deq.popleft()
                if resp.startswith('+') or resp.startswith('-'):
                    data = resp[1:]
                elif resp.startswith(':'):
                    self.last_str = resp
                    if len(resp) == 1:
                        break
                    data = int(resp[1:])
                    self.last_str = None
                elif resp.startswith('$'):
                    self.last_str = resp
                    if resp[1:] == '-1':
                        data = None
                    else:
                        count = int(resp[1:])
                        data = data_deq.popleft()
                        # TODO: handle exception
                        assert len(data) == count
                    self.last_str = None
                elif resp.startswith('*'):
                    self.array_stack.append([int(resp[1]), []])
                    continue
                if self.array_stack:
                    self.array_stack[-1][0] -= 1
                    self.array_stack[-1][1].append(data)
                    while True:
                        if self.array_stack[-1][0] == 0:
                            last_array = self.array_stack.pop()[1]
                            if self.array_stack:
                                self.array_stack[-1][0] -= 1
                                self.array_stack[-1][1].append(last_array)
                                continue
                            else:
                                res.append(last_array)
                                self.array_stack = []
                                break
                        break
                else:
                    res.append(data)
            except IndexError:
                break
        return res


def main():
    resps = b'$1\r\n1\r\n$1\r\n2\r\n:4\r\n$6\r\naadata\r\n*4\r\n$1\r\n8\r\n$1\r\n7\r\n$1\r\n6\r\n$1\r\n5\r\n'
    resp_parser = RESPParser()
    x = resp_parser.parse(resps)
    print(x)
    return


if __name__ == '__main__':
    main()
