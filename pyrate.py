import logging
import os
import Queue
import socket
import sys
import threading
import time
import random

import commands


class ClientListener(threading.Thread):
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
                try:
                    m = clientsocket.recv(4096)
                    if len(m) <= 0:
                        loop_flag = False
                    message += m
                    logging.debug('Read: %s' % m)
                except socket.timeout:
                    # logging.debug('Socket timed out.')
                    pass
            clientsocket.close()

            # process complete message
            logging.debug('Complete message: %s' % message)
            self.process(message, address)

    def process(self, message, address):
        """Determines which type of message was received and adds it to the queue."""
        server, port = address
        # Register Msg Format -> 0:ListeningPort
        if message.find('0:') == 0:
            # This is not a Bootstrap node, so do nothing
            logging.info('Detected incoming BootstrapRegister message. Discarded.')

        # Request Peer List Msg Format -> 1:MaxNumberOfPeersRequested
        elif message.find('1:') == 0:
            # This is not a Bootstrap node, so do nothing
            logging.info('Detected incoming BootstrapRequestPeerList message. Discarded.')

        # Unregister Msg Format -> 2:ListeningPort
        elif message.find('2:') == 0:
            # This is not a Bootstrap node, so do nothing
            logging.info('Detected incoming BootstrapRegister message. Discarded.')

        # Keepalive Msg Format -> 3:ListeningPort
        elif message.find('3:') == 0:
            # This is not a Bootstrap node, so do nothing
            logging.info('Detected incoming BootstrapRegister message. Discarded.')

        # Download Msg Format -> 4:Filename
        elif message.find('4:') == 0:
            code, filename = message.split(':')
            logging.info('Detected incoming DownloadRequest message from %s:%s %s' % (server, port, filename))
            command = commands.InboundDownloadRequest(self.client, server, port, filename)
            self.client.inbound(command)

        # List Files Msg Format -> 5:
        elif message.find('5:') == 0:
            logging.info('Detected incoming ListFilesRequest message from %s:%s' % server, port)
            command = commands.InboundListRequest(self.client, server, port)
            self.client.inbound(command)

        # Search Msg Format -> 6:ID:File String:RequestingIP:RequestingPort:TTL
        elif message.find('6:') == 0:
            code, id, filename, requesting_ip, requesting_port, ttl = message.split(':')
            logging.info('Detected incoming SearchRequest message from %s:%s' % (server, port))
            command = commands.InboundSearchRequest(self.client, server, port, requesting_ip, requesting_port, filename, ttl)
            self.client.inbound(command)

        # Search Response Msg Format -> 7:ID:RespondingIP:RespondingPort:Filename
        elif message.find('7:') == 0:
            code, id, respdonding_ip, responding_port, filename = message.split(':')
            logging.info('Detected incoming SearchResponse message from %s:%s %s' % (server, port, filename))
            command = commands.InboundSearchResponse(self.client, server, port, filename, respdonding_ip, responding_port)
            self.client.inbound(command)

        # List Files Response Msg Format ->Filename1\nFilename2\n (etc.)
        else:
            filelist = filename.split('\n')
            logging.info('Detected incoming ListResponse message from %s:%s %s' % (server, port, filelist))
            command = commands.InboundListResponse(self.client, server, port, filelist)
            self.client.inbound(command)


