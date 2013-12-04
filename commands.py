import abc

class Command():
    """Abstract Base Class for Inbound and Outbound Queue Commands."""
    __metaclass__  = abc.ABCMeta

    @abc.abstractmethod
    def run():
        pass


class InboundDownloadRequest(Command):
    def __init__(self, *args, **kwargs):
        pass

    def run():
        pass


class InboundDownloadResponse(Command):
    def __init__(self, *args, **kwargs):
        pass

    def run():
        pass


class InboundListRequest(Command):
    def __init__(self, *args, **kwargs):
        pass

    def run():
        pass


class InboundListResponse(Command):
    def __init__(self, *args, **kwargs):
        pass

    def run():
        pass


class InboundSearchRequest(Command):
    def __init__(self, *args, **kwargs):
        pass

    def run():
        pass


class InboundSearchResponse(Command):
    def __init__(self, *args, **kwargs):
        pass

    def run():
        pass


class OutboundDownloadRequest(Command):
    def __init__(self, *args, **kwargs):
        pass

    def run():
        pass


class OutboundDownloadResponse(Command):
    def __init__(self, *args, **kwargs):
        pass

    def run():
        pass


class OutboundListRequest(Command):
    def __init__(self, *args, **kwargs):
        pass

    def run():
        pass


class OutboundListResponse(Command):
    def __init__(self, *args, **kwargs):
        pass

    def run():
        pass


class OutboundSearchRequest(Command):
    def __init__(self, *args, **kwargs):
        pass

    def run():
        pass


class OutboundSearchResponse(Command):
    def __init__(self, *args, **kwargs):
        pass

    def run():
        pass
