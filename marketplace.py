"""
Marketplace provider interface.

Why this is separate:
Facebook Marketplace data access is not an unrestricted public scrape endpoint.
Use an approved Meta API/data partner, a user-authorized compliant connector,
or import data you are licensed to use.

Implement fetch_listings() and return normalized dictionaries:
{
  "title": str, "price": float, "market_value": float|None,
  "mileage": int|None, "city": str, "state": str,
  "listing_url": str, "source": str
}
"""

from abc import ABC, abstractmethod

class MarketplaceProvider(ABC):
    @abstractmethod
    async def fetch_listings(self, city: str, state: str, radius: int):
        raise NotImplementedError

class DemoProvider(MarketplaceProvider):
    async def fetch_listings(self, city: str, state: str, radius: int):
        return []
