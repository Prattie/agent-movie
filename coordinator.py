from llama_index.core import Settings
from llama_index.core.agent.react import ReActAgent
from llama_index.core.tools import FunctionTool
from typing import Tuple, Dict
from movie_agent import MovieAgent
from seating_agent import SeatingAgent
from booking_agent import BookingAgent
from preferences_agent import PreferencesAgent
import re


class CoordinatorAgent:
    def __init__(self):
        # Initialize specialist agents
        self.movie_agent = MovieAgent()
        self.seating_agent = SeatingAgent()
        self.booking_agent = BookingAgent()
        self.preferences_agent = PreferencesAgent()
        
        # Define tools for the coordinator
        self.tools = [
            FunctionTool.from_defaults(
                fn=self.handle_greeting,
                name="handle_greeting",
                description="Handle initial greeting and customer details"
            ),
            FunctionTool.from_defaults(
                fn=self.handle_preferences,
                name="handle_preferences",
                description="Handle user preferences collection"
            ),
            FunctionTool.from_defaults(
                fn=self.handle_initial_state,
                name="handle_initial_state",
                description="Handle movie search and selection"
            ),
            FunctionTool.from_defaults(
                fn=self.handle_booking,
                name="handle_booking",
                description="Handle final booking process"
            )
        ]
        
        # Initialize ReAct agent with global settings
        self.agent = ReActAgent.from_tools(
            self.tools,
            verbose=True
        )

    async def process_input(self, user_input: str, context: Dict) -> str:
        """Process user input based on current state"""
        try:
            current_state = context.get("current_state", "greeting")
            response = ""
            new_state = current_state

            # Get response from current state handler
            if current_state == "greeting":
                response, new_state = await self.handle_greeting(user_input, context)
            elif current_state == "preferences":
                response, new_state = await self.handle_preferences(user_input, context)
            elif current_state == "get_email":
                response, new_state = await self.handle_email(user_input, context)
            elif current_state == "initial":
                response, new_state = await self.handle_initial_state(user_input, context)
            elif current_state == "movie_selection":
                response, new_state = await self.handle_movie_selection(user_input, context)
            elif current_state == "theater_selection":
                response, new_state = await self.handle_theater_selection(user_input, context)
            elif current_state == "seat_selection":
                response, new_state = await self.handle_seat_selection(user_input, context)
            elif current_state == "booking_confirmation":
                response, new_state = await self.handle_booking(user_input, context)
            elif current_state == "finished":
                return "Have a great day!", "finished"
            else:
                return "I'm not sure how to handle this state. Let's start over.", "greeting"
                
            context["current_state"] = new_state
            return self._format_response_with_name(response, context)
            
        except Exception as e:
            print(f"Error in process_input: {str(e)}")
            return f"An error occurred: {str(e)}. Let's try again."
    

    async def handle_greeting(self, user_input: str, context: Dict) -> Tuple[str, str]:
        """Handle initial greeting and get customer name"""
        if "customer_name" not in context or not context["customer_name"]:
            # Clean and extract name from input
            name = self._extract_name(user_input)
            
            if not name or len(name) < 2:
                return "Please tell me your name:", "greeting"
            
            context["customer_name"] = name
            return (
                f"Nice to meet you, {context['customer_name']}! "
                "Could you please provide your email address?",
                "get_email"
            )
        return "Let's get to know your movie preferences!", "preferences"

    def _extract_name(self, input_text: str) -> str:
        """Extract name from various greeting formats"""
        import re
        
        # Common patterns for name extraction
        patterns = [
            r"(?i)i am ([a-zA-Z]+)",           # "I am John"
            r"(?i)my name is ([a-zA-Z]+)",     # "My name is John"
            r"(?i)i'm ([a-zA-Z]+)",            # "I'm John"
            r"(?i)call me ([a-zA-Z]+)",        # "Call me John"
            r"(?i)this is ([a-zA-Z]+)",        # "This is John"
            r"(?i)^([a-zA-Z]+)$",              # Just "John"
            r"(?i)^hi[,\s]+([a-zA-Z]+)$",      # "Hi John"
            r"(?i)^hello[,\s]+([a-zA-Z]+)$",   # "Hello John"
            r"(?i)^hey[,\s]+([a-zA-Z]+)$"      # "Hey John"
        ]

        # Try each pattern
        for pattern in patterns:
            match = re.search(pattern, input_text)
            if match:
                name = match.group(1)
                return name.strip().title()  # Capitalize first letter

        # If no patterns match, clean and return the entire input as fallback
        # Remove common greetings and filler words
        cleaned = input_text.lower()
        for word in ['hi', 'hello', 'hey', 'i am', "i'm", 'my name is', 'this is', 'call me']:
            cleaned = cleaned.replace(word, '').strip()
        
        # Remove punctuation and extra whitespace
        cleaned = re.sub(r'[^\w\s]', '', cleaned).strip()
        
        # Return first word if multiple words exist
        if cleaned:
            return cleaned.split()[0].title()
        
        return ""

    async def handle_email(self, user_input: str, context: Dict) -> Tuple[str, str]:
        """Handle email collection"""
        # Extract email from input
        email = self._extract_email(user_input)
        
        if not email or not self._validate_email(email):
            return (
                "Please provide a valid email address "
                "(e.g., username@domain.com):", 
                "get_email"
            )
        
        context["customer_email"] = email
        name = context['customer_name']
        return (
            f"Thank you, {name}! "
            "Now, let's learn about your movie preferences.",
            "preferences"
        )

    def _extract_email(self, input_text: str) -> str:
        """Extract email from various input formats"""
        import re
        
        # Common patterns for email extraction
        patterns = [
            r"(?i)my email is[:\s]+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",  # "my email is user@domain.com"
            r"(?i)email[:\s]+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",        # "email: user@domain.com"
            r"(?i)email address[:\s]+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", # "email address: user@domain.com"
            r"(?i)here'?s my email[:\s]+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", # "here's my email: user@domain.com"
            r"(?i)you can reach me at[:\s]+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", # "you can reach me at user@domain.com"
            r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"  # Just the email
        ]

        # Try each pattern
        for pattern in patterns:
            match = re.search(pattern, input_text)
            if match:
                return match.group(1).strip().lower()

        # If no patterns match, clean and look for email-like string
        words = input_text.strip().split()
        for word in words:
            if self._validate_email(word):
                return word.lower()
        
        return ""

    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        import re
        # More comprehensive email validation pattern
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email.strip().lower()))

    def _format_response_with_name(self, response: str, context: Dict) -> str:
        """Format response using user's name consistently"""
        if 'customer_name' in context:
            # Replace various greeting formats with consistent name usage
            name = context['customer_name']
            response = re.sub(
                r'(?i)(thank you|thanks|hi|hello|hey),?\s*(.*?)!',
                f"\\1, {name}!",
                response
            )
        return response



    async def handle_preferences(self, user_input: str, context: Dict) -> Tuple[str, str]:
        """Handle user preferences collection"""
        if "preferences_state" not in context:
            context["preferences_state"] = "genres"
            return (
                "What kinds of movies do you enjoy? (You can list multiple genres, "
                "separated by commas, e.g., 'action, comedy, drama')",
                "preferences"
            )
            
        if context["preferences_state"] == "genres":
            genres = [g.strip() for g in user_input.split(",")]
            context["favorite_genres"] = genres
            context["preferences_state"] = "actors"
            return (
                "Great choices! Who are some of your favorite actors? "
                "(Separate names with commas)",
                "preferences"
            )
            
        if context["preferences_state"] == "actors":
            actors = [a.strip() for a in user_input.split(",")]
            context["favorite_actors"] = actors
            context["preferences_state"] = "times"
            return (
                "What times do you usually prefer to watch movies? "
                "(morning, afternoon, evening, or night - select multiple if applicable)",
                "preferences"
            )
            
        if context["preferences_state"] == "times":
            preferred_times = [t.strip() for t in user_input.split(",")]
            
            # Save all preferences
            preferences = {
                "favorite_genres": context["favorite_genres"],
                "favorite_actors": context["favorite_actors"],
                "preferred_times": preferred_times,
                "price_sensitivity": "medium"  # default value
            }
            
            # Save preferences to database
            await self.preferences_agent.update_preferences(
                context.get("user_id", "user123"),
                preferences
            )
            
            # Get personalized recommendations
            recommendations = await self.preferences_agent.get_personalized_recommendations(
                context.get("user_id", "user123")
            )
        
        # Format recommendations with proper key handling
        if recommendations:
            rec_text = "\nBased on your preferences, you might enjoy these movies:\n"
            for i, movie in enumerate(recommendations, 1):
                # Handle both OMDB and local database formats
                title = movie.get('Title', movie.get('title', 'Unknown Title'))
                genre = movie.get('Genre', movie.get('genre', 'N/A'))
                rec_text += f"{i}. {title} - {genre}\n"
        else:
            rec_text = ""
        
        return (
            f"Thanks for sharing your preferences!{rec_text}\n\n"
            "What movie would you like to watch today?",
            "initial"
        )
        
        return "Let's start looking for movies!", "initial"

    async def handle_initial_state(self, user_input: str, context: Dict) -> Tuple[str, str]:
        """Handle initial movie search with recommendations"""
        if user_input.lower() in ["what movies do you have", "show movies", "available movies", "list movies"]:
            # Get a list of trending movies as default options
            movies = await self.preferences_agent.get_trending_movies(10)
            if movies:
                context["available_movies"] = movies
                movie_list = "\n".join([
                    f"{i+1}. {m.get('title', m.get('Title', ''))} "
                    f"({m.get('year', m.get('Year', 'N/A'))}) - "
                    f"{m.get('genre', m.get('Genre', 'N/A'))}"
                    for i, m in enumerate(movies)
                ])
                return (
                    f"Here are some popular movies currently showing:\n{movie_list}\n\n"
                    "Which one would you like to watch? (Enter the number or search for another movie)",
                    "movie_selection"
                )
        
        # Get user preferences
        preferences = await self.preferences_agent.get_user_preferences(
            context.get("user_id", "user123")
        )
        
        # Handle recommendation requests
        if user_input.lower() in ["recommend", "suggestions", "what's good"]:
            recommendations = await self.preferences_agent.get_personalized_recommendations(
                context.get("user_id", "user123")
            )
            if recommendations:
                context["available_movies"] = recommendations
                movie_list = "\n".join([
                    f"{i+1}. {m.get('title', m.get('Title', ''))} - "
                    f"{m.get('genre', m.get('Genre', 'N/A'))}"
                    for i, m in enumerate(recommendations)
                ])
                return (
                    f"Based on your preferences, here are some recommendations:\n{movie_list}\n\n"
                    "Which movie would you like to watch? (Enter the number or type a movie name to search)",
                    "movie_selection"
                )
        
        # Regular movie search
        movies = await self.movie_agent.search_movies(user_input)
        if movies:
            context["available_movies"] = movies
            movie_list = "\n".join([
                f"{i+1}. {m.get('Title', m.get('title', ''))} "
                f"({m.get('Year', m.get('year', 'N/A'))}) - "
                f"{m.get('Genre', m.get('genre', 'N/A'))}"
                for i, m in enumerate(movies)
            ])
            
            # Add preference-based suggestion if available
            suggestion = ""
            if preferences and preferences.get('favorite_genres'):
                for movie in movies:
                    movie_genre = movie.get('Genre', movie.get('genre', '')).lower()
                    if any(genre.strip().lower() in movie_genre 
                        for genre in preferences['favorite_genres']):
                        suggestion = f"\n💡 Based on your preferences, you might especially enjoy '{movie.get('Title', movie.get('title', ''))}'!"
                        break
            
            return (
                f"I found these movies:\n{movie_list}{suggestion}\n\n"
                "Which one would you like to watch? (Enter the number or search for another movie)",
                "movie_selection"
            )
        
        # If no movies found, provide a more helpful message
        return (
            "I couldn't find any movies matching your search. You can:\n"
            "1. Try searching with a different movie name\n"
            "2. Type 'show movies' to see what's available\n"
            "3. Type 'recommend' for personalized suggestions\n"
            "What would you like to do?",
            "initial"
        )

    async def handle_movie_selection(self, user_input: str, context: Dict) -> Tuple[str, str]:
        """Handle movie selection"""
        try:
            selection = int(user_input) - 1
            movies = context.get("available_movies", [])
            if 0 <= selection < len(movies):
                selected_movie = movies[selection]
                context["selected_movie"] = selected_movie
                theaters = await self.booking_agent.get_theaters()
                theater_list = "\n".join([f"{i+1}. {t['name']} ({t['location']})" 
                                        for i, t in enumerate(theaters)])
                context["available_theaters"] = theaters
                return (
                    f"Great choice, {context['customer_name']}! '{selected_movie['Title']}' is playing at these theaters:\n"
                    f"{theater_list}\n\nWhich theater would you prefer? (Enter the number)",
                    "theater_selection"
                )
            return "Invalid selection. Please choose a number from the list.", "movie_selection"
        except ValueError:
            return "Please enter a valid number.", "movie_selection"

    async def handle_theater_selection(self, user_input: str, context: Dict) -> Tuple[str, str]:
        """Handle theater selection"""
        try:
            selection = int(user_input) - 1
            theaters = context.get("available_theaters", [])
            if 0 <= selection < len(theaters):
                selected_theater = theaters[selection]
                context["selected_theater"] = selected_theater
                showtimes = await self.booking_agent.get_showtimes(
                    selected_theater["id"],
                    context["selected_movie"]["imdbID"],
                    None  # You can add date selection later
                )
                context["available_showtimes"] = showtimes
                showtime_list = "\n".join([f"{i+1}. {s['time']} - ${s['price']}"
                                         for i, s in enumerate(showtimes)])
                return (
                    f"Available showtimes at {selected_theater['name']}:\n"
                    f"{showtime_list}\n\nWhich showtime would you prefer? (Enter the number)",
                    "seat_selection"
                )
            return "Invalid selection. Please choose a number from the list.", "theater_selection"
        except ValueError:
            return "Please enter a valid number.", "theater_selection"

    async def handle_seat_selection(self, user_input: str, context: Dict) -> Tuple[str, str]:
        """Handle seat selection"""
        try:
            selection = int(user_input) - 1
            showtimes = context.get("available_showtimes", [])
            if 0 <= selection < len(showtimes):
                selected_showtime = showtimes[selection]
                # Store the complete showtime object
                context["selected_showtime"] = {
                    "id": f"st_{context['selected_theater']['id']}_{selection}",  # Generate proper showtime ID
                    "time": selected_showtime["time"],
                    "date": selected_showtime["date"],
                    "price": selected_showtime["price"]
                }
                
                # Get and display available seats
                available_seats = await self.seating_agent.get_available_seats(context["selected_showtime"]["id"])
                seat_map = self.seating_agent.format_seat_map(available_seats)
                context["available_seats"] = available_seats
                
                return (
                    f"Here's the seating map:\n{seat_map}\n"
                    "Please enter your seat selections (e.g., 'A1 A2' for multiple seats):",
                    "booking_confirmation"
                )
            return "Invalid selection. Please choose a number from the list.", "seat_selection"
        except ValueError:
            return "Please enter a valid number.", "seat_selection"

    async def handle_booking(self, user_input: str, context: Dict) -> Tuple[str, str]:
        """Handle final booking process"""
        try:
            if context.get("booking_completed"):
                # Handle post-booking interactions
                if user_input.lower() in ['thanks', 'thank you', 'bye', 'goodbye', 'no']:
                    return (
                        f"Thank you for using our service, {context['customer_name']}! "
                        f"Your booking confirmation and tickets have been sent to {context['customer_email']}. "
                        "Have a great time at the movies! 👋",
                        "finished"
                    )
                elif user_input.lower() in ['yes', 'yeah', 'sure', 'ok']:
                    # Reset necessary context for new booking
                    context.update({
                        "current_state": "initial",
                        "selected_movie": None,
                        "selected_theater": None,
                        "selected_showtime": None,
                        "selected_seats": None,
                        "booking_completed": False
                    })
                    return (
                        "What movie would you like to watch?",
                        "initial"
                    )

            # First time handling seat selection or if we need to select seats again
            if "selected_seats" not in context or context.get("selecting_seats", True):
                seats = user_input.upper().replace("'", "").strip().split()
                available_seats = context.get("available_seats", {})

                # Validate seat format
                valid_format = all(
                    len(seat) in [2, 3] and 
                    seat[0] in "ABCDEFGH" and 
                    seat[1:].isdigit() and 
                    1 <= int(seat[1:]) <= 10 
                    for seat in seats
                )

                if not valid_format:
                    return (
                        "Invalid seat format. Please use format like 'A1 A2' or 'B1 B2'.", 
                        "booking_confirmation"
                    )

                # Validate seat availability
                if all(seat in available_seats and available_seats[seat]["status"] == "available" 
                      for seat in seats):
                    # Store the selected seats in context
                    context["selected_seats"] = seats
                    context["selecting_seats"] = False  # Mark seat selection as complete
                    total_price = sum(float(available_seats[seat]["price"]) for seat in seats)
                    context["total_price"] = total_price

                    # Create booking summary
                    booking_summary = (
                        f"Booking Summary for {context['customer_name']}:\n"
                        f"Email: {context['customer_email']}\n"
                        f"Movie: {context['selected_movie']['Title']}\n"
                        f"Theater: {context['selected_theater']['name']}\n"
                        f"Time: {context['selected_showtime']['time']}\n"
                        f"Seats: {', '.join(seats)}\n"
                        f"Total Price: ${total_price:.2f}\n\n"
                        f"Would you like to confirm your booking? (Yes/No)"
                    )
                    return (booking_summary, "booking_confirmation")

                return (
                    "Some of the selected seats are not available. Please choose different seats.", 
                    "booking_confirmation"
                )

            # Handle booking confirmation
            if not context.get("selecting_seats", True):
                if user_input.lower() in ['yes', 'y', 'confirm', 'yeah', 'yep']:
                    showtime_id = context["selected_showtime"]["id"]
                    
                    # In a real app, user_id would come from user authentication
                    booking_id = await self.booking_agent.create_booking(
                        user_id="user123",
                        showtime_id=showtime_id,
                        seats=context["selected_seats"]
                    )
                    
                    if booking_id:
                        booking_details = {
                            "id": booking_id,
                            "customer_name": context["customer_name"],
                            "customer_email": context["customer_email"],
                            "theater_name": context["selected_theater"]["name"],
                            "movie_title": context["selected_movie"]["Title"],
                            "date": context["selected_showtime"]["date"],
                            "time": context["selected_showtime"]["time"],
                            "seats": context["selected_seats"],
                            "total_price": context["total_price"]
                        }
                        
                        confirmation = self.booking_agent.format_booking_confirmation(booking_details)
                        context["booking_completed"] = True  # Mark booking as completed
                        return (
                            f"{confirmation}\n\n"
                            "Would you like to book another movie? (Yes/No)",
                            "booking_confirmation"
                        )
                    
                    return (
                        "Sorry, there was an error processing your booking. Please try again.", 
                        "booking_confirmation"
                    )
                    
                elif user_input.lower() in ['no', 'n', 'cancel']:
                    # Reset the seat selection process
                    context["selecting_seats"] = True
                    if "selected_seats" in context:
                        del context["selected_seats"]
                    return ("Booking cancelled. Would you like to start over?", "initial")
                else:
                    return (
                        "Please confirm with 'yes' or 'no' to proceed with the booking.", 
                        "booking_confirmation"
                    )

            # If we get here something went wrong, reset to seat selection
            context["selecting_seats"] = True
            if "selected_seats" in context:
                del context["selected_seats"]
            return (
                "Let's try again. Please enter your seat selections (e.g., 'A1 A2' for multiple seats):",
                "booking_confirmation"
            )

        except Exception as e:
            print(f"Error in handle_booking: {str(e)}")
            return (
                "An error occurred while processing your booking. Please try again.", 
                "booking_confirmation"
            )