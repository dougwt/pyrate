import logging
import Queue
import socket
import sys
import threading
import time

import commands


class Inbound(threading.Thread):
    """Process inbound queue commands in a separate thread."""
    def __init__(self, in_queue, out_queue):
        threading.Thread.__init__(self)
        self.in_queue = in_queue
        self.out_queue = out_queue

    def run(self):
        logging.debug('Launching Inbound thread')
        while True:
            item = self.in_queue.get()
            item.run()
            self.in_queue.task_done()


class Outbound(threading.Thread):
    """Process outbound queue commands in a separate thread."""
    def __init__(self, in_queue, out_queue):
        threading.Thread.__init__(self)
        self.in_queue = in_queue
        self.out_queue = out_queue

    def run(self):
        logging.debug('Launching Outbound thread')
        while True:
            item = self.out_queue.get()
            item.run()
            self.out_queue.task_done()


class Client():
    def __init__(self, bootstrap_server, bootstrap_port, listen_port):
        self.in_queue = Queue.Queue()
        self.out_queue = Queue.Queue()
        self.peers = []
        self.bootstrap_server = bootstrap_server
        self.bootstrap_port = bootstrap_port
        self.listen_port = listen_port
        self.prev_keepalive = None

        # configure logging module
        logging.basicConfig(filename='pyrate.log',level=logging.DEBUG)
        logging.debug('Initializing client...')

    def register(self):
        """Register our P2P client with bootstrap node."""

        # update keepalive timer
        self.prev_keepalive = time.clock()

        self.outbound(commands.BootstrapRegister(self))

    def fetch_peers(self):
        """Fetch a list of peers from bootstrap node."""
        self.outbound(commands.BootstrapRequestPeerList(self))

    def start(self):
        """Start the P2P client process."""
        logging.info('Starting client...')

        # register with bootstrap node
        self.register()

        # request peer list
        self.fetch_peers()

        # launch Inbound thread
        t = Inbound(self.in_queue, self.out_queue)
        t.daemon = True
        t.start()

        # launch Outbound thread
        t = Outbound(self.in_queue, self.out_queue)
        t.daemon = True
        t.start()

        # update display buffer
        # prompt user for input

        # in_queue.join()
        # out_queue.join()

    def outbound(self, command):
        """Add a command to the outbound queue."""
        self.out_queue.put(command)

    def inbound(self, command):
        """Add a command to the inbound queue."""
        self.in_queue.put(command)

    def quit(self):
        """Stop the P2P client process."""
        # Unregister with Bootstrap Node
        self.outbound(commands.BootstrapUnregister(self))

        # Wait to finish processing all commands in outbound queue
        self.out_queue.join()

        logging.info('Exiting client.')
        sys.exit()


if __name__ == '__main__':
    bootstrap_server = 'localhost'
    bootstrap_port = 21168
    listen_port = 63339

    pyrate = Client(bootstrap_server, bootstrap_port, listen_port)
    pyrate.start()
    pyrate.quit()
