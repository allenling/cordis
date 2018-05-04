
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
    return


if __name__ == '__main__':
    main()
