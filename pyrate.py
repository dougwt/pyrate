import threading
import Queue
import commands

class Inbound(threading.Thread):
    def __init__(self, in_queue, out_queue):
        threading.Thread.__init__(self)
        self.in_queue = in_queue
        self.out_queue = out_queue

    def run(self):
        while True:
            # item = self.in_queue.get()

            # result = 'You should be doing work.'
            # self.out_queue.put(result)

            # self.in_queue.task_done()
            pass

class Outbound(threading.Thread):
    def __init__(self, in_queue, out_queue):
        threading.Thread.__init__(self)
        self.in_queue = in_queue
        self.out_queue = out_queue

    def run(self):
        while True:
            # item = self.out_queue.get()

            # result = 'This is your awesome output.'

            # self.out_queue.task_done()
            pass

if __name__ == '__main__':

    in_queue = Queue.Queue()
    out_queue = Queue.Queue()

    # Launch Inbound thread
    t = Inbound(in_queue, out_queue)
    t.daemon = True
    t.start()

    # Launch Outbound thread
    t = Outbound(out_queue)
    t.daemon = True
    t.start()

    # in_queue.join()
    # out_queue.join()
