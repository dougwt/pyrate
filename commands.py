import abc
import logging
import socket

class Socket():
    """Establishes a socket connection."""
    def __init__(self, address, port):
        self.address = address
        self.port = port

        # logging.debug('Establishing socket connection to %s:%s...' % (address, port))
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error, msg:
            print 'Failed to create socket. Error code: %s, Error message: %s' % (str(msg[0]), msg[1])
            sys.exit()

        try:
            remote_ip = socket.gethostbyname(address)
        except socket.gaierror:
            print 'Hostname could not be resolved. Exiting.'
            sys.exit()

        # now connect to the Bootstrap node on the given port
        self.s.connect((remote_ip, port))

    def __del__(self):
        self.close()

    def close(self):
        # logging.debug('Disconnecting socket to %s:%s' % (self.address, self.port))
        self.s.close()

    def send(self, message):
        try:
            self.s.sendall(message)
        except socket.error:
            print 'Send failed'
            sys.exit()

    def recv(self):
        message = ""
        loop_flag = True
        while loop_flag:
            m = self.s.recv(4096)
            if len(m) <= 0:
                loop_flag = False
            message += m
            logging.debug('Read: %s' % m)
        return message

    def get_port(self):
        return self.s.getsockname()


class ServerSocket(Socket):
    def __init__(self, port):
        self.port = port

        # logging.debug('Establishing socket connection to %s:%s...' % (address, port))
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error, msg:
            print 'Failed to create socket. Error code: %s, Error message: %s' % (str(msg[0]), msg[1])
            sys.exit()

        # now connect to the Bootstrap node on the given port
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind(('', port))
        self.s.listen(0)
        (self.clientsocket, self.address) = self.s.accept()
        self.s.close()
        self.s = self.clientsocket


class Command():
    """Abstract Base Class for Inbound and Outbound Queue Commands."""
    __metaclass__  = abc.ABCMeta
    def __init__(self, client, *args, **kwargs):
        self.client = client

    @abc.abstractmethod
    def run(self):
        pass


class CommandFactory():
    """This is the place where Commands are born."""
    @staticmethod
    def decode(client, message, connection):
        """Decodes a response into the corresponding Command object."""
        address, port = connection

        prefix = message[:2]

        # Register Msg Format -> 0:ListeningPort
        if prefix == '0:':
            # This is not a Bootstrap node, so do nothing
            logging.info('Detected incoming BootstrapRegister message. Discarded.')

        # Request Peer List Msg Format -> 1:MaxNumberOfPeersRequested
        elif prefix == '1:':
            # This is not a Bootstrap node, so do nothing
            logging.info('Detected incoming BootstrapRequestPeerList message. Discarded.')

        # Unregister Msg Format -> 2:ListeningPort
        elif prefix == '2:':
            # This is not a Bootstrap node, so do nothing
            logging.info('Detected incoming BootstrapRegister message. Discarded.')

        # Keepalive Msg Format -> 3:ListeningPort
        elif prefix == '3:':
            # This is not a Bootstrap node, so do nothing
            logging.info('Detected incoming BootstrapRegister message. Discarded.')

        # Download Msg Format -> 4:Filename
        elif prefix == '4:':
            code, filename = message.split(':')
            logging.info('Detected incoming DownloadRequest message from %s:%s %s' % (address, port, filename))
            return InboundDownloadRequest(client, address, port, filename)

        # List Files Msg Format -> 5:
        elif prefix == '5:':
            logging.info('Detected incoming ListFilesRequest message from %s:%s' % (address, port))
            return InboundListRequest(client, address, port)

        # Search Msg Format -> 6:ID:File String:RequestingIP:RequestingPort:TTL
        elif prefix == '6:':
            code, id, filename, requesting_ip, requesting_port, ttl = message.split(':')
            logging.info('Detected incoming SearchRequest message from %s:%s' % (address, port))
            return InboundSearchRequest(client, address, port, requesting_ip, requesting_port, filename, ttl)

        # Search Response Msg Format -> 7:ID:RespondingIP:RespondingPort:Filename
        elif prefix == '7:':
            code, id, respdonding_ip, responding_port, filename = message.split(':')
            logging.info('Detected incoming SearchResponse message from %s:%s %s' % (address, port, filename))
            return InboundSearchResponse(client, address, port, filename, respdonding_ip, responding_port)


        # TODO: else case should result in the message being discarded.
        # I'm leaving this here for now until I can refactor the Files Response
        # message directly into the RequestFiles Command.

        # List Files Response Msg Format ->Filename1\nFilename2\n (etc.)
        else:
            filelist = filename.split('\n')
            logging.info('Detected incoming ListResponse message from %s:%s %s' % (address, port, filelist))
            return InboundListResponse(client, address, port, filelist)

        return None


# Client Commands


