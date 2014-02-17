import abc
from logging import debug
import socket

DEBUG = 0  # KLUDGE: Stand-in for Message.DEBUG

class Socket():
    """Establishes a socket connection."""
    def __init__(self, address, port):
        self.address = address
        self.port = port

        debug('Establishing socket connection to %s:%s...' % (address, port))
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error, msg:
            msg = 'Failed to create socket. Error code: %s, Error message: %s'
            print msg % (str(msg[0]), msg[1])
            sys.exit()

        try:
            remote_ip = socket.gethostbyname(address)
        except socket.gaierror:
            print 'Hostname could not be resolved. Exiting.'
            sys.exit()

        # now connect to the Bootstrap node on the given port
        self.s.connect((remote_ip, port))

    def __del__(self):
        """Let's wrap it up, boys! Time to go home."""
        self.close()

    def close(self):
        debug('Disconnecting socket to %s:%s' % (self.address, self.port))
        self.s.close()

    def send(self, message):
        """Send a message via the socket."""
        try:
            self.s.sendall(message)
        except socket.error:
            print 'Send failed'
            sys.exit()

    def recv(self):
        """Receive a message via the socket."""
        message = ""
        loop_flag = True
        while loop_flag:
            m = self.s.recv(4096)
            if len(m) <= 0:
                loop_flag = False
            message += m
            debug('Read: %s' % m)
        return message

    def get_port(self):
        """Returns the socket's port number."""
        return self.s.getsockname()


class ServerSocket(Socket):
    """Establishes a temp server socket to accept one incoming connection."""
    def __init__(self, port, address=''):
        self.address = address
        self.port = port

        debug('Establishing socket connection to %s:%s...' % (address, port))
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error, msg:
            error = 'Failed to create socket. Error code: %s, Error message: %s'
            print error % (str(msg[0]), msg[1])
            sys.exit()

        # now connect to the Bootstrap node on the given port
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind((self.address, self.port))
        self.s.listen(0)
        self.clientsocket, self.address = self.s.accept()
        self.s.close()
        self.s = self.clientsocket


class Command():
    """Abstract Base Class for Queue commands."""
    __metaclass__  = abc.ABCMeta
    def __init__(self, client):
        self.client = client

    @abc.abstractmethod
    def run(self):
        pass

    def log(self, msg):
        return self.client.log(DEBUG, msg)


class CommandFactory():
    """We must be crazy, cuz we're practically giving Commands away!"""
    @staticmethod
    def decode(client, message, connection):
        """Decodes an incoming message into its corresponding Command object."""
        address, port = connection

        def log(msg):
            return client.log(DEBUG, msg)

        prefix = message[:2]

        # Register Msg Format -> 0:ListeningPort
        if prefix == '0:':
            # This is not a Bootstrap node, so do nothing
            log('Detected incoming BootstrapRegister message. Discarded.')

        # Request Peer List Msg Format -> 1:MaxNumberOfPeersRequested
        elif prefix == '1:':
            # This is not a Bootstrap node, so do nothing
            log('Detected incoming BootstrapRequestPeerList message. Discarded.')

        # Unregister Msg Format -> 2:ListeningPort
        elif prefix == '2:':
            # This is not a Bootstrap node, so do nothing
            log('Detected incoming BootstrapRegister message. Discarded.')

        # Keepalive Msg Format -> 3:ListeningPort
        elif prefix == '3:':
            # This is not a Bootstrap node, so do nothing
            log('Detected incoming BootstrapRegister message. Discarded.')

        # Download Msg Format -> 4:Filename
        elif prefix == '4:':
            code, filename = message.split(':')
            msg = 'Detected incoming DownloadRequest message from %s:%s %s'
            log(msg % (address, port, filename))
            return InboundDownloadRequest(client, address, port, filename)

        # List Files Msg Format -> 5:
        elif prefix == '5:':
            msg = 'Detected incoming ListFilesRequest message from %s:%s'
            log(msg % (address, port))
            return InboundListRequest(client, address, port)

        # Search Msg Format -> 6:ID:File String:RequestingIP:RequestingPort:TTL
        elif prefix == '6:':
            code, id, filename, requesting_ip, requesting_port, ttl = \
              message.split(':')

            msg = 'Detected incoming SearchRequest message from %s:%s'
            log(msg % (address, port))
            return InboundSearchRequest(client, address, port, requesting_ip,
              requesting_port, filename, ttl)

        # Search Response Msg Format -> 7:ID:RespondingIP:RespondingPort:Filename
        elif prefix == '7:':
            code, id, respdonding_ip, responding_port, filename = \
              message.split(':')

            msg = 'Detected incoming SearchResponse message from %s:%s %s'
            log(msg % (address, port, filename))
            return InboundSearchResponse(client, address, port, filename,
              respdonding_ip, responding_port)

        # TODO: else case should result in the message being discarded.
        # I'm leaving this here for now until I can refactor the Files Response
        # message directly into the RequestFiles Command.

        # List Files Response Msg Format ->Filename1\nFilename2\n (etc.)
        else:
            filelist = filename.split('\n')
            msg = 'Detected incoming ListResponse message from %s:%s %s'
            log(msg % (address, port, filelist))
            return InboundListResponse(client, address, port, filelist)

        return None


