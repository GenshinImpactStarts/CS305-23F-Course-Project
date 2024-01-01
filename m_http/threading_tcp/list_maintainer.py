from threading import Thread, Condition

__all__ = 'ListMaintainer'


class ListMaintainer:
    def __init__(self, list_to_maintain, list_lock):
        self.__tasks = []
        self.__running = True
        self.__list_to_maintain = list_to_maintain
        self.__list_lock = list_lock
        self.__maintainer_cv = Condition()
        self.__maintainer_thread = None

    def start(self):
        def __start():
            while self.__running:
                # block when have no task
                with self.__maintainer_cv:
                    if len(self.__tasks) == 0:
                        self.__maintainer_cv.wait()
                        # if notifed by join() then return asap
                        if not self.__running:
                            return
                # working
                to_remove = self.__tasks.pop()
                with self.__list_lock:
                    for i in range(len(self.__list_to_maintain)):
                        self.__list_to_maintain[i].remove(to_remove[i])
                        if type(to_remove[i]) == Thread:
                            to_remove[i].join()

        self.__maintainer_thread = Thread(target=__start)
        self.__maintainer_thread.start()

    def stop(self):
        self.__running = False
        with self.__maintainer_cv:
            self.__maintainer_cv.notify()
        self.__maintainer_thread.join()

    def remove(self, task: list):
        with self.__maintainer_cv:
            self.__tasks.append(task)
            self.__maintainer_cv.notify()
