import logging
import os
import Queue
import socket
import sys
import threading
import time
import random

import commands







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