# Decode


class Decode(Command):
    """Contains a received message that is yet to be decoded."""
    def __init__(self, client, message, connection):
        self.client = client
        self.message = message
        self.connection = connection

    def run(self):
        command = CommandFactory.decode(self.client, self.message,
          self.connection)

        msg = 'Decoding \'%s\' (%s:%s) -> %s' % (self.message, \
          self.connection.address, self.connection.port, command)
        self.log(msg)

        if command:
            msg = 'Queueing (%s:%s) %s'
            log(msg % (self.connection.address, self.connection.port, command))
            self.client.add(command)


# BootstrapRegister


class InboundBootstrapRegister(Command):
    """Registers the sending peer with the network."""
    # TODO: Implement stub
    def run(self):
        pass

class OutboundBootstrapRegister(Command):
    """Register with the Bootstrap Node."""
    def run(self):
        msg = 'Registering with Bootstrap Node %s:%s'
        log(msg % (self.client.bootstrap.address, self.client.bootstrap.port))

        bootstrap = Socket(self.client.bootstrap.address,
          self.client.bootstrap.port)

        # Register Message
        bootstrap.send('0:%s' % self.client.bootstrap.port)


# BootstrapRequestPeerList


class InboundBootstrapRequestPeerList(Command):
    """Respond with BootstrapResponsePeerList."""
    # TODO: Implement stub
    def run(self):
        pass


class OutboundBootstrapRequestPeerList(Command):
    """Request an updated Peer List from the Bootstrap Node."""
    def run(self):
        msg = 'Requesting Peer List from Bootstrap Node %s:%s'
        log(msg % (self.client.bootstrap.address, self.client.bootstrap.port))

        bootstrap = Socket(self.client.bootstrap.address,
          self.client.bootstrap.port)

        # Request Peer List Message
        bootstrap.send('1:3')

        peer_list_response = bootstrap.recv()
        log('Received Peer List Response: %s' % peer_list_response)

        peerlist = []
        for item in peer_list_response.split('\n')[0:-1]:
            node = item.split(',')
            peerlist.append((node[0], node[1]))

        # update peer list with any new peers
        for peer in peerlist:
            if peer not in self.client.peers:
                self.client.peers.append(peer)

        # return peer_list_response


# BootstrapUnregister


class InboundBootstrapUnregister(Command):
    """Unregisters the sending peer with the network."""
    # TODO: Implement stub
    def run(self):
        pass


class OutboundBootstrapUnregister(Command):
    """Unregister with the Bootstrap Node."""
    def run(self):
        msg = 'Unregistering with Bootstrap Node %s:%s'
        log(msg % (self.client.bootstrap.address, self.client.bootstrap.port))

        bootstrap = Socket(self.client.bootstrap.address,
          self.client.bootstrap.port)

        # Unregister Message
        bootstrap.send('2:%s' % self.client.bootstrap.port)


# BootstrapKeepAlive


class InboundBootstrapKeepAlive(Command):
    """Refresh the sending peer's keepalive timer."""
    # TODO: Implement stub
    def run(self):
        pass


class OutboundBootstrapKeepAlive(Command):
    """Transmit a KeepAlive message to the Bootstrap Node."""
    def run(self):
        msg = 'Sending KeepAlive to Bootstrap Node %s:%s'
        log(msg % (self.client.bootstrap.address, self.client.bootstrap.port))

        bootstrap = Socket(self.client.bootstrap.address,
          self.client.bootstrap.port)

        # KeepAlive Message
        bootstrap.send('3:%s' % self.client.bootstrap.port)


# DownloadRequest


class InboundDownloadRequest(Command):
    """Respond with the requested file."""
    def __init__(self, client, server, port, filename):
        self.client = client
        self.server = server
        self.port = port
        self.filename = filename

    def run(self):
        log('Received Download Request from %s:%s' % (self.server, self.port))

        msg = 'Preparing to send \'%s\' to %s:%s...'
        log(msg % (self. filename, self.server, self.port))
        bootstrap = Socket(self.server, self.port)

        # send actual file contents
        with open(self.client.local_directory + '/' + self.filename, 'r') as f:
            # Download Response Message
            bootstrap.send(f.read())

        msg = 'Finished sending \'%s\' to %s:%s...'
        log(msg % (self. filename, self.server, self.port))


