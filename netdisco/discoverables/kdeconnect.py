"""Discover KDEConnect devices."""
from . import BaseDiscoverable


class Discoverable(BaseDiscoverable):
    """Add support for discovering a KDEConnect device."""

    def __init__(self, netdis):
        """Initialize the KDEConnect discovery."""
        self._netdis = netdis

    def get_entries(self):
        """Get all the KDEConnect details."""
        return self._netdis.kdeconnect.entries
