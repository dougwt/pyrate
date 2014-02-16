# Pyrate

- [Introduction](#introduction)
- [Message protocol](#message-protocol)
    - [Bootstrap protocol](#bootstrap-protocol)
    - [Peer protocol](#peer-protocol)
- [Client](#client)
    - [Starting a simple client](#starting-a-simple-client)
    - [Client parameters](#client-parameters)
    - [Example client code](#example-client-code)
    - [Bootstrap client](#bootstrap-client)
- [Command objects](#command-objects)
    - [Internal](#internal)
        - [Decode](#decode)
    - [Bootstrap](#bootstrap)
        - [BootstrapRegister](#bootstrapregister)
        - [BootstrapUnregister](#bootstrapunregister)
        - [BootstrapRequestPeerList](#bootstraprequestpeerlist)
        - [BootstrapKeepAlive](#bootstrapkeepalive)
    - [Peer](#peer)
        - [DownloadRequest](#downloadrequest)
        - [ListRequest](#listrequest)
        - [SearchRequest](#searchrequest)
        - [SearchResponse](#searchresponse)
    - [Command sequence diagram](#command-sequence-diagrams)
- [Feedback](#feedback)

## Introduction

Pyrate is a primitive P2P filesharing client implemented in Python. Using
sockets and a simple protocol, Pyrate clients maintain a network of peers used
to distribute files to one another.

Each client must register with a Bootstrap node before its connection info can
be distributed to any available peers.

At this point in development, Pyrate is intended for use with text files only.
I have not had a chance to test it with binary files, so proceed at your own
risk.

The project was originally the
[final assignment](http://faculty.washington.edu/lagesse/FinalProj.html) for a
Network Design course taught by Professor Brent Lagesse. After finishing the
course, I chose to continue working on the project because it allows me to
explore the following concepts:

- Producer/Consumer design pattern
- Queueing
- Multithreading
- Sockets
- Peer-to-peer networking

## Message protocol

Pyrate currently uses the same simple protocol provided by Professor Brent
Lagesse. It includes support for the following:

### Bootstrap protocol

Message | Format
--- | ---
Register | `0:ListeningPort`
Request Peer List | `1:MaxNumberOfPeersRequested`
Response Peer List | `IPAddress1,PortNumber1\nIPAddress2,PortNumber2\n (etc.)`
Unregister | `2:ListeningPort`
Keepalive | `3:ListeningPort`

### Peer protocol

Message | Format
--- | ---
Download Response | `FILE`
List Files | `5:`
List Files Response | `Filename1\nFilename2\n (etc.)`
Search | `6:ID:File String:RequestingIP:RequestingPort:TTL`
Search Response | `7:ID:RespondingIP:RespondingPort:Filename`

## Client

### Starting a simple client

The Pyrate network relies on Bootstrap nodes to track available peers for
clients to communicate with.

**TODO:** Finish section

### Client parameters

**bootstrap_addr**
> IP Address of the Bootstrap node you wish to register with

**bootstrap_port**
> Port number of the Bootstrap node you wish to register with

**listen_addr**
> Local address to listen to for incoming connections

**listen_port**
> Local port number to listen to for incoming connections

**keepalive_refresh**
> Number of seconds to wait between KeepAlive requests

**filemonitor_refresh**
> Number of seconds to wait between updating the local file list

**local_directory**
> Path to a local directory to share on the Pyrate network

**log_file**
> Path to a local file containing log information

**max_workers**
> Maximum number of simultaneous worker threads available to process Commands
from the queue

### Example client code

```python
bootstrap_address = 'localhost'
bootstrap_port = 79422
listen_address = 'localhost'
listen_port = 99641
keepalive_refresh = 600
filemonitor_refresh = 60
local_directory = '~/pyrate-files'
log_file = 'pyrate.log'
max_workers = 4

c = Client(
  bootstrap_address,
  bootstrap_port,
  listen_address,
  listen_port,
  keepalive_refresh,
  filemonitor_refresh,
  local_directory,
  log_file,
  max_workers)

c.start()
c.quit()
```

### Bootstrap client

The Pyrate network relies on Bootstrap nodes to track available peers for
clients to communicate with. Bootstrap nodes may be run standalone by
instantiating the `Bootstrap` class.

**TODO:** Finish section

## Command objects

**TODO:** Add sequence diagrams for each command type; describe Inbound/Outbound

### Internal

##### Decode

### Bootstrap

##### BootstrapRegister

##### BootstrapUnregister

##### BootstrapRequestPeerList

##### BootstrapKeepAlive

### Peer

##### DownloadRequest

##### ListRequest

##### SearchRequest

##### SearchResponse

### Typical command sequence

**TODO:** Add sequence diagram showing typical command sequence

## Feedback

Suggestions/improvements [welcome](https://github.com/dougwt/pyrate/issues)!
