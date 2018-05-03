from curds import redis_protocol


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
        data = b'*2\r\n*2\r\n$7\r\nPalermo\r\n*2\r\n$20\r\n13.36138933897018433\r\n$20\r\n38.11555639549629859\r\n*2\r\n$7\r\nCatania\r\n*2\r\n$20\r\n15.08726745843887329\r\n$20\r\n37.50266842333162032\r\n'
        list_data = [['Palermo', ['13.36138933897018433', '38.11555639549629859']], ['Catania', ['15.08726745843887329', '37.50266842333162032']]]
        resp = self.parser.parse(data)
        assert type(resp) is list and len(resp) == 1 and len(resp[0]) == 2
        resp = resp[0]
        for i, j in zip(list_data, resp):
            assert i[0] == j[0]
            for subi, subj in zip(i[1], j[1]):
                assert subi == subj
        return


class TestKey:
    pass


def main():
    ts = TestParseCommonType()
    ts.test_string()
    return


if __name__ == '__main__':
    main()
