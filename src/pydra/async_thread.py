import asyncio
import threading
from collections.abc import Coroutine
from concurrent.futures import Future
from typing import Self


class AsyncThread:
    """ Context manager that enables running of async coroutines in sync code 

    It works by starting a worker threads which has its own event loop.
    The coruotines are then simply scheduled on that thread.
    This solves the cases of "OHH, I just want to run a bit of async in my sync code".
    """
    def __init__(self):
        self.loop: asyncio.AbstractEventLoop | None = None
        self.thread: threading.Thread | None = None

    def __enter__(self) -> Self:
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        # Wait until loop is set
        while self.loop is None:
            pass
        return self

    def _run_loop(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.loop = loop
        # Run unitl `stop` is called
        loop.run_forever()

        pending = asyncio.all_tasks(loop)
        if pending:
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        loop.close()

    def submit[T](self, coro: Coroutine[None, None, T]) -> Future[T]:
        """Submit coroutine to the background loop."""
        if self.loop is None:
            raise RuntimeError("Event loop not started yet")
        return asyncio.run_coroutine_threadsafe(coro, self.loop)

    def __exit__(self, exc_type, exc, tb):
        # Stop the loop gracefully
        if self.loop is not None:
            self.loop.call_soon_threadsafe(self.loop.stop)
        if self.thread is not None:
            self.thread.join()

