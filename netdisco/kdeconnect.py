"""KDEconnect discovery, based on Daikin device discovery."""
import socket
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
    """ Wrapper for device initialization failures. """
    pass


class KDEConnectDevice(object):
    """ A wrapper for device info. """
    def __init__(self, address, data):
        self._addr = address
        self.fulldata = data
        self.data = data["body"]

    @property
    def name(self):
        """ Name as reported by device. """
        return self.data["deviceName"]

    @property
    def device_type(self):
        """ Device type. """
        return self.data["deviceType"]

    @property
    def device_id(self):
        """ device ID. """
        return self.data["deviceId"]

    @property
    def protocol_version(self):
        """ KDE connect protocol version. """
        return self.data["protocolVersion"]

    @property
    def incoming_capabilities(self):
        """ Supported incoming caps. """
        return self.data["incomingCapabilities"]

    @property
    def outgoing_capabilities(self):
        """ Supported outgoing caps. """
        return self.data["outgoingCapabilities"]

    @property
    def addr(self):
        """ Device's IP address. """
        return self._addr

    @property
    def port(self):
        """ TCP port for connecting to the device. """
        return self.data["tcpPort"]

    def to_dict(self):
        """ Returns a dict to be passed onwards. """
        return {'name': self.name,
                'device_id': self.device_id,
                'addr': self.addr,
                'port': self.port,
                'protocol_version': self.protocol_version,
                'type': self.device_type,
                'incoming_caps': self.incoming_capabilities,
                'outgoing_caps': self.outgoing_capabilities}

    def __repr__(self):
        return "<KDEConnectDevice %s, id=%s, host=%s:%s, v=%s, type=%s>" % \
               (self.name, self.device_id, self.addr,
                self.port, self.protocol_version, self.device_type)


class KDEConnect(object):
    """Base class to discover kdeconnect devices."""

    def __init__(self):
        """Initialize the kdeconnect discovery."""
        self.entries = []

    def scan(self):
        """Scan the network."""
        self.update()

    def all(self):
        """Scan and return all found entries."""
        self.entries.clear()
        self.scan()
        return self.entries

    def parse_device_info(self, addr, data):
        """ Parses the response from a device and returns device object. """
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
        """ Read notifications from the socket. """
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
