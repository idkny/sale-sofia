import os
from typing import Dict, Optional

from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()


class PaidProxyService:
    """Interface to PacketStream.io paid proxy service.
    Constructs authenticated proxy strings for various protocols and countries.
    """

    def __init__(self):
        self.username = os.getenv("PACKETSTREAM_USERNAME")
        self.password = os.getenv("PACKETSTREAM_PASSWORD")
        if not self.username or not self.password:
            raise ValueError("Missing PacketStream credentials in .env file")

        self.base_host = "proxy.packetstream.io"
        self.port_map = {"http": 31112, "https": 31112, "socks5": 31113}

    def get_proxy(
        self, protocol: str = "http", country: Optional[str] = None, as_dict: bool = False
    ) -> str | Dict[str, str]:
        """Generate an authenticated proxy string or requests-style dictionary.

        :param protocol: http, https, or socks5
        :param country: ISO country code (e.g., "US", "FR")
        :param as_dict: If True, return dict suitable for requests/aiohttp
        :return: proxy string or dict
        """
        if protocol not in self.port_map:
            raise ValueError(f"Unsupported protocol: {protocol}")

        port = self.port_map[protocol]
        user = f"{self.username}:{self.password}"
        if country:
            user = f"{self.username}_country-{country}:{self.password}"

        if protocol == "socks5":
            prefix = "socks5h"
        else:
            prefix = protocol

        proxy_str = f"{prefix}://{user}@{self.base_host}:{port}"

        if as_dict:
            return (
                {"http": proxy_str, "https": proxy_str}
                if protocol in ("http", "https")
                else {"all": proxy_str}  # for aiohttp or selenium-style use
            )

        return proxy_str
