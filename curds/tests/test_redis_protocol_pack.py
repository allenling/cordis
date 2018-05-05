from curds.redis_protocol import pack_redis_command, pack_redis_pipeline


class TestPackCmd:

    def test_pack_get(self):
        cmds = [['get', 'a']]
        data = pack_redis_command(cmds)
        assert type(data) is list and len(data) == 1 and data[0] == b'*2\r\n$3\r\nGET\r\n$1\r\na\r\n'
        return

    def test_pack_set(self):
        cmds = [['set', 'a', 1]]
        data = pack_redis_command(cmds)
        assert type(data) is list and len(data) == 1 and data[0] == b'*3\r\n$3\r\nSET\r\n$1\r\na\r\n$1\r\n1\r\n'
        return

    def test_pack_multi_cmds(self):
        cmds = [['multi'], ['set', 'a', 1], ['incr', 'a'], ['get', 'a'], ['exec']]
        data = pack_redis_command(cmds)
        assert type(data) is list and len(data) == 5
        assert b''.join(data) == b'*1\r\n$5\r\nMULTI\r\n*3\r\n$3\r\nSET\r\n$1\r\na\r\n$1\r\n1\r\n*2\r\n$4\r\nINCR\r\n$1\r\na\r\n*2\r\n$3\r\nGET\r\n$1\r\na\r\n*1\r\n$4\r\nEXEC\r\n'
        return

    def test_pack_pipeline(self):
        cmds = [['set', 'a', 1], ['incr', 'a'], ['get', 'a']]
        data = pack_redis_pipeline(*cmds)
        assert type(data) is list and len(data) == 5
        assert b''.join(data) == b'*1\r\n$5\r\nMULTI\r\n*3\r\n$3\r\nSET\r\n$1\r\na\r\n$1\r\n1\r\n*2\r\n$4\r\nINCR\r\n$1\r\na\r\n*2\r\n$3\r\nGET\r\n$1\r\na\r\n*1\r\n$4\r\nEXEC\r\n'
        return


def main():
    tps = TestPackCmd()
    tps.test_pack_multi_cmds()
    return


if __name__ == '__main__':
    main()
