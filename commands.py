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

        # now connect to the Bootstrap node on the given portA
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
        return self.s.recv(self.port)


class Command():
    """Abstract Base Class for Inbound and Outbound Queue Commands."""
    __metaclass__  = abc.ABCMeta
    def __init__(self, client, *args, **kwargs):
        self.client = client

    @abc.abstractmethod
    def run(self):
        pass


# Bootstrap Commands


class BootstrapRegister(Command):
    """Register with the Bootstrap Node."""
    def run(self):
        logging.info('Registering with Bootstrap Node %s:%s' %
            (self.client.bootstrap_server, self.client.bootstrap_port))

        bootstrap = Socket(self.client.bootstrap_server, self.client.bootstrap_port)

        # Register Message
        bootstrap.send('0:%s' % self.client.bootstrap_port)


class BootstrapRequestPeerList(Command):
    """Request an updated Peer List from the Bootstrap Node."""
    def run(self):
        logging.info('Requesting Peer List from Bootstrap Node %s:%s' %
            (self.client.bootstrap_server, self.client.bootstrap_port))

        bootstrap = Socket(self.client.bootstrap_server, self.client.bootstrap_port)

        # Request Peer List Message
        bootstrap.send('1:3')

        peer_list_response = bootstrap.recv()
        logging.info('Received Peer List Response: %s' % peer_list_response)

        return peer_list_response


class BootstrapUnregister(Command):
    """Unregister with the Bootstrap Node."""
    def run(self):
        logging.info('Unregistering with Bootstrap Node %s:%s' %
            (self.client.bootstrap_server, self.client.bootstrap_port))

        bootstrap = Socket(self.client.bootstrap_server, self.client.bootstrap_port)

        # Unregister Message
        bootstrap.send('2:%s' % self.client.bootstrap_port)


class BootstrapKeepAlive(Command):
    """Transmit a KeepAlive message to the Bootstrap Node."""
    def run(self):
        logging.info('Sending KeepAlive to Bootstrap Node %s:%s' %
            (self.client.bootstrap_server, self.client.bootstrap_port))

        bootstrap = Socket(self.client.bootstrap_server, self.client.bootstrap_port)

        # KeepAlive Message
        bootstrap.send('3:%s' % self.client.bootstrap_port)


# Inbound Commands


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

        bootstrap = Socket(self.server, self.port)

        # add Download Response to outbound queue
        command = OutboundDownloadResponse(self.client, self.server, self.port, self.filename)
        self.client.out_queue.put(command)


class InboundDownloadResponse(Command):
    """Inbound Download Response."""
    def __init__(self, client, server, port, data, *args, **kwargs):
        self.client = client
        self.server = server
        self.port = port
        self.data = data

    def run(self):
        logging.info('Received Download Response from %s:%s' %
            (self.server, self.port))

        # save file to local directory
        filename = 'newfile.txt'
        with open(self.client.local_directory + '/' + filename) as f:
            f.write(self.data)

        # TODO: Use the actual filename!


class InboundListRequest(Command):
    """Inbound List Request."""
    def __init__(self, client, server, port, *args, **kwargs):
        self.client = client
        self.server = server
        self.port = port

    def run(self):
        logging.info('Received File List Request from %s:%s' %
            (self.server, self.port))

        # add file list response to outbound queue
        command = OutboundListResponse(self.client, self.server, self.port)
        self.client.out_queue.put(command)


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
    def __init__(self, client, server, port, requesting_ip, requesting_port, id, filename, ttl, *args, **kwargs):
        self.client = client
        self.server = server
        self.port = port
        self.requesting_ip = requesting_ip
        self.requesting_port = requesting_port
        self.id = id
        self.filename = filename
        self.ttl = ttl

    def run(self):
        logging.info('Received Search Request for \'%s\' from %s:%s : %s' %
            (self.filename, self.server, self.port, self.filelist))

        if self.filename in self.client.filelist:
            # add Search Response to outbound queue
            command = OutboundSearchResponse(self.client,
                                             self.server,
                                             self.port,
                                             self.id,
                                             self.responding_ip,
                                             self.responding_port,
                                             self.filename)
            self.client.out_queue.put(command)
        else:
            # TODO: Have I already seen this request?

            # add Search Request to outbound queue
            command = OutboundSearchRequest(self.client,
                                             self.server,
                                             self.port,
                                             self.id,
                                             self.responding_ip,
                                             self.responding_port,
                                             self.filename)
            self.client.out_queue.put(command)


class InboundSearchResponse(Command):
    """Inbound Search Response."""
    def __init__(self, client, server, port, filename, *args, **kwargs):
        self.client = client
        self.server = server
        self.port = port
        self.filename = filename

    def run(self):
        logging.info('Received File List Response from %s:%s : %s' %
            (self.server, self.port, self.filelist))

        # TODO: Display Search Results


# Outbound Commands


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

        # Download Message
        bootstrap.send('4:%s' % self.filename)


class OutboundDownloadResponse(Command):
    """Outbound Download Response."""
    def __init__(self, client, server, port, filename, *args, **kwargs):
        self.client = client
        self.server = server
        self.port = port
        self.filename = filename

    def run(self):
        logging.info('Sending \'%s\' to %s:%s' %
            (self.filename, self.server, self.port))

        bootstrap = Socket(self.server, self.port)

        # send actual file contents
        with open(self.client.local_directory + '/' + self.filename) as f:
            # Download Response Message
            bootstrap.send(f.read())




class OutboundListRequest(Command):
    """Outbound Download Request."""
    def __init__(self, client, server, port, filename, *args, **kwargs):
        self.client = client
        self.server = server
        self.port = port
        self.filename = filename

    def run(self):
        logging.info('Sending File List Request to %s:%s' %
            (self.filename, self.server, self.port))

        bootstrap = Socket(self.server, self.port)

        # List Files Message
        bootstrap.send('5:')


class OutboundListResponse(Command):
    """Outbound List Files Response."""
    def __init__(self, client, server, port, *args, **kwargs):
        self.client = client
        self.server = server
        self.port = port

    def run(self):
        logging.info('Sending File List Response to %s:%s' %
            (self.filename, self.server, self.port))

        bootstrap = Socket(self.server, self.port)

        # format file list for transmission
        if len(self.filelist) > 0:
            msg = ('\n').join(self.client.filelist) + '\n'
        else:
            msg = ''

        # List Files Response Message
        bootstrap.send(msg)


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

        # Search Message
        bootstrap.send('6:%s:%s:%s' % (self.id, self.filename, self.requesting_ip, self.requesting_port, self.ttl))


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
