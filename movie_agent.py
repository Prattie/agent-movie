from llama_index.core.agent.react import ReActAgent
from llama_index.core.tools import FunctionTool
from typing import List, Dict, Optional
from omdb_client import OMDBClient
from mockdb import MockDatabase
from llama_index.core import Settings
from config_file import Config

class MovieAgent:
    def __init__(self):
        self.omdb_client = OMDBClient()
        self.db = MockDatabase()
        
        # Define tools for movie-related operations
        self.tools = [
            FunctionTool.from_defaults(
                fn=self.search_movies,
                name="search_movies",
                description="Search for movies in OMDB database"
            ),
            FunctionTool.from_defaults(
                fn=self.get_movie_details,
                name="get_movie_details",
                description="Get detailed information about a specific movie"
            ),
            FunctionTool.from_defaults(
                fn=self.format_movie_info,
                name="format_movie_info",
                description="Format movie information for display"
            )
        ]
        
        # Initialize ReAct agent with global settings
        llm = Settings.llm
        if llm:
            llm = llm.copy()
            llm.system_prompt = Config.SYSTEM_MESSAGES.get("movie_agent", "")
            
        self.agent = ReActAgent.from_tools(
            tools=self.tools,
            llm=llm,
            verbose=True
        )

    async def search_movies(self, query: str) -> List[Dict]:
        """Search for movies using OMDB API and local database"""
        try:
            # First try OMDB search
            movies = await self.omdb_client.search(query)
            if movies:
                # Get additional details for each movie
                detailed_movies = []
                for movie in movies[:5]:  # Limit to 5 movies for performance
                    details = await self.get_movie_details(movie['imdbID'])
                    if details:
                        detailed_movies.append(details)
                return detailed_movies
            
            # If no movies found in OMDB, try local database as fallback
            local_movies = list(self.db.movies.values())
            matching_movies = [
                movie for movie in local_movies 
                if query.lower() in movie['title'].lower()
            ]
            
            # Convert local movie format to match OMDB format
            formatted_movies = [
                {
                    'Title': movie['title'],
                    'Year': movie['year'],
                    'imdbID': movie['id'],
                    'Genre': movie['genre'],
                    'Director': movie['director'],
                    'Actors': movie['actors'],
                    'Plot': movie['plot'],
                    'imdbRating': movie.get('rating', 'N/A')
                }
                for movie in matching_movies
            ]
            
            return formatted_movies[:5]
            
        except Exception as e:
            print(f"Error searching movies: {str(e)}")
            return []

    async def get_movie_details(self, movie_id: str) -> Optional[Dict]:
        """Get detailed movie information"""
        try:
            # First try OMDB
            details = await self.omdb_client.get_details(movie_id)
            if details:
                return details
            
            # Fallback to local database
            local_movie = self.db.movies.get(movie_id)
            if local_movie:
                return {
                    'Title': local_movie['title'],
                    'Year': local_movie['year'],
                    'imdbID': local_movie['id'],
                    'Genre': local_movie['genre'],
                    'Director': local_movie['director'],
                    'Actors': local_movie['actors'],
                    'Plot': local_movie['plot'],
                    'imdbRating': local_movie.get('rating', 'N/A')
                }
            
            return None
            
        except Exception as e:
            print(f"Error getting movie details: {str(e)}")
            return None

    def format_movie_info(self, movie: Dict) -> str:
        """Format movie information for display"""
        try:
            # Handle both OMDB and local database formats
            title = movie.get('Title', movie.get('title', 'N/A'))
            year = movie.get('Year', movie.get('year', 'N/A'))
            rating = movie.get('imdbRating', movie.get('rating', 'N/A'))
            runtime = movie.get('Runtime', 'N/A')
            genre = movie.get('Genre', movie.get('genre', 'N/A'))
            actors = movie.get('Actors', movie.get('actors', 'N/A'))
            plot = movie.get('Plot', movie.get('plot', 'N/A'))
            
            return (
                f"🎬 {title} ({year})\n"
                f"⭐ Rating: {rating}\n"
                f"⏱️ Runtime: {runtime}\n"
                f"🎭 Genre: {genre}\n"
                f"👥 Cast: {actors}\n"
                f"📝 Plot: {plot[:200]}..."
            )
        except Exception as e:
            print(f"Error formatting movie info: {str(e)}")
            return "Error formatting movie information"

    async def get_movie_suggestions(self, preferences: Dict) -> List[Dict]:
        """Get movie suggestions based on user preferences"""
        try:
            if not preferences:
                return []
                
            # Create search query based on preferences
            favorite_genres = preferences.get('favorite_genres', [])
            favorite_actors = preferences.get('favorite_actors', [])
            
            suggestions = []
            if favorite_genres:
                # Search by preferred genre
                for genre in favorite_genres[:2]:  # Limit to top 2 genres
                    movies = await self.search_movies(f"{genre} movies")
                    suggestions.extend(movies)
                    
            if favorite_actors:
                # Add movies with favorite actors
                for actor in favorite_actors[:2]:  # Limit to top 2 actors
                    movies = await self.search_movies(actor)
                    suggestions.extend(movies)
            
            # Remove duplicates and limit results
            unique_suggestions = []
            seen_ids = set()
            
            for movie in suggestions:
                movie_id = movie.get('imdbID')
                if movie_id and movie_id not in seen_ids:
                    seen_ids.add(movie_id)
                    unique_suggestions.append(movie)
            
            return unique_suggestions[:5]  # Return top 5 suggestions
            
        except Exception as e:
            print(f"Error getting movie suggestions: {str(e)}")
            return []

    def _validate_movie_data(self, movie: Dict) -> bool:
        """Validate movie data has required fields"""
        required_fields = ['Title', 'Year', 'imdbID']
        return all(field in movie for field in required_fields)