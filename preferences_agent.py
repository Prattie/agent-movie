from llama_index.core.agent.react import ReActAgent
from llama_index.core.tools import FunctionTool
from llama_index.core import VectorStoreIndex, Document, Settings
from typing import List, Dict, Optional
from mockdb import MockDatabase
from movie_agent import MovieAgent
from config_file import Config
import json

class PreferencesAgent:
    def __init__(self):
        self.db = MockDatabase()
        self.movie_agent = MovieAgent()  # Add MovieAgent instance
        
        # Initialize vector store for movie data
        self.movie_index = self._initialize_movie_index()
        
        self.tools = [
            FunctionTool.from_defaults(
                fn=self.get_user_preferences,
                name="get_user_preferences",
                description="Get user's movie preferences"
            ),
            FunctionTool.from_defaults(
                fn=self.update_preferences,
                name="update_preferences",
                description="Update user preferences"
            ),
            FunctionTool.from_defaults(
                fn=self.get_personalized_recommendations,
                name="get_personalized_recommendations",
                description="Get movie recommendations based on user preferences"
            ),
            FunctionTool.from_defaults(
                fn=self.analyze_booking_history,
                name="analyze_booking_history",
                description="Analyze user's booking history for patterns"
            ),
            FunctionTool.from_defaults(
                fn=self.get_trending_movies,
                name="get_trending_movies",
                description="Get currently trending movies"
            )
        ]
        
        # Initialize ReAct agent
        llm = Settings.llm
        if llm:
            llm = llm.copy()
            llm.system_prompt = Config.SYSTEM_MESSAGES.get("preferences_agent", "")
        
        self.agent = ReActAgent.from_tools(
            tools=self.tools,
            llm=llm,
            verbose=True
        )

    def _initialize_movie_index(self) -> VectorStoreIndex:
        """Initialize vector store index for movie data synchronously"""
        try:
            # Get movies directly from the mock database
            movies = self.db.movies.values()
            
            # Create documents from movie data
            movie_docs = []
            for movie in movies:
                content = f"""
                Title: {movie['title']}
                Genre: {movie['genre']}
                Director: {movie['director']}
                Actors: {movie['actors']}
                Plot: {movie['plot']}
                """
                movie_docs.append(Document(text=content, metadata=movie))
            
            # Create vector store index
            return VectorStoreIndex.from_documents(movie_docs)
            
        except Exception as e:
            print(f"Error initializing movie index: {str(e)}")
            return None

    async def get_personalized_recommendations(self, user_id: str, limit: int = 5) -> List[Dict]:
        """Get personalized movie recommendations"""
        try:
            preferences = await self.get_user_preferences(user_id)
            if not preferences:
                return await self.get_trending_movies(limit)

            # First try OMDB search for user preferences
            omdb_recommendations = await self.movie_agent.get_movie_suggestions(preferences)
            if omdb_recommendations:
                return omdb_recommendations

            # If no OMDB results, fall back to local database and vector search
            query = f"""
            Find movies with genres {', '.join(preferences['favorite_genres'])} 
            or starring {', '.join(preferences['favorite_actors'])}
            """

            # Use query engine to find relevant movies
            query_engine = self.movie_index.as_query_engine()
            response = query_engine.query(query)
            
            # Process and rank results
            recommendations = self._rank_recommendations(response.source_nodes, preferences)
            return recommendations[:limit]
            
        except Exception as e:
            print(f"Error getting recommendations: {str(e)}")
            return []

    async def get_user_preferences(self, user_id: str) -> Dict:
        """Get user's movie preferences"""
        try:
            preferences = await self.db.get_user_preferences(user_id)
            return preferences or {
                "favorite_genres": [],
                "favorite_actors": [],
                "preferred_times": [],
                "preferred_theaters": [],
                "price_sensitivity": "medium"
            }
        except Exception as e:
            print(f"Error getting user preferences: {str(e)}")
            return {
                "favorite_genres": [],
                "favorite_actors": [],
                "preferred_times": [],
                "preferred_theaters": [],
                "price_sensitivity": "medium"
            }

    async def update_preferences(self, user_id: str, preferences: Dict) -> bool:
        """Update user preferences"""
        try:
            # Validate preferences format
            required_fields = [
                'favorite_genres', 
                'favorite_actors', 
                'preferred_times'
            ]
            if not all(field in preferences for field in required_fields):
                print("Missing required preference fields")
                return False

            # Clean and normalize preferences
            cleaned_preferences = {
                "favorite_genres": [
                    genre.strip().lower() 
                    for genre in preferences.get('favorite_genres', [])
                ],
                "favorite_actors": [
                    actor.strip().lower() 
                    for actor in preferences.get('favorite_actors', [])
                ],
                "preferred_times": [
                    time.strip().lower() 
                    for time in preferences.get('preferred_times', [])
                ],
                "preferred_theaters": preferences.get('preferred_theaters', []),
                "price_sensitivity": preferences.get('price_sensitivity', 'medium')
            }

            # Update preferences in database
            return await self.db.update_user_preferences(user_id, cleaned_preferences)
            
        except Exception as e:
            print(f"Error updating preferences: {str(e)}")
            return False
        
    def _rank_recommendations(self, movies: List[Dict], preferences: Dict) -> List[Dict]:
        """Rank movie recommendations based on user preferences"""
        ranked_movies = []
        for movie in movies:
            score = 0
            metadata = movie.metadata
            
            # Score based on genre match
            for genre in metadata['genre'].split(','):
                if genre.strip() in preferences['favorite_genres']:
                    score += 2
                    
            # Score based on actor match
            for actor in metadata['actors'].split(','):
                if actor.strip() in preferences['favorite_actors']:
                    score += 1
                    
            ranked_movies.append({
                'movie': metadata,
                'score': score
            })
            
        # Sort by score and return movies
        return [item['movie'] for item in sorted(ranked_movies, 
                key=lambda x: x['score'], reverse=True)]

    async def analyze_booking_history(self, user_id: str) -> Dict:
        """Analyze user's booking history for patterns"""
        try:
            bookings = await self.db.get_user_bookings(user_id)
            if not bookings:
                return {}

            analysis = {
                'favorite_genres': {},
                'favorite_actors': {},
                'preferred_times': {},
                'preferred_theaters': {},
                'average_spending': 0.0
            }

            total_spent = 0
            for booking in bookings:
                # Analyze genres
                for genre in booking['movie']['genre'].split(','):
                    genre = genre.strip()
                    analysis['favorite_genres'][genre] = \
                        analysis['favorite_genres'].get(genre, 0) + 1

                # Analyze actors
                for actor in booking['movie']['actors'].split(','):
                    actor = actor.strip()
                    analysis['favorite_actors'][actor] = \
                        analysis['favorite_actors'].get(actor, 0) + 1

                # Analyze preferred times
                time_slot = self._get_time_slot(booking['showtime'])
                analysis['preferred_times'][time_slot] = \
                    analysis['preferred_times'].get(time_slot, 0) + 1

                # Analyze theaters
                theater = booking['theater']['name']
                analysis['preferred_theaters'][theater] = \
                    analysis['preferred_theaters'].get(theater, 0) + 1

                total_spent += booking['total_price']

            # Calculate average spending
            if bookings:  # Avoid division by zero
                analysis['average_spending'] = total_spent / len(bookings)

            # Sort and get top items
            analysis['favorite_genres'] = dict(sorted(
                analysis['favorite_genres'].items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:3])
            
            analysis['favorite_actors'] = dict(sorted(
                analysis['favorite_actors'].items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:3])

            return analysis

        except Exception as e:
            print(f"Error analyzing booking history: {str(e)}")
            return {}

    def _get_time_slot(self, time: str) -> str:
        """Convert time to time slot category"""
        hour = int(time.split(':')[0])
        if hour < 12:
            return 'morning'
        elif hour < 17:
            return 'afternoon'
        elif hour < 20:
            return 'evening'
        return 'night'

    async def get_trending_movies(self, limit: int = 5) -> List[Dict]:
        """Get currently trending movies based on recent bookings"""
        try:
            # Get recent bookings
            recent_bookings = await self.db.get_recent_bookings()
            
            # Count movie occurrences
            movie_counts = {}
            for booking in recent_bookings:
                movie_id = booking['movie']['id']
                movie_counts[movie_id] = movie_counts.get(movie_id, 0) + 1
            
            # Get top movies
            top_movie_ids = sorted(
                movie_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:limit]
            
            # Get movie details
            trending_movies = []
            for movie_id, _ in top_movie_ids:
                movie = await self.db.get_movie_details(movie_id)
                if movie:
                    trending_movies.append(movie)
            
            return trending_movies
            
        except Exception as e:
            print(f"Error getting trending movies: {str(e)}")
            return []