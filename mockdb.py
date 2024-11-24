from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

class MockDatabase:
    def __init__(self):
        self.movies = {}
        self.theaters = {}
        self.showtimes = {}
        self.seats = {}
        self.bookings = {}
        self.user_preferences = {}
        self._initialize_mock_data()
    
    def _initialize_mock_data(self):
        """Initialize mock data for testing"""
        # Mock movies data
        self.movies = {
            "tt1375666": {
                "id": "tt1375666",
                "title": "Inception",
                "year": "2010",
                "genre": "Action, Adventure, Sci-Fi",
                "director": "Christopher Nolan",
                "actors": "Leonardo DiCaprio, Joseph Gordon-Levitt, Ellen Page",
                "plot": "A thief who steals corporate secrets through dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O.",
                "rating": "8.8",
                "poster": "https://example.com/inception.jpg"
            },
            "tt0468569": {
                "id": "tt0468569",
                "title": "The Dark Knight",
                "year": "2008",
                "genre": "Action, Crime, Drama",
                "director": "Christopher Nolan",
                "actors": "Christian Bale, Heath Ledger, Aaron Eckhart",
                "plot": "When the menace known as the Joker wreaks havoc and chaos on the people of Gotham, Batman must accept one of the greatest psychological and physical tests of his ability to fight injustice.",
                "rating": "9.0",
                "poster": "https://example.com/dark-knight.jpg"
            },
            "tt0111161": {
                "id": "tt0111161",
                "title": "The Shawshank Redemption",
                "year": "1994",
                "genre": "Drama",
                "director": "Frank Darabont",
                "actors": "Tim Robbins, Morgan Freeman",
                "plot": "Two imprisoned men bond over a number of years, finding solace and eventual redemption through acts of common decency.",
                "rating": "9.3",
                "poster": "https://example.com/shawshank.jpg"
            }
        }

        # Mock theaters
        self.theaters = {
            "th1": {"name": "Cinema City", "location": "Downtown"},
            "th2": {"name": "Movieplex", "location": "Westside"},
            "th3": {"name": "Star Cinema", "location": "Eastside"}
        }
        
        # Mock showtimes - now with movie references
        current_date = datetime.now()
        for theater_id in self.theaters:
            self.showtimes[theater_id] = [
                {
                    "id": f"st_{theater_id}_{i}",
                    "movie_id": list(self.movies.keys())[i % len(self.movies)],  # Rotate through movies
                    "time": (current_date + timedelta(hours=i)).strftime("%H:%M"),
                    "date": current_date.strftime("%Y-%m-%d"),
                    "price": 12.99
                }
                for i in range(4)  # 4 showtimes per theater
            ]
        
        # Initialize empty seats for each showtime
        for theater_id, shows in self.showtimes.items():
            for show in shows:
                self.seats[show["id"]] = self._create_empty_seat_map()

    def _create_empty_seat_map(self) -> Dict:
        """Create an empty seat map with 8 rows and 10 seats per row"""
        seats = {}
        for row in "ABCDEFGH":
            for seat_num in range(1, 11):
                seat_id = f"{row}{seat_num}"
                seats[seat_id] = {"status": "available", "price": 12.99}
        return seats
    
    async def get_all_movies(self) -> List[Dict]:
        """Get all movies in the database"""
        return list(self.movies.values())

    async def get_movie_details(self, movie_id: str) -> Optional[Dict]:
        """Get detailed movie information"""
        return self.movies.get(movie_id)

    async def get_user_preferences(self, user_id: str) -> Optional[Dict]:
        """Get user preferences"""
        return self.user_preferences.get(user_id)

    async def update_user_preferences(self, user_id: str, preferences: Dict) -> bool:
        """Update user preferences"""
        try:
            self.user_preferences[user_id] = preferences
            return True
        except Exception as e:
            print(f"Error updating preferences: {str(e)}")
            return False

    async def get_user_bookings(self, user_id: str) -> List[Dict]:
        """Get user's booking history"""
        return [
            booking for booking in self.bookings.values()
            if booking["user_id"] == user_id
        ]

    async def get_recent_bookings(self, limit: int = 50) -> List[Dict]:
        """Get recent bookings"""
        sorted_bookings = sorted(
            self.bookings.values(),
            key=lambda x: x["created_at"],
            reverse=True
        )
        return sorted_bookings[:limit]
    
    async def get_theaters(self) -> List[Dict]:
        """Get all theaters"""
        return [{"id": k, **v} for k, v in self.theaters.items()]
    
    async def get_showtimes(self, theater_id: str, movie_id: str, date: str) -> List[Dict]:
        """Get showtimes for a specific theater and movie"""
        return self.showtimes.get(theater_id, [])
    
    async def get_available_seats(self, showtime_id: str) -> Dict:
        """Get available seats for a showtime"""
        return self.seats.get(showtime_id, {})
    
    async def create_booking(self, user_id: str, showtime_id: str, seats: List[str]) -> Optional[str]:
        """Create a new booking"""
        booking_id = f"bk_{len(self.bookings) + 1}"
        showtime_seats = self.seats.get(showtime_id, {})
        
        # Check if seats are available
        for seat in seats:
            if seat not in showtime_seats or showtime_seats[seat]["status"] != "available":
                return None
        
        # Mark seats as booked
        for seat in seats:
            showtime_seats[seat]["status"] = "booked"
        
        # Create booking record
        self.bookings[booking_id] = {
            "user_id": user_id,
            "showtime_id": showtime_id,
            "seats": seats,
            "status": "confirmed",
            "created_at": datetime.now().isoformat()
        }
        
        return booking_id
    
    async def get_booking(self, booking_id: str) -> Optional[Dict]:
        """Get booking details"""
        return self.bookings.get(booking_id)
