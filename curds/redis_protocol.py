'''
redis protocol(RESP)

simple pack and parse

'''

from collections import deque

from typing import List, Any, Dict

CRLF = '\r\n'

BYTE_CRLF = b'\r\n'


def resp_ok_to_bool(resp: str) -> bool:
    '''
    OK     -> True
    others -> False
    '''
    return True if resp == 'OK' else False


def resp_list_to_dict(resp: List) -> Dict[str, str]:
    '''
    [key1, value1, key2, value2, ...] -> {key1: value1, key2: value2, ...}
    '''
    len_resp = len(resp)
    # even len
    assert len_resp % 2 == 0
    iter_resp = iter(resp)
    clean_list = [(i, next(iter_resp)) for i in iter_resp]
    clean_dict = dict(clean_list)
    return clean_dict


def pack_redis(cmds: List[List[str]]) -> List[bytes]:
    '''
    cmds = [[cmd1, arg1, ...], ...]
    '''
    result = []
    for cmd in cmds:
        array_len = str(len(cmd))
        cmd_name = str(cmd[0]).upper()
        cmd_name_len = len(cmd_name)
        cmd_str = ['*%s' % array_len, '$%s' % cmd_name_len, cmd_name]
        for arg in cmd[1:]:
            arg_str = str(arg)
            arg_len = len(arg_str)
            cmd_str.extend(['$%s' % arg_len, arg_str])
        cmd_str.append('')
        cmd_byte = CRLF.join(cmd_str).encode()
        result.append(cmd_byte)
    return result


class RESPParser:
    '''
    parser will hold truncated response stream
    '''

    def __init__(self):
        self.array_stack = []
        self.last_str = deque([])
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
        if self.last_str:
            deq_str = ''.join(self.last_str)
            data_str = deq_str + data_str
            self.last_str = deque([])
        data_deq = deque(data_str.split(CRLF))
        truncated_str = data_deq.pop()
        if truncated_str != '':
            self.last_str.append(truncated_str)
        # main loop, pop string only
        while True:
            try:
                resp = data_deq.popleft()
                if resp.startswith('+') or resp.startswith('-'):
                    data = resp[1:]
                elif resp.startswith(':'):
                    self.last_str.appendleft(resp)
                    if len(resp) == 1:
                        break
                    data = int(resp[1:])
                    self.last_str.popleft()
                elif resp.startswith('$'):
                    if resp[1:] == '-1':
                        data = None
                    else:
                        count = int(resp[1:])
                        try:
                            data = data_deq.popleft()
                            # TODO: handle assert exception?
                            assert len(data) == count
                        except IndexError:
                            # last string
                            self.last_str.extendleft([CRLF, resp])
                            break
                elif resp.startswith('*'):
                    self.array_stack.append([int(resp[1]), []])
                    continue
                # handle nested array
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