class OutboundDownloadRequest(Command):
    """Request a file from a peer."""
    def __init__(self, client, server, port, filename):
        self.client = client
        self.server = server
        self.port = port
        self.filename = filename

    def run(self):
        msg = 'Sending Download Request for \'%s\' to %s:%s'
        log (msg % (self.filename, self.server, self.port))

        bootstrap = Socket(self.server, self.port)

        # Send Download Message
        bootstrap.send('4:%s' % self.filename)
        unused, temp_port = bootstrap.get_port()
        bootstrap.close()

        msg = 'Waiting for response from %s:%s [%s]...'
        log(msg % (self.server, self.port, temp_port))

        # Establish server socket for response connection
        bootstrap = ServerSocket(temp_port, self.client.listen_addr)
        data = bootstrap.recv()

        log('Response received. Saving \'%s\'.' % self.filename)
        # save file to local directory
        with open(self.client.local_directory + '/' + self.filename, 'w') as f:
            f.write(data)

        log('Finished saving \'%s\'.' % self.filename)


# DownloadRequest


class InboundListRequest(Command):
    """Respond with our Peer List"""
    def __init__(self, client, server, port):
        self.client = client
        self.server = server
        self.port = port

    def run(self):
        log('Received File List Request from %s:%s' % (self.server, self.port))

        # format file list for transmission
        if len(self.filelist) > 0:
            msg = ('\n').join(self.client.filelist) + '\n'
        else:
            msg = ''

        log('Sending File List Response to %s:%s...' % (self.server, self.port))

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


class OutboundListRequest(Command):
    """Request a File List from a peer."""
    def __init__(self, client, server, port):
        self.client = client
        self.server = server
        self.port = port

    def run(self):
        log('Sending File List Request to %s:%s' % (self.server, self.port))

        bootstrap = Socket(self.server, self.port)

        # List Files Message
        bootstrap.send('5:')

        # Receive response
        filelist = bootstrap.recv()

        msg = 'Received File List response (%s:%s):\n %s'
        log(msg % (self.server, self.port, filelist))


# SearchRequest


class InboundSearchRequest(Command):
    """Check to see if we have the requested file."""
    def __init__(self, client, server, port, requesting_ip, requesting_port,
      ident, filename, ttl):
        self.client = client
        self.server = server
        self.port = port
        self.requesting_ip = requesting_ip
        self.requesting_port = requesting_port
        self.id = ident
        self.filename = filename
        self.ttl = ttl

    def run(self):
        msg = 'Received Search Request for \'%s\' from %s:%s : %s'
        log(msg % (self.filename, self.server, self.port, self.filelist))

        # if we've already seen this request, do nothing
        if self.id in self.client.seen:
            return
        # otherwise, add it to our list of seen requests for next time
        else:
            self.client.seen.add(self.id)

        # if we have this file, let the original client know
        if self.filename in self.client.filelist:
            # add Search Response to outbound queue
            command = OutboundSearchResponse(self.client, self.server,
              self.port, self.id, self.requesting_ip, self.requesting_port,
              self.filename)
            self.client.out_queue.put(command)

        # if we don't have the file and TTL > 0, forward the Search Request
        elif self.ttl > 0:
            # add Search Request to outbound queue
            command = OutboundSearchRequest(self.client, self.server, self.port,
              self.id, self.filename, self.requesting_ip, self.requesting_port,
              self.ttl - 1)
            self.client.out_queue.put(command)


class OutboundSearchRequest(Command):
    """Notify peers of your request."""
    def __init__(self, client, server, port, id, filename, requesting_ip,
      requesting_port, ttl):
        self.client = client
        self.server = server
        self.port = port
        self.id = id
        self.filename = filename
        self.requesting_ip = requesting_ip
        self.requesting_port = requesting_port
        self.ttl = ttl

    def run(self):
        msg = 'Sending Search Request for \'%s\' to %s:%s'
        log(msg % (self.filename, self.server, self.port))

        bootstrap = Socket(self.server, self.port)

        # This line causes an error for some reason, so use alt string below
        # message = '6:%s:%s:%s' % (self.id, self.filename, self.requesting_ip,
        #   self.requesting_port, self.ttl)
        message = '6:' + self.id + ':' + str(self.filename) + ':' + \
          str(self.requesting_ip) + ':' + str(self.requesting_port) + ':' + \
          str(self.ttl)

        # Search Message
        bootstrap.send(message)


# SearchResponse


class InboundSearchResponse(Command):
    """Process search response from peers."""
    def __init__(self, client, server, port, filename, responding_ip,
      responding_port):
        self.client = client
        self.server = server
        self.port = port
        self.filename = filename
        self.responding_ip
        self.responding_port

    def run(self):
        msg = 'Received File List Response from %s:%s : %s'
        log(msg % (self.server, self.port, self.filelist))

        # TODO: Display Search Results


class OutboundSearchResponse(Command):
    """Respond to a peer's search request."""
    def __init__(self, client, server, port, id, responding_ip, responding_port,
      filename):
        self.client = client
        self.server = server
        self.port = port
        self.id = id
        self.responding_ip = responding_ip
        self.responding_port = responding_port
        self.filename = filename

    def run(self):
        msg = 'Sending Search Response for \'%s\' to %s:%s'
        log(msg % (self.filename, self.server, self.port))

        bootstrap = Socket(self.server, self.port)

        # Search Response Message
        bootstrap.send('7:%s:%s:%s' % (self.id, self.responding_port,
          self.name))