class Decode(Command):
    """Decodes received message into corresponding Command."""
    def __init__(self, client, message, connection):
        self.client = client
        self.message = message
        self.connection = connection

    def run(self):
        command = CommandFactory.decode(self.client, self.message, self.connection)
        logging.debug('Decoding \'%s\' (%s:%s) -> %s' %
            (self.message, self.connection.address, self.connection.port, command))

        if command:
            logging.debug('Queueing (%s:%s) %s' % (self.connection.address, self.connection.port, command))
            self.client.add(command)


# Inbound Commands


class InboundBootstrapRegister(Command):
    # TODO: Implement stub
    def run(self):
        pass


class InboundBootstrapRequestPeerList(Command):
    # TODO: Implement stub
    def run(self):
        pass


class InboundBootstrapUnregister(Command):
    # TODO: Implement stub
    def run(self):
        pass


class InboundBootstrapKeepAlive(Command):
    # TODO: Implement stub
    def run(self):
        pass


class InboundDownloadRequest(Command):
    """Inbound Download Request."""
    def __init__(self, client, server, port, filename, *args, **kwargs):
        self.client = client
        self.server = server
        self.port = port
        self.filename = filename

    def run(self):
        logging.info('Received Download Request from %s:%s' %
            (self.server, self.port))

        logging.info('Preparing to send \'%s\' to %s:%s...' %
            (self. filename, self.server, self.port))
        bootstrap = Socket(self.server, self.port)

        # send actual file contents
        with open(self.client.local_directory + '/' + self.filename, 'r') as f:
            # Download Response Message
            bootstrap.send(f.read())

        logging.info('Finished sending \'%s\' to %s:%s...' %
            (self. filename, self.server, self.port))


class InboundListRequest(Command):
    """Inbound File List Request."""
    def __init__(self, client, server, port, *args, **kwargs):
        self.client = client
        self.server = server
        self.port = port

    def run(self):
        logging.info('Received File List Request from %s:%s' %
            (self.server, self.port))

        # format file list for transmission
        if len(self.filelist) > 0:
            msg = ('\n').join(self.client.filelist) + '\n'
        else:
            msg = ''

        logging.info('Sending File List Response to %s:%s...' %
            (self.server, self.port))

        bootstrap = Socket(self.server, self.port)

        # List Files Response Message
        bootstrap.send(msg)

        # format file list for transmission
        if len(self.filelist) > 0:
            msg = ('\n').join(self.client.filelist) + '\n'
        else:
            msg = ''

        # List Files Response Message
        bootstrap.send(msg)


class InboundListResponse(Command):
    """Inbound List Response."""
    def __init__(self, client, server, port, filelist, *args, **kwargs):
        self.client = client
        self.server = server
        self.port = port
        self.filelist = filelist

    def run(self):
        logging.info('Received File List Response from %s:%s : %s' %
            (self.server, self.port, self.filelist))

        # TODO: Display List Files Result


class InboundSearchRequest(Command):
    """Inbound Search Request."""
    def __init__(self, client, server, port, requesting_ip, requesting_port, ident, filename, ttl, *args, **kwargs):
        self.client = client
        self.server = server
        self.port = port
        self.requesting_ip = requesting_ip
        self.requesting_port = requesting_port
        self.id = ident
        self.filename = filename
        self.ttl = ttl

    def run(self):
        logging.info('Received Search Request for \'%s\' from %s:%s : %s' %
            (self.filename, self.server, self.port, self.filelist))

        # if we've already seen this request, do nothing
        if self.id in self.client.seen:
            return
        # otherwise, add it to our list of seen requests for next time
        else:
            self.client.seen.add(self.id)

        # if we have this file, let the original client know
        if self.filename in self.client.filelist:
            # add Search Response to outbound queue
            command = OutboundSearchResponse(self.client,
                                             self.server,
                                             self.port,
                                             self.id,
                                             self.requesting_ip,
                                             self.requesting_port,
                                             self.filename)
            self.client.out_queue.put(command)

        # if we don't have the file and TTL > 0, forward the Search Request
        elif self.ttl > 0:
            # add Search Request to outbound queue
            command = OutboundSearchRequest(self.client,
                                             self.server,
                                             self.port,
                                             self.id,
                                             self.filename,
                                             self.requesting_ip,
                                             self.requesting_port,
                                             self.ttl - 1)
            self.client.out_queue.put(command)


class InboundSearchResponse(Command):
    """Inbound Search Response."""
    def __init__(self, client, server, port, filename, responding_ip, responding_port, *args, **kwargs):
        self.client = client
        self.server = server
        self.port = port
        self.filename = filename
        self.responding_ip
        self.responding_port

    def run(self):
        logging.info('Received File List Response from %s:%s : %s' %
            (self.server, self.port, self.filelist))

        # TODO: Display Search Results


# Outbound Commands


class OutboundBootstrapRegister(Command):
    """Register with the Bootstrap Node."""
    def run(self):
        logging.info('Registering with Bootstrap Node %s:%s' %
            (self.client.bootstrap.address, self.client.bootstrap.port))

        bootstrap = Socket(self.client.bootstrap.address, self.client.bootstrap.port)

        # Register Message
        bootstrap.send('0:%s' % self.client.bootstrap.port)


class OutboundBootstrapRequestPeerList(Command):
    """Request an updated Peer List from the Bootstrap Node."""
    def run(self):
        logging.info('Requesting Peer List from Bootstrap Node %s:%s' %
            (self.client.bootstrap.address, self.client.bootstrap.port))

        bootstrap = Socket(self.client.bootstrap.address, self.client.bootstrap.port)

        # Request Peer List Message
        bootstrap.send('1:3')

        peer_list_response = bootstrap.recv()
        logging.info('Received Peer List Response: %s' % peer_list_response)

        peerlist = []
        for item in peer_list_response.split('\n')[0:-1]:
            node = item.split(',')
            peerlist.append((node[0], node[1]))

        # update peer list with any new peers
        for peer in peerlist:
            if peer not in self.client.peers:
                self.client.peers.append(peer)

        # return peer_list_response


class OutboundBootstrapUnregister(Command):
    """Unregister with the Bootstrap Node."""
    def run(self):
        logging.info('Unregistering with Bootstrap Node %s:%s' %
            (self.client.bootstrap.address, self.client.bootstrap.port))

        bootstrap = Socket(self.client.bootstrap.address, self.client.bootstrap.port)

        # Unregister Message
        bootstrap.send('2:%s' % self.client.bootstrap.port)


class OutboundBootstrapKeepAlive(Command):
    """Transmit a KeepAlive message to the Bootstrap Node."""
    def run(self):
        logging.info('Sending KeepAlive to Bootstrap Node %s:%s' %
            (self.client.bootstrap.address, self.client.bootstrap.port))

        bootstrap = Socket(self.client.bootstrap.address, self.client.bootstrap.port)

        # KeepAlive Message
        bootstrap.send('3:%s' % self.client.bootstrap.port)


class OutboundDownloadRequest(Command):
    """Outbound Download Request."""
    def __init__(self, client, server, port, filename, *args, **kwargs):
        self.client = client
        self.server = server
        self.port = port
        self.filename = filename

    def run(self):
        logging.info('Sending Download Request for \'%s\' to %s:%s' %
            (self.filename, self.server, self.port))

        bootstrap = Socket(self.server, self.port)

        # Send Download Message
        bootstrap.send('4:%s' % self.filename)
        unused, temp_port = bootstrap.get_port()
        bootstrap.close()

        logging.info('Waiting for response from %s:%s [%s]...' %
            (self.server, self.port, temp_port))

        # Establish server socket for response connection
        bootstrap = ServerSocket(temp_port)
        data = bootstrap.recv()

        logging.info('Response received. Saving \'%s\'.' % self.filename)
        # save file to local directory
        with open(self.client.local_directory + '/' + self.filename, 'w') as f:
            f.write(data)

        logging.info('Finished saving \'%s\'.' % self.filename)


class OutboundListRequest(Command):
    """Outbound Download Request."""
    def __init__(self, client, server, port, *args, **kwargs):
        self.client = client
        self.server = server
        self.port = port

    def run(self):
        logging.info('Sending File List Request to %s:%s' %
            (self.server, self.port))

        bootstrap = Socket(self.server, self.port)

        # List Files Message
        bootstrap.send('5:')


class OutboundSearchRequest(Command):
    """Outbound Search Request."""
    def __init__(self, client, server, port, id, filename, requesting_ip, requesting_port, ttl, *args, **kwargs):
        self.client = client
        self.server = server
        self.port = port
        self.id = id
        self.filename = filename
        self.requesting_ip = requesting_ip
        self.requesting_port = requesting_port
        self.ttl = ttl

    def run(self):
        logging.info('Sending Search Request for \'%s\' to %s:%s' %
            (self.filename, self.server, self.port))

        bootstrap = Socket(self.server, self.port)

        # For some reason, this line causes an error, so use alternate string below
        # message = '6:%s:%s:%s' % (self.id, self.filename, self.requesting_ip, self.requesting_port, self.ttl)
        message = '6:' + self.id + ':' + str(self.filename) + ':' + str(self.requesting_ip) + ':' + str(self.requesting_port) + ':' + str(self.ttl)

        # Search Message
        bootstrap.send(message)


class OutboundSearchResponse(Command):
    """Outbound Search Response."""
    def __init__(self, client, server, port, id, responding_ip, responding_port, filename, *args, **kwargs):
        self.client = client
        self.server = server
        self.port = port
        self.id = id
        self.responding_ip = responding_ip
        self.responding_port = responding_port
        self.filename = filename

    def run(self):
        logging.info('Sending Search Response for \'%s\' to %s:%s' %
            (self.filename, self.server, self.port))

        bootstrap = Socket(self.server, self.port)

        # Search Response Message
        bootstrap.send('7:%s:%s:%s' % (self.id, self.responding_port, self.name))
