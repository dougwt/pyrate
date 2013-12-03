import abc

class Command():
    """Abstract Base Class for Inbound and Outbound Queue Commands."""
    __metaclass__  = abc.ABCMeta

    @abc.abstractmethod
    def run():
        pass

class InboundDownloadRequest(Command):
    """One liner description."""
    def __init__(self, *args, **kwargs):
        pass

    def run():
        pass

class InboundDownloadResponse(Command):
    """One liner description."""
    def __init__(self, *args, **kwargs):
        pass

    def run():
        pass

class InboundListRequest(Command):
    """One liner description."""
    def __init__(self, *args, **kwargs):
        pass

    def run():
        pass

class InboundListResponse(Command):
    """One liner description."""
    def __init__(self, *args, **kwargs):
        pass

    def run():
        pass

class InboundSearchRequest(Command):
    """One liner description."""
    def __init__(self, *args, **kwargs):
        pass

    def run():
        pass

class InboundSearchResponse(Command):
    """One liner description."""
    def __init__(self, *args, **kwargs):
        pass

    def run():
        pass

class OutboundDownloadRequest(Command):
    """One liner description."""
    def __init__(self, *args, **kwargs):
        pass

    def run():
        pass

class OutboundDownloadResponse(Command):
    """One liner description."""
    def __init__(self, *args, **kwargs):
        pass

    def run():
        pass

class OutboundListRequest(Command):
    """One liner description."""
    def __init__(self, *args, **kwargs):
        pass

    def run():
        pass

class OutboundListResponse(Command):
    """One liner description."""
    def __init__(self, *args, **kwargs):
        pass

    def run():
        pass

class OutboundSearchRequest(Command):
    """One liner description."""
    def __init__(self, *args, **kwargs):
        pass

    def run():
        pass

class OutboundSearchResponse(Command):
    """One liner description."""
    def __init__(self, *args, **kwargs):
        pass

    def run():
        pass
