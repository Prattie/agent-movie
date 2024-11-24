# config/config.py
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

class Config:
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OMDB_API_KEY = os.getenv("OMDB_API_KEY")
    
    # API Endpoints
    OMDB_BASE_URL = "http://www.omdbapi.com/"
    
    # LLM Settings
    MODEL_NAME = "gpt-3.5-turbo"
    TEMPERATURE = 0.7
    MAX_TOKENS = 1000
    
    # Application Settings
    DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Booking Settings
    MAX_SEATS_PER_BOOKING = 10
    BOOKING_EXPIRY_MINUTES = 15
    CANCELLATION_WINDOW_HOURS = 24
    
    # Theater Settings
    MOCK_THEATERS = [
        {"id": "th1", "name": "Cinema City", "location": "Downtown"},
        {"id": "th2", "name": "Movieplex", "location": "Westside"},
        {"id": "th3", "name": "Star Cinema", "location": "Eastside"}
    ]
    
    # Pricing Settings
    BASE_TICKET_PRICE = 12.99
    PREMIUM_SEAT_MARKUP = 1.5
    WEEKEND_MARKUP = 1.2
    
    # System Messages for Agents
    SYSTEM_MESSAGES = {
        "coordinator": """You are a helpful movie booking assistant. Guide users through the process of 
        finding and booking movie tickets. Be concise but friendly in your responses.""",
        
        "movie_agent": """You are a movie information specialist. Help users find movies and provide 
        accurate information about them. Include relevant details like ratings, runtime, and genre.""",
        
        "seating_agent": """You are a seating specialist. Help users select the best available seats 
        for their movie experience. Consider factors like screen distance and group seating.""",
        
        "booking_agent": """You are a booking specialist. Help users complete their movie ticket 
        booking efficiently and accurately. Handle payment processing and booking confirmations."""
    }
    
    # Error Messages
    ERROR_MESSAGES = {
        "api_error": "Sorry, we're having trouble connecting to our service.",
        "invalid_movie": "Sorry, we couldn't find that movie.",
        "invalid_seats": "Those seats are not available.",
        "booking_failed": "Sorry, we couldn't complete your booking.",
        "session_expired": "Your session has expired. Please start over."
    }
    
    # Validation Settings
    VALID_SEAT_ROWS = "ABCDEFGH"
    MAX_SEAT_NUMBER = 10
    
    @classmethod
    def validate_environment(cls):
        """Validate that all required environment variables are set"""
        required_vars = ['OPENAI_API_KEY', 'OMDB_API_KEY']
        missing_vars = [var for var in required_vars if not getattr(cls, var)]
        
        if missing_vars:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )
        return True
    
    @classmethod
    def get_seat_price(cls, seat_row: str, is_weekend: bool = False) -> float:
        """Calculate seat price based on row and day"""
        base_price = cls.BASE_TICKET_PRICE
        
        # Premium rows (closer to screen)
        if seat_row in "ABC":
            base_price *= cls.PREMIUM_SEAT_MARKUP
            
        # Weekend markup
        if is_weekend:
            base_price *= cls.WEEKEND_MARKUP
            
        return round(base_price, 2)