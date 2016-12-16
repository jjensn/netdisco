"""KDEconnect discovery, based on Daikin device discovery."""
import socket
import threading
import logging
import json
from pprint import pprint as pp

# pylint: disable=unused-import, import-error, no-name-in-module
try:
    # Py2
    from urlparse import unquote  # noqa
except ImportError:
    # Py3
    from urllib.parse import unquote  # noqa

from datetime import timedelta

_LOGGER = logging.getLogger(__name__)

UDP_SRC_PORT = 1714

KDECONNECT_ID = "kdeconnect.identity"

DISCOVERY_TIMEOUT = timedelta(seconds=5)

class KDEConnectError(Exception):
    pass

class KDEConnectDevice(object):
    def __init__(self, address, data):
        self._addr = address
        self.fulldata = data
        self.data = data["body"]

    @property
    def name(self):
        return self.data["deviceName"]

    @property
    def type(self):
        return self.data["deviceType"]

    @property
    def id(self):
        return self.data["deviceId"]

    @property
    def protocol_version(self):
        return self.data["protocolVersion"]

    @property
    def incoming_capabilities(self):
        return self.data["incomingCapabilities"]

    @property
    def outgoing_capabilities(self):
        return self.data["outgoingCapabilities"]

    @property
    def addr(self):
        return self._addr

    @property
    def port(self):
        return self.data["tcpPort"]

    def __repr__(self):
        return "<KDEConnectDevice %s, id=%s, host=%s:%s, v=%s, type=%s>" % (self.name, self.id, self.addr, self.port, self.protocol_version, self.type)


class KDEConnect(object):
    """Base class to discover kdeconnect devices."""

    def __init__(self):
        """Initialize the kdeconnect discovery."""
        self.entries = []
        self._lock = threading.RLock()

    def scan(self):
        """Scan the network."""
        with self._lock:
            self.update()

    def all(self):
        """Scan and return all found entries."""
        self.entries.clear()
        self.scan()
        return self.entries

    def parse_device_info(self, addr, data):
        try:
            data = json.loads(data.decode('utf-8'))
            #pp(data)
            if "type" in data and data["type"] == KDECONNECT_ID:
                dev = KDEConnectDevice(addr, data)
                _LOGGER.info("KDEConnect, found device %s", dev)
                return dev

            return None

        except Exception as ex:
            raise KDEConnectError(ex)


    def update(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(DISCOVERY_TIMEOUT.seconds)
        sock.bind(("", UDP_SRC_PORT))

        try:
            while True:
                try:
                    data, (address, _) = sock.recvfrom(1024)
                    try:
                        dev = self.parse_device_info(address, data)
                        if dev:
                            self.entries.append(dev)
                    except KDEConnectError as ex:
                        _LOGGER.error("Got an error: %s", ex)

                except socket.timeout:
                    break

        finally:
            sock.close()


def main():
    logging.basicConfig(level=logging.DEBUG)
    kdeconnect = KDEConnect()
    pp("Scanning for KDEConnect devices..")
    kdeconnect.update()
    pp(kdeconnect.entries)


if __name__ == "__main__":
    main()
