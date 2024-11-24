# utils/omdb_client.py
import aiohttp
from typing import Dict, List, Optional
from config_file import Config

class OMDBClient:
    def __init__(self):
        self.base_url = Config.OMDB_BASE_URL
        self.api_key = Config.OMDB_API_KEY
    
    async def search(self, query: str) -> List[Dict]:
        """Search for movies in OMDB"""
        async with aiohttp.ClientSession() as session:
            params = {
                "apikey": self.api_key,
                "s": query,
                "type": "movie"
            }
            async with session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("Response") == "True":
                        return data.get("Search", [])
                return []
    
    async def get_details(self, movie_id: str) -> Optional[Dict]:
        """Get detailed movie information"""
        async with aiohttp.ClientSession() as session:
            params = {
                "apikey": self.api_key,
                "i": movie_id,
                "plot": "full"
            }
            async with session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("Response") == "True":
                        return data
                return None