class BootstrapListener(threading.Thread):
"""Creates a server socket on listen_port for incoming connections."""
    def __init__(self, bootstrap, queue, listen_port):
        threading.Thread.__init__(self)
        self.bootstrap = bootstrap
        self.queue = queue
        self.listen_port = listen_port

    def run(self):
        logging.debug('Launching Bootstrap Listener')
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
                try:
                    m = clientsocket.recv(4096)
                    if len(m) <= 0:
                        loop_flag = False
                    message += m
                    logging.debug('Read: %s' % m)
                except socket.timeout:
                    # logging.debug('Socket timed out.')
                    pass
            clientsocket.close()

            # process complete message
            logging.debug('Complete message: %s' % message)
            self.process(message, address)

    def process(self, message, address):
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
    def __init__(self, bootstrap_server, bootstrap_port, listen_port, keepalive, local_directory, log_file):
        self.in_queue = Queue.Queue()
        self.out_queue = Queue.Queue()
        self.peers = []
        self.bootstrap_server = bootstrap_server
        self.bootstrap_port = bootstrap_port
        self.listen_port = listen_port
        self.keepalive = keepalive
        self.local_directory = local_directory
        self.log_file = log_file
        self.seen = []

        # configure logging module
        logging.basicConfig(filename=self.log_file,level=logging.DEBUG)
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

    def input_loop(self):
        print 'Available commands include GET, LIST, SEARCH, PEERS, GETPEERS, and QUIT'
        while True:
            # TODO: update display buffer

            # prompt user for input
            input = raw_input('Enter a command: ').split()

            if input[0].upper() == 'QUIT':
                logging.debug('User entered QUIT command.')
                print 'Exiting client.'
                return

            elif input[0].upper() == 'GET':
                if len(input) == 4:
                    server, port, filename = input[1:]
                    port = int(port)

                    logging.debug('User entered GET command. [GET %s %s %s' % (server, port, filename))
                    command = commands.OutboundDownloadRequest(self, server, port, filename)
                    self.outbound(command)
                else:
                    print 'Invalid GET parameters. Try GET <server> <port> <filename>'

            elif input[0].upper() == 'LIST':
                if len(input) == 3:
                    server, port = input[1:]
                    port = int(port)
                    logging.debug('User entered LIST command. [LIST %s %s]' % (server, port))
                    command = commands.OutboundListRequest(self, server, port)
                    self.outbound(command)
                else:
                    print 'Invalid LIST parameters. Try LIST <server> <port>'

            elif input[0].upper() == 'SEARCH':
                if len(input) == 2:
                    filename = input[1]
                    logging.debug('User entered SEARCH command. [SEARCH %s]' % (filename))
                    id = filename + str(random.randint(100, 999))
                    requesting_ip = socket.gethostbyname(socket.gethostname())
                    requesting_port = listen_port
                    ttl = 10

                    # add id to list of seen searches, so we don't forward our own requests
                    self.seen.append(id)

                    # generate a Request for each peer in peerlist
                    for peer in self.peers:
                        server, port = peer
                        port = int(port)
                        print 'Building Command for %s:%s' % (server, port)
                        command = commands.OutboundSearchRequest(self, server, port, id, filename, requesting_ip, requesting_port, ttl)
                        self.outbound(command)
                else:
                    print 'Invalid SEARCH parameters. Try SEARCH <filename>'

            elif input[0].upper() == 'PEERS':
                logging.debug('User entered PEERS command.')
                for peer in self.peers:
                    print peer

            elif input[0].upper() == 'GETPEERS':
                logging.debug('User entered GETPEERS command.')
                self.fetch_peers()

            else:
                print 'Invalid Command. Try GET, LIST, SEARCH, PEERS, GETPEERS, or QUIT.'


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

        self.input_loop()

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


class Bootstrap():
    def __init__(self, listen_port, keepalive, log_file):
        self.queue = Queue.Queue()
        self.listen_port = listen_port
        self.keepalive = keepalive
        self.log_file = log_file
        self.peers = {}

    def start(self):
    """Start the P2P bootstrap process."""
        # spawn listener process

        while True:
            # process anything in queue
            # remove expired peers

    def process(self, message, address):
    """Command Factory."""
        pass

    def quit(self):
    """Stop the P2P bootstrap process."""
        pass


if __name__ == '__main__':
    bootstrap_server = 'localhost'
    bootstrap_port = 21168
    listen_port = 63339
    keepalive_timer = 10
    local_directory = '/Users/dougwt/Code/School/css432/pyrate/files'
    log_file = 'pyrate.log'

    p = Client(bootstrap_server, bootstrap_port, listen_port, keepalive_timer, local_directory, log_file)
    p.start()
    p.quit()
