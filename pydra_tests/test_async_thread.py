import asyncio
import time

from pydra.async_thread import AsyncThread


def test_basic():
    global_dict = {"a": "init"}

    async def modifier(time: int, name: str) -> int:
        global_dict["a"] = name + "_start"
        await asyncio.sleep(time)
        global_dict["a"] = name + "_end"
        return time

    with AsyncThread() as at:
        assert global_dict["a"] == "init"
        res_a = at.submit(modifier(1, "a"))
        time.sleep(0.2)
        assert global_dict["a"] == "a_start"
        time.sleep(1.1)
        assert global_dict["a"] == "a_end"
    assert res_a.result() == 1


def test_submit_multiple():
    global_dict = {"a": "init"}
    start_time = time.time()

    async def modifier(time: int, name: str) -> int:
        global_dict["a"] = name + "_start"
        await asyncio.sleep(time)
        global_dict["a"] = name + "_end"
        return time

    with AsyncThread() as at:
        assert global_dict["a"] == "init"
        res_a = at.submit(modifier(5, "a"))
        res_b = at.submit(modifier(3, "b"))
        time.sleep(1)
        assert global_dict["a"] == "b_start"
    duration = time.time() - start_time
    assert 5 < duration and duration < 6
    assert global_dict["a"] == "a_end"
    assert res_a.result() == 5
    assert res_b.result() == 3