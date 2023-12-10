# read all the protocol messages and respond to any "cmds" with one of the tests msgs
# also echo to console the parsed cmd and msg
# could give an alternative file of message responses
# take command line args: protocol, message_file

import logging
import argparse as arg
import socket
import threading
from functools import wraps
from threading import RLock

clients = []

# special locked wrapper
sync_lock = RLock()


def synchronized(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        with sync_lock:
            return func(*args, **kwargs)

    return wrapper


class Server(threading.Thread):
    def __init__(self, sock, address):
        threading.Thread.__init__(self)
        self._socket = sock
        self._address = address

    @synchronized
    def register_client(self):
        LOG.info("%s:%s connected." % self._address)
        clients.append(self)

    @synchronized
    def deregister_client(self):
        LOG.info("%s:%s disconnected." % self._address)
        clients.remove(self)

    def run(self):
        self.register_client()

        try:
            while True:  # continously read data
                data = self._socket.recv(1024)
                if not data:
                    break
                for c in clients:
                    c.socket.send(data)

        finally:
            self._socket.close()
            self.deregister_client()


def main():
    p = arg.ArgumentParser(description="RS232 client example (asynchronous)")
    p.add_argument(
        "--port",
        help="port to listen on (default=4999, same as the ip2serial port)",
        type=int,
        default=4999,
    )
    p.add_argument(
        "--host", help="listener host (default=127.0.0.1)", default="127.0.0.1"
    )
    p.add_argument("-d", "--debug", action="store_true", help="verbose logging")
    args = p.parse_args()

    if args.debug:
        logging.getLogger().setLevel(level=logging.DEBUG)

    # listen on the specified port
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((args.host, args.port))
    s.listen(4)

    while True:
        (sock, address) = s.accept()
        Server(sock, address).start()


main()
