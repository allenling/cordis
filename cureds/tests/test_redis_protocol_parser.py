from cureds import redis_protocol
from cureds.tests.common_data import nested_array_resp, nested_array_result


class TestParseCommonType:
    parser = redis_protocol.RESPParser()

    def test_string(self):
        data = b'$2\r\n\\a\r\n'
        resp = self.parser.parse(data)
        assert len(resp) == 1 and resp[0] == r'\a'
        return

    def test_int(self):
        data = b':3\r\n'
        resp = self.parser.parse(data)
        assert len(resp) == 1 and resp[0] == 3
        return

    def test_none(self):
        data = b'$-1\r\n'
        resp = self.parser.parse(data)
        assert len(resp) == 1 and resp[0] is None
        return

    def test_array(self):
        data = b'*6\r\n$1\r\na\r\n$3\r\n100\r\n$1\r\nc\r\n$3\r\n101\r\n$1\r\nb\r\n$3\r\n110\r\n'
        list_data = ['a', '100', 'c', '101', 'b', '110']
        resp = self.parser.parse(data)
        assert type(resp) is list and len(resp) == 1 and len(resp[0]) == 6
        resp = resp[0]
        for i, j in zip(resp, list_data):
            assert i == j
        return

    def test_nested_array(self):
        '''
        data = GEORADIUS Sicily 15 37 200 km WITHCOORD
        '''
        data = nested_array_resp
        resp = self.parser.parse(data)
        self.check_nested_arrray(resp)
        return

    def check_nested_arrray(self, resp):
        assert type(resp) is list and len(resp) == 1 and len(resp[0]) == 2
        resp = resp[0]
        for i, j in zip(nested_array_result, resp):
            assert i[0] == j[0]
            for subi, subj in zip(i[1], j[1]):
                assert subi == subj
        return

    def test_truncated_byte1(self):
        '''
        ...\r\n$20\r\n13.36138933897018433\r\n...
        ...\r\n$20\r\n13.361389338
        '''
        data = nested_array_resp
        resp = self.parser.parse(data[:42])
        assert type(resp) is list and len(resp) == 0
        resp = self.parser.parse(data[42:])
        self.check_nested_arrray(resp)
        return

    def test_truncated_byte2(self):
        '''
        ...\r\n$20\r\n13.36138933897018433\r\n...
        ...\r\n$2
        '''
        data = nested_array_resp
        resp = self.parser.parse(data[:27])
        assert type(resp) is list and len(resp) == 0
        resp = self.parser.parse(data[27:])
        self.check_nested_arrray(resp)
        return

    def test_truncated_byte3(self):
        '''
        ...\r\n$20\r\n13.36138933897018433\r\n...
        ...\r\n$20\r
        '''
        data = nested_array_resp
        resp = self.parser.parse(data[:29])
        assert type(resp) is list and len(resp) == 0
        resp = self.parser.parse(data[29:])
        self.check_nested_arrray(resp)
        return

    def test_truncated_byte4(self):
        '''
        ...\r\n$20\r\n13.36138933897018433\r\n...
        ...\r\n$20\r\n
        '''
        data = nested_array_resp
        resp = self.parser.parse(data[:30])
        assert type(resp) is list and len(resp) == 0
        resp = self.parser.parse(data[30:])
        self.check_nested_arrray(resp)
        return

    def test_truncated_byte5(self):
        '''
        ...\r\n$20\r\n13.36138933897018433\r\n...
        ...\r\n$
        '''
        data = nested_array_resp
        resp = self.parser.parse(data[:26])
        assert type(resp) is list and len(resp) == 0
        resp = self.parser.parse(data[26:])
        self.check_nested_arrray(resp)
        return

    def test_pipeline_resp(self):
        data = b'+OK\r\n+QUEUED\r\n+QUEUED\r\n*2\r\n$1\r\n1\r\n:2\r\n'
        result = ['OK', 'QUEUED', 'QUEUED', ['1', 2]]
        resp = self.parser.parse(data)
        assert type(resp) is list and len(resp) == 4
        for i, j in zip(result, resp):
            assert i == j
        return


class TestKey:
    pass


def main():
    ts = TestParseCommonType()
    ts.test_pipeline_resp()
    return


if __name__ == '__main__':
    main()
