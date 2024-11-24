# agents/seating_agent.py
from llama_index.core.agent.react import ReActAgent
from llama_index.core.tools import FunctionTool
from typing import List, Dict
from mockdb import MockDatabase
from llama_index.core import Settings
from config_file import Config

class SeatingAgent:
    def __init__(self):
        self.db = MockDatabase()
        
        self.tools = [
            FunctionTool.from_defaults(
                fn=self.get_available_seats,
                name="get_available_seats",
                description="Get available seats for a showtime"
            ),
            FunctionTool.from_defaults(
                fn=self.validate_seat_selection,
                name="validate_seat_selection",
                description="Validate selected seats"
            ),
            FunctionTool.from_defaults(
                fn=self.format_seat_map,
                name="format_seat_map",
                description="Format seat map for display"
            ),
            FunctionTool.from_defaults(
                fn=self.suggest_seats,
                name="suggest_seats",
                description="Suggest best available seats based on group size"
            )
        ]
        
        # Initialize ReAct agent with global settings
        llm = Settings.llm
        if llm:
            llm = llm.copy()
            llm.system_prompt = Config.SYSTEM_MESSAGES["seating_agent"]
            
        self.agent = ReActAgent.from_tools(
            tools=self.tools,
            llm=llm,
            verbose=True
        )

    async def get_available_seats(self, showtime_id: str) -> Dict:
        """Get available seats for a showtime"""
        try:
            seats = await self.db.get_available_seats(showtime_id)
            return seats
        except Exception as e:
            print(f"Error getting available seats: {str(e)}")
            return {}

    async def validate_seat_selection(self, seats: List[str], showtime_id: str) -> bool:
        """Validate if selected seats are available"""
        try:
            available_seats = await self.db.get_available_seats(showtime_id)
            return all(
                seat in available_seats 
                and available_seats[seat]["status"] == "available" 
                for seat in seats
            )
        except Exception as e:
            print(f"Error validating seats: {str(e)}")
            return False

    def format_seat_map(self, seats: Dict) -> str:
        """Format seat map for display"""
        try:
            seat_map = "\n🎬 SCREEN HERE 🎬\n\n"
            for row in "ABCDEFGH":
                row_seats = [
                    "🟦" if seats.get(f"{row}{i}", {}).get("status") == "available"
                    else "⬛" 
                    for i in range(1, 11)
                ]
                seat_map += f"{row} {' '.join(row_seats)}\n"
            return seat_map + "\n🟦 Available  ⬛ Taken\n"
        except Exception as e:
            print(f"Error formatting seat map: {str(e)}")
            return "Error displaying seat map"

    async def suggest_seats(self, showtime_id: str, group_size: int) -> List[str]:
        """Suggest best available seats for a group"""
        try:
            seats = await self.get_available_seats(showtime_id)
            best_seats = []
            
            # Prefer middle rows (D, E) for best view
            preferred_rows = "DEFCBAGH"
            
            for row in preferred_rows:
                consecutive_seats = []
                for seat_num in range(1, 11):
                    seat_id = f"{row}{seat_num}"
                    if seats.get(seat_id, {}).get("status") == "available":
                        consecutive_seats.append(seat_id)
                        if len(consecutive_seats) == group_size:
                            return consecutive_seats
                    else:
                        consecutive_seats = []
                        
            return []  # No suitable consecutive seats found
        except Exception as e:
            print(f"Error suggesting seats: {str(e)}")
            return []