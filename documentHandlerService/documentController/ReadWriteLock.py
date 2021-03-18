import threading


class ReadWriteLock:
    """ A lock object that allows many simultaneous "read locks", but
    only one "write lock." """

    # def __init__(self):
    #     self._read_ready = threading.Condition(threading.Lock())
    #     self._readers = 0
    #
    # def acquire_read(self):
    #     """ Acquire a read lock. Blocks only if a thread has
    #     acquired the write lock. """
    #     self._read_ready.acquire()
    #     try:
    #         self._readers += 1
    #     finally:
    #         self._read_ready.release()
    #
    # def release_read(self):
    #     """ Release a read lock. """
    #     self._read_ready.acquire()
    #     try:
    #         self._readers -= 1
    #         if not self._readers:
    #             self._read_ready.notifyAll()
    #     finally:
    #         self._read_ready.release()
    #
    # def acquire_write(self):
    #     """ Acquire a write lock. Blocks until there are no
    #     acquired read or write locks. """
    #     self._read_ready.acquire()
    #     while self._readers > 0:
    #         self._read_ready.wait()
    #
    # def release_write(self):
    #     """ Release a write lock. """
    #     self._read_ready.release()

    def __init__(self):
        self.rwlock = 0
        self.writers_waiting = 0
        self.monitor = threading.Lock()
        self.readers_ok = threading.Condition(self.monitor)
        self.writers_ok = threading.Condition(self.monitor)

    def acquire_read(self):
        """Acquire a read lock. Several threads can hold this typeof lock.
        It is exclusive with write locks."""
        self.monitor.acquire()
        while self.rwlock < 0 or self.writers_waiting:
            self.readers_ok.wait()
        self.rwlock += 1
        self.monitor.release()

    def acquire_write(self):
        """Acquire a write lock. Only one thread can hold this lock, and
    only when no read locks are also held."""
        self.monitor.acquire()
        while self.rwlock != 0:
            self.writers_waiting += 1
            self.writers_ok.wait()
            self.writers_waiting -= 1
        self.rwlock = -1
        self.monitor.release()

    def release(self):
        """Release a lock, whether read or write."""
        self.monitor.acquire()
        if self.rwlock < 0:
            self.rwlock = 0
        else:
            self.rwlock -= 1
        wake_writers = self.writers_waiting and self.rwlock == 0
        wake_readers = self.writers_waiting == 0
        self.monitor.release()
        if wake_writers:
            self.writers_ok.acquire()
            self.writers_ok.notify()
            self.writers_ok.release()
        elif wake_readers:
            self.readers_ok.acquire()
            self.readers_ok.notifyAll()
            self.readers_ok.release()
