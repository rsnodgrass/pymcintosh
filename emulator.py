#!/usr/bin/env python3
#
# read all the protocol messages and respond to any "cmds" with one of the tests msgs
# also echo to console the parsed cmd and msg

import logging
import argparse as arg
import socket
import threading
from functools import wraps
from threading import RLock

import coloredlogs

from pymcintosh import DeviceController

LOG = logging.getLogger(__name__)
coloredlogs.install(level="DEBUG")

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

    def handle_command(self):
        return

    def run(self):
        try:
            self.register_client()

            while True:  # continously read data
                data = self._socket.recv(1024)
                if not data:
                    break

                text = data.decode()
                text = text.replace("\r", "").replace("\n", "")

                LOG.info(f"Received {text}")

                # for c in clients:
                #    c.socket.send(data)

        finally:
            self._socket.close()
            self.deregister_client()


VALID_COMMANDS = []


def build_responses(protocol_def: dict):
    api = protocol_def.get("api")
    for group, group_def in api.items():
        LOG.debug(f"Building responses for group {group}")
        actions = group_def.get("actions")
        for action, action_def in actions.items():
            LOG.debug(f"... action {action}")
            cmd = action.get("cmd")


# FIXME: based on model, apply any overrides to the protocol to get final protocol


def main():
    p = arg.ArgumentParser(
        description="Test server that partially emulates the protocol for a specific model"
    )
    p.add_argument(
        "--port",
        help="port to listen on (default=4999, same as an IP2SL device)",
        type=int,
        default=4999,
    )
    p.add_argument("--model", default="mx160", help="device model (e.g. mx160)")
    p.add_argument(
        "--messages", help="alternative file of message responses (instead of model)"
    )
    p.add_argument(
        "--host", help="listener host (default=127.0.0.1)", default="127.0.0.1"
    )
    p.add_argument("-d", "--debug", action="store_true", help="verbose logging")
    args = p.parse_args()

    if args.debug:
        logging.getLogger().setLevel(level=logging.DEBUG)

    # listen on the specified port
    url = f"socket://{args.host}:{args.port}/"
    LOG.info(f"Listener emulating model {args.model} on {url}")

    s = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((args.host, args.port))
        s.listen(2)

        device = DeviceController.create(args.model, url)
        build_responses(device.protocol())

        # accept connections
        while True:
            (sock, address) = s.accept()
            Server(sock, address).start()

    finally:
        if s:
            s.close()


main()
