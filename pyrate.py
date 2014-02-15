import logging
import os
import Queue
import socket
import sys
import threading
import time
import random
import collections

import commands

def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)

Message = enum('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
Connection = collections.namedtuple('Connection', ['address', 'port'])


class Client():
    def __init__(self, bootstrap_addr, bootstrap_port, listen_addr, listen_port,
      keepalive_seconds, filemonitor_seconds, local_directory, log_file, max_workers):
        self.queue = Queue.Queue()
        self.peers = []
        self.seen_requests = []
        self.shared_files = []

        self.bootstrap = Connection(bootstrap_addr, bootstrap_port)
        self.listen = Connection(listen_addr, listen_port)

        self.keepalive_seconds = keepalive_seconds
        self.filemonitor_seconds = filemonitor_seconds
        self.keepalive = Timer(self.keepalive_seconds)
        self.file_monitor = Timer(self.filemonitor_seconds)
        self.max_workers = max_workers  # Max # of simultaneous worker threads
        self.pool = Threadpool(self.max_workers)

        self.shared_path = local_directory
        self.log_file = log_file

        self.listener = Listener(self)
        self.listener.daemon = True
        # self.console = Console(self)      # TODO: Implement Console
        self.console = None
        # self.console.daemon = True

        # configure logging module
        logging.basicConfig(filename=self.log_file,level=logging.DEBUG)
        self.log(Message.DEBUG, 'Initializing client...')

    def register(self):
        """Register P2P client with bootstrap node."""
        msg = 'Queueing Bootstrap Register command (%s:%s)' % self.bootstrap
        self.log(Message.DEBUG, msg)
        self.add(commands.OutboundBootstrapRegister(self))

    def unregister(self):
        """Unregisteres P2P client with bootstrap node."""
        msg = 'Queueing Bootstrap Unregister command (%s:%s)' % self.bootstrap
        self.log(Message.DEBUG, msg)
        self.add(commands.OutboundBootstrapUnregister(self))

    def keepalive(self):
        """Send KeepAlive message to bootstrap node."""
        msg = 'Queueing Bootstrap KeepAlive command (%s:%s)' % self.bootstrap
        self.log(Message.DEBUG, msg)
        self.add(commands.OutboundBootstrapKeepAlive(self))

    def fetch_peers(self):
        """Fetch a list of peers from bootstrap node."""
        msg = 'Queueing Bootstrap Request PeerList command (%s:%s)' % self.bootstrap
        self.log(Message.DEBUG, msg)
        self.add(commands.OutboundBootstrapRequestPeerList(self))

    def update_files(self):
        """Refreshes current filelist with local directory contents."""
        self.log(Message.DEBUG, 'Updating filelist')
        # TODO: Update File List
        # self.filelist = os.listdir(self.local_directory)

    def start(self):
        """Start the P2P client process."""
        self.log(Message.INFO, 'Starting client...')

        # gather initial list of available local files
        self.update_files()

        # register with bootstrap node
        self.register()

        # request peer list
        self.fetch_peers()

        # launch component threads
        self.listener.start()
        # self.console.start()      # TODO: Uncomment once Console implemented

        while True:
            # Check Queue for commands
            if not self.queue.empty() and self.pool.acquire():
                item = self.queue.get()
                # TODO: Spin off Command in separate Thread
                item.run()
                self.log(Message.DEBUG, 'Running %s' % item)
                self.queue.task_done()
                self.Threadpool.release()

            # keepalive
            if self.keepalive.expired():
                self.log(Message.DEBUG, 'KeepAlive expired')
                self.add(commands.OutboundBootstrapKeepAlive(self))

            # file monitor
            if self.file_monitor.expired():
                self.log(Message.DEBUG, 'File Monitor expired')
                self.client.update_files()

    def add(self, command):
        """Add a command to the inbound queue."""
        self.queue.put(command)

    def add_seen(self, command):
        """Add a command to the recently seen queue."""
        self.seen_requests.put(command)

    def quit(self):
        """Stop the P2P client process."""
        self.unregister()

        # Wait to finish processing all commands in queue
        self.queue.join()

        self.log(Message.INFO, 'Exiting client.')
        sys.exit()

    def log(self, level, message = Message.INFO):
        """Generate a log message with the given level of importance."""
        # Write non-debug message to Console buffer
        if (self.console and level > Message.DEBUG):
            self.console.write(message)

        # Forward message to appropriate logging function
        if (level == Message.DEBUG):
            logging.debug(message)
        elif (level == Message.INFO):
            logging.info(message)
        elif (level == Message.WARNING):
            logging.warning(message)
        elif (level == Message.ERROR):
            logging.error(message)
        elif (level == Message.CRITICAL):
            logging.critical(message)


class Listener(threading.Thread):
    """Creates a server socket on listen_port for incoming connections."""
    def __init__(self, client):
        threading.Thread.__init__(self)
        self.client = client
        self.queue = client.queue
        self.listen = client.listen

    def run(self):
        """Monitor server socket for incoming connections."""
        self.client.log(Message.DEBUG, 'Launching Listener thread')
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.listen.address, self.listen.port))
        s.listen(5)
        while True:
            # accept a new client connection
            (clientsocket, address) = s.accept()
            self.client.log(Message.DEBUG, 'Client connected:' + str(address))

            # set timeout so the socket closes when no new data is sent
            clientsocket.settimeout(0.4)

            # continue reading from socket until all data has been received
            message = ""
            loop_flag = True
            while loop_flag:
                try:
                    m = clientsocket.recv(4096)
                    if len(m) <= 0:
                        loop_flag = False
                    message += m
                    self.client.log(Message.DEBUG, 'Read: %s' % m)
                except socket.timeout:
                    self.client.log(Message.DEBUG, 'Socket timed out.')
            clientsocket.close()

            # process complete message
            self.client.log(Message.DEBUG, 'Complete message: %s' % message)
            self.client.add(commands.Decode(self.client, message, address))


class Threadpool():
    """A simple counter to track the number of current worker threads."""
    def __init__(self, max_workers):
        self.workers = 0
        self.max = max_workers

    def acquire(self):
        """Returns True if an available Worker was found and claimed."""
        if self.workers < self.max:
            self.workers += 1
            return True
        else:
            return False

    def release(self):
        """Returns True if a worker was successfully released."""
        if self.workers > 0:
            workers -= 1
            return True
        else:
            return False

class Timer():
    """A simple timer that expires at a set interval given in seconds."""
    def __init__(self, seconds):
        self.seconds = seconds
        self.start_time = self.get_current_time()

    def expired(self):
        """Returns True if enough time has elapsed since start_time."""
        current_time = self.get_current_time()
        if (current_time > (self.start_time + self.seconds)):
            self.start_time = current_time  # prepare for next interval
            return True
        else:
            return False

    def get_current_time(self):
        """Returns the current time in seconds."""
        return time.time()

if __name__ == '__main__':
    bootstrap_address = 'localhost'
    bootstrap_port = 21168
    listen_address = 'localhost'
    listen_port = 63339
    keepalive_seconds = 1*60
    filemonitor_seconds = 1*60
    local_directory = '/Users/dougwt/Code/School/css432/pyrate/files'
    log_file = 'pyrate.log'
    max_workers = 4

    p = Client(bootstrap_address,
               bootstrap_port,
               listen_address,
               listen_port,
               keepalive_seconds,
               filemonitor_seconds,
               local_directory,
               log_file,
               max_workers)
    p.start()
    p.quit()
