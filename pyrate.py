import logging
import os
import Queue
import socket
import sys
import threading
import time

import commands


class Listen(threading.Thread):
    """Creates a server socket on listen_port for incoming connections."""
    def __init__(self, client, in_queue, out_queue, listen_port):
        threading.Thread.__init__(self)
        self.client = client
        self.in_queue = in_queue
        self.out_queue = out_queue
        self.listen_port = listen_port

    def run(self):
        logging.debug('Launching Incoming thread')
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', self.listen_port))
        s.listen(5)
        while True:
            # accept a new client connection
            (clientsocket, address) = s.accept()
            logging.debug('Client connected:' + str(address))

            # set timeout so the socket closes when no new data is sent
            clientsocket.settimeout(0.4)

            # continue reading from socket until all data has been received
            message = ""
            loop_flag = True
            while loop_flag:
                m = clientsocket.recv(4096)
                if len(m) <= 0:
                    loop_flag = False
                message += m
                logging.debug('Read: %s' % m)
            clientsocket.close()

            # process complete message
            logging.debug('Complete message: %s' % message)
            self.process(message, address)


    def process(self, message, address):
        """Determines which type of message was received and adds it to the queue."""
        # # Register Msg Format -> 0:ListeningPort
        # if message.find('0:') == 0:
        #     # This is not a Bootstrap node, so do nothing
        #     pass

        # # Request Peer List Msg Format -> 1:MaxNumberOfPeersRequested
        # else if message.find('1:') == 0:
        #     # This is not a Bootstrap node, so do nothing
        #     pass

        # # Unregister Msg Format -> 2:ListeningPort
        # else if message.find('2:') == 0:
        #     # This is not a Bootstrap node, so do nothing
        #     pass

        # # Keepalive Msg Format -> 3:ListeningPort
        # else if message.find('3:') == 0:
        #     # This is not a Bootstrap node, so do nothing
        #     pass

        # # Download Msg Format -> 4:Filename
        # else if message.find('4:') == 0:
        #     code, filename = message.split(':')
        #     # command = InboundDownloadRequest(self.client, server, port, filename)

        # # List Files Msg Format -> 5:
        # else if message.find('5:') == 0:

        # # Search Msg Format -> 6:ID:File String:RequestingIP:RequestingPort:TTL
        # else if message.find('6:') == 0:

        # # Search Response Msg Format -> 7:ID:RespondingIP:RespondingPort:Filename
        # else if message.find('7:') == 0:

        # # Response Peer List Msg Format -> IPAddress1,PortNumber1\nIPAddress2,PortNumber2\n (etc.)
        # else if message.find('1:') == 0:

        # # Download Response Msg Format -> FILE

        # # List Files Response Msg Format ->Filename1\nFilename2\n (etc.)
        pass


class InboundQueue(threading.Thread):
    """Process inbound queue commands in a separate thread."""
    def __init__(self, in_queue, out_queue):
        threading.Thread.__init__(self)
        self.in_queue = in_queue
        self.out_queue = out_queue

    def run(self):
        logging.debug('Launching InboundQueue thread')
        while True:
            item = self.in_queue.get()
            item.run()
            self.in_queue.task_done()


class OutboundQueue(threading.Thread):
    """Process outbound queue commands in a separate thread."""
    def __init__(self, in_queue, out_queue):
        threading.Thread.__init__(self)
        self.in_queue = in_queue
        self.out_queue = out_queue

    def run(self):
        logging.debug('Launching OutboundQueue thread')
        while True:
            item = self.out_queue.get()
            item.run()
            self.out_queue.task_done()

class KeepAlive(threading.Thread):
    """Adds a KeepAlive command to the outbound queue every 10 minutes."""
    def __init__(self, in_queue, out_queue, interval_in_minutes ,client):
        threading.Thread.__init__(self)
        self.in_queue = in_queue
        self.out_queue = out_queue
        self.interval_in_minutes = interval_in_minutes
        self.client = client

    def run(self):
        logging.debug('Launching KeepAlive thread')
        while True:
            time.sleep(60 * self.interval_in_minutes)
            command = commands.BootstrapKeepAlive(self.client)
            self.out_queue.put(command)


class FileMonitor(threading.Thread):
    """Periodically updates filelist at a given interval."""
    def __init__(self, local_directory, interval_in_minutes, client):
        threading.Thread.__init__(self)
        self.local_directory = local_directory
        self.interval_in_minutes = interval_in_minutes
        self.client = client

    def run(self):
        logging.debug('Launching FileMonitor thread')
        while True:
            time.sleep(60 * self.interval_in_minutes)
            self.client.update_files()


class Client():
    def __init__(self, bootstrap_server, bootstrap_port, listen_port, keepalive, local_directory):
        self.in_queue = Queue.Queue()
        self.out_queue = Queue.Queue()
        self.peers = []
        self.bootstrap_server = bootstrap_server
        self.bootstrap_port = bootstrap_port
        self.listen_port = listen_port
        self.keepalive = keepalive
        self.local_directory = local_directory

        # configure logging module
        logging.basicConfig(filename='pyrate.log',level=logging.DEBUG)
        logging.debug('Initializing client...')

    def register(self):
        """Register our P2P client with bootstrap node."""
        self.outbound(commands.BootstrapRegister(self))

    def fetch_peers(self):
        """Fetch a list of peers from bootstrap node."""
        self.outbound(commands.BootstrapRequestPeerList(self))

    def update_files(self):
        """Refreshes current filelist with local directory contents."""
        logging.debug('Updating filelist')
        self.filelist = os.listdir(self.local_directory)

    def start(self):
        """Start the P2P client process."""
        logging.info('Starting client...')

        # gather initial list of available local files
        self.update_files()

        # register with bootstrap node
        self.register()

        # request peer list
        self.fetch_peers()

        # launch Listen thread
        t = Listen(self, self.in_queue, self.out_queue, self.listen_port)
        t.daemon = True
        t.start()

        # launch Inbound thread
        t = InboundQueue(self.in_queue, self.out_queue)
        t.daemon = True
        t.start()

        # launch Outbound thread
        t = OutboundQueue(self.in_queue, self.out_queue)
        t.daemon = True
        t.start()

        # launch KeepAlive thread
        t = KeepAlive(self.in_queue, self.out_queue, self.keepalive, self)
        t.daemon = True
        t.start()

        # launch FileMonitor thread
        t = FileMonitor(self.local_directory, 1, self)
        t.daemon = True
        t.start()

        # update display buffer
        # prompt user for input
        time.sleep(60*5)

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
    keepalive_timer = 10
    local_directory = '/Users/dougwt/Code/School/css432/pyrate/files'

    pyrate = Client(bootstrap_server, bootstrap_port, listen_port, keepalive_timer, local_directory)
    pyrate.start()
    pyrate.quit()
