from llama_index.core.agent.react import ReActAgent
from llama_index.core.tools import FunctionTool
from typing import List, Dict, Optional
from mockdb import MockDatabase
from llama_index.core import Settings
from config_file import Config

class BookingAgent:
    def __init__(self):
        self.db = MockDatabase()
        
        self.tools = [
            FunctionTool.from_defaults(
                fn=self.get_theaters,
                name="get_theaters",
                description="Get list of theaters"
            ),
            FunctionTool.from_defaults(
                fn=self.get_showtimes,
                name="get_showtimes",
                description="Get showtimes for a theater and movie"
            ),
            FunctionTool.from_defaults(
                fn=self.create_booking,
                name="create_booking",
                description="Create a new booking"
            ),
            FunctionTool.from_defaults(
                fn=self.format_booking_confirmation,
                name="format_booking_confirmation",
                description="Format the booking confirmation message"
            )
        ]
        
        # Initialize ReAct agent with global settings
        llm = Settings.llm
        if llm:
            llm = llm.copy()
            llm.system_prompt = Config.SYSTEM_MESSAGES["booking_agent"]
            
        self.agent = ReActAgent.from_tools(
            tools=self.tools,
            llm=llm,
            verbose=True
        )

    async def get_theaters(self) -> List[Dict]:
        """Get list of theaters"""
        try:
            theaters = await self.db.get_theaters()
            return theaters
        except Exception as e:
            print(f"Error getting theaters: {str(e)}")
            return []

    async def get_showtimes(self, theater_id: str, movie_id: str, date: str = None) -> List[Dict]:
        """Get showtimes for a theater and movie"""
        try:
            return await self.db.get_showtimes(theater_id, movie_id, date)
        except Exception as e:
            print(f"Error getting showtimes: {str(e)}")
            return []

    async def create_booking(self, user_id: str, showtime_id: str, seats: List[str]) -> Optional[str]:
        """Create a new booking"""
        try:
            if not user_id or not showtime_id or not seats:
                print("Missing required booking information")
                return None
            
            # Validate seats are still available
            available_seats = await self.db.get_available_seats(showtime_id)
            if not all(seat in available_seats and available_seats[seat]["status"] == "available" 
                      for seat in seats):
                print("Some selected seats are no longer available")
                return None
            
            # Create the booking
            booking_id = await self.db.create_booking(user_id, showtime_id, seats)
            return booking_id
            
        except Exception as e:
            print(f"Error creating booking: {str(e)}")
            return None

    def format_booking_confirmation(self, booking_details: Dict) -> str:
        """Format booking confirmation message - synchronous method"""
        try:
            if not booking_details:
                return "Error: No booking details available"
                
            return (
                f"🎫 Booking Confirmation\n"
                f"Booking ID: {booking_details['id']}\n"
                f"Customer Name: {booking_details['customer_name']}\n"
                f"Email: {booking_details['customer_email']}\n"
                f"Theater: {booking_details['theater_name']}\n"
                f"Movie: {booking_details['movie_title']}\n"
                f"Date: {booking_details['date']}\n"
                f"Time: {booking_details['time']}\n"
                f"Seats: {', '.join(booking_details['seats'])}\n"
                f"Total Price: ${booking_details['total_price']:.2f}\n"
                f"\nThank you for booking with us! 🎬"
            )
        except Exception as e:
            print(f"Error formatting booking confirmation: {str(e)}")
            return "Error formatting booking confirmation"