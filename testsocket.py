import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('localhost', 63339))
msg = "Hello, World!"
s.sendall(msg)
