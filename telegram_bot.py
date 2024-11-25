from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from main_file import MovieBookingSystem
from movie_agent import MovieAgent
import asyncio
from typing import Dict, Any
import os
import re
from rich.console import Console

console = Console()

# Define conversation states
GREETING, GET_NAME, GET_EMAIL, MOVIE_SEARCH, SELECT_MOVIE, SELECT_THEATER, SELECT_SHOWTIME, SELECT_SEATS, CONFIRM_BOOKING = range(9)

class TelegramMovieBot:
    def __init__(self, token: str):
        self.token = token
        self.booking_system = MovieBookingSystem()
        self.movie_agent = MovieAgent()  # Initialize MovieAgent directly
        self.user_contexts: Dict[int, Dict[str, Any]] = {}
        
    def _extract_name(self, input_text: str) -> str:
        """Extract name from various greeting formats"""
        patterns = [
            r"(?i)i am ([a-zA-Z]+)",
            r"(?i)my name is ([a-zA-Z]+)",
            r"(?i)i'm ([a-zA-Z]+)",
            r"(?i)call me ([a-zA-Z]+)",
            r"(?i)this is ([a-zA-Z]+)",
            r"(?i)^([a-zA-Z]+)$",
            r"(?i)^hi[,\s]+([a-zA-Z]+)$",
            r"(?i)^hello[,\s]+([a-zA-Z]+)$",
            r"(?i)^hey[,\s]+([a-zA-Z]+)$"
        ]

        for pattern in patterns:
            match = re.search(pattern, input_text)
            if match:
                name = match.group(1)
                return name.strip().title()

        cleaned = input_text.lower()
        for word in ['hi', 'hello', 'hey', 'i am', "i'm", 'my name is', 'this is', 'call me']:
            cleaned = cleaned.replace(word, '').strip()
        
        cleaned = re.sub(r'[^\w\s]', '', cleaned).strip()
        
        if cleaned:
            return cleaned.split()[0].title()
        
        return ""

    def _extract_email(self, input_text: str) -> str:
        """Extract email from various input formats"""
        patterns = [
            r"(?i)my email is[:\s]+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
            r"(?i)email[:\s]+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
            r"(?i)email address[:\s]+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
            r"(?i)here'?s my email[:\s]+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
            r"(?i)you can reach me at[:\s]+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
            r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"
        ]

        for pattern in patterns:
            match = re.search(pattern, input_text)
            if match:
                return match.group(1).strip().lower()

        words = input_text.strip().split()
        for word in words:
            if self._validate_email(word):
                return word.lower()
        
        return ""

    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email.strip().lower()))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start the conversation and ask for user's name."""
        user_id = update.effective_user.id
        self.user_contexts[user_id] = {
            "current_state": "greeting",
            "selected_movie": None,
            "selected_theater": None,
            "selected_showtime": None,
            "selected_seats": None,
            "customer_name": None,
            "customer_email": None
        }
        
        await update.message.reply_text(
            "Welcome to Movie Booking Assistant! 🎬\n"
            "I am Max, your Movie Booking Assistant. May I know your name?"
        )
        return GET_NAME

    async def get_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Store the name and ask for email."""
        user_id = update.effective_user.id
        input_text = update.message.text
        
        name = self._extract_name(input_text)
        
        if not name or len(name) < 2:
            await update.message.reply_text(
                "Please provide a valid name. You can simply type your name or say "
                "'My name is [your name]'."
            )
            return GET_NAME
        
        self.user_contexts[user_id]["customer_name"] = name
        
        await update.message.reply_text(
            f"Nice to meet you, {name}! "
            "Please share your email address for booking confirmation."
        )
        return GET_EMAIL

    async def get_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Store the email and start movie search."""
        user_id = update.effective_user.id
        input_text = update.message.text
        
        email = self._extract_email(input_text)
        
        if not email or not self._validate_email(email):
            await update.message.reply_text(
                "Please provide a valid email address "
                "(e.g., username@domain.com)."
            )
            return GET_EMAIL
        
        self.user_contexts[user_id]["customer_email"] = email
        name = self.user_contexts[user_id]["customer_name"]
        
        await update.message.reply_text(
            f"Thank you, {name}! What kind of movie would you like to watch? "
            "You can search by title, genre, or actor."
        )
        return MOVIE_SEARCH

    async def search_movies(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Search for movies based on user input."""
        user_id = update.effective_user.id
        search_query = update.message.text.strip()
        
        try:
            # First try local database through MockDatabase
            local_movies = await self.booking_system.coordinator.booking_agent.db.get_all_movies()
            matching_movies = [
                movie for movie in local_movies 
                if search_query.lower() in movie['title'].lower() or
                   search_query.lower() in movie['genre'].lower()
            ]
            
            if not matching_movies:
                # Try OMDB search through movie agent
                movies = await self.movie_agent.search_movies(search_query)
                if movies:
                    matching_movies = movies

            if not matching_movies:
                await update.message.reply_text(
                    "I couldn't find any movies matching your search. "
                    "Please try another search term or try searching by a specific movie title."
                )
                return MOVIE_SEARCH
            
            # Format movie options for display
            movie_text = "Here are some movies that match your search:\n\n"
            keyboard = []
            
            for movie in matching_movies[:5]:  # Limit to 5 movies
                # Handle both OMDB and local database formats
                title = movie.get('Title', movie.get('title', 'Unknown'))
                year = movie.get('Year', movie.get('year', ''))
                genre = movie.get('Genre', movie.get('genre', 'Unknown genre'))
                
                movie_text += f"🎬 {title} ({year}) - {genre}\n"
                keyboard.append([f"{title} ({year})"])
            
            keyboard.append(["Search Again"])
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
            
            # Store movies in context for later reference
            self.user_contexts[user_id]['available_movies'] = matching_movies
            
            await update.message.reply_text(
                movie_text,
                reply_markup=reply_markup
            )
            return SELECT_MOVIE
            
        except Exception as e:
            console.print(f"[bold red]Error in movie search: {str(e)}[/bold red]")
            await update.message.reply_text(
                "Sorry, I encountered an error while searching for movies. "
                "Please try again with a different search term."
            )
            return MOVIE_SEARCH

    async def select_movie(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle movie selection and show theaters."""
        user_id = update.effective_user.id
        selected_movie = update.message.text

        if selected_movie == "Search Again":
            await update.message.reply_text(
                "Please enter another search term for movies.",
                reply_markup=ReplyKeyboardRemove()
            )
            return MOVIE_SEARCH

        try:
            # Store selected movie details
            available_movies = self.user_contexts[user_id].get('available_movies', [])
            # Extract movie name without year
            selected_movie_name = selected_movie.split(" (")[0] if " (" in selected_movie else selected_movie
            
            # Try to find the movie in available movies
            movie_details = next(
                (movie for movie in available_movies 
                 if (movie.get('Title', movie.get('title', '')).strip() == selected_movie_name)),
                None
            )
            
            if not movie_details:
                # If not found, try to get from local database
                local_movies = await self.booking_system.coordinator.booking_agent.db.get_all_movies()
                movie_details = next(
                    (movie for movie in local_movies 
                     if movie['title'].strip() == selected_movie_name),
                    None
                )
            
            if not movie_details:
                console.print("[bold yellow]No movie details found for the selected movie.[/bold yellow]")
                await update.message.reply_text(
                    "Sorry, I couldn't find the details for this movie. Please try searching again.",
                    reply_markup=ReplyKeyboardRemove()
                )
                return MOVIE_SEARCH
            
            # Convert to consistent format
            formatted_movie = {
                'title': movie_details.get('Title', movie_details.get('title')),
                'year': movie_details.get('Year', movie_details.get('year')),
                'id': movie_details.get('imdbID', movie_details.get('id')),
                'genre': movie_details.get('Genre', movie_details.get('genre')),
                'director': movie_details.get('Director', movie_details.get('director')),
                'actors': movie_details.get('Actors', movie_details.get('actors')),
                'plot': movie_details.get('Plot', movie_details.get('plot')),
                'rating': movie_details.get('imdbRating', movie_details.get('rating', 'N/A'))
            }
            
            self.user_contexts[user_id]["selected_movie"] = formatted_movie
            
            # Format movie information for display
            movie_info = (
                f"🎬 {formatted_movie['title']} ({formatted_movie['year']})\n"
                f"⭐ Rating: {formatted_movie['rating']}\n"
                f"🎭 Genre: {formatted_movie['genre']}\n"
                f"👥 Cast: {formatted_movie['actors']}\n"
                f"📝 Plot: {formatted_movie['plot'][:200]}..."
            )
            
            await update.message.reply_text(f"You selected:\n\n{movie_info}")
            
            # Get theaters through booking agent
            theaters = await self.booking_system.coordinator.booking_agent.get_theaters()
            
            if not theaters:
                await update.message.reply_text(
                    "Sorry, no theaters are available at the moment. Please try again later.",
                    reply_markup=ReplyKeyboardRemove()
                )
                return ConversationHandler.END
            
            # Create theater selection keyboard
            keyboard = [[theater['name']] for theater in theaters]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
            
            await update.message.reply_text(
                "Please select a theater:",
                reply_markup=reply_markup
            )
            return SELECT_THEATER
            
        except Exception as e:
            console.print(f"[bold red]Error in movie selection: {str(e)}[/bold red]")
            await update.message.reply_text(
                "Sorry, there was an error processing your selection. Please try searching again.",
                reply_markup=ReplyKeyboardRemove()
            )
            return MOVIE_SEARCH

    async def select_theater(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle theater selection and show showtimes."""
        user_id = update.effective_user.id
        user_input = update.message.text.lower()

        try:
            # Get theaters through coordinator
            response = await self.booking_system.coordinator.process_input(
                "What theaters are available?",
                self.user_contexts[user_id]
            )
            
            # If user is asking about theater availability
            if "can i watch this in theatre" in user_input or "where" in user_input:
                await update.message.reply_text(response)

            # Extract theater names from response and create keyboard
            theaters = [line.split("🏢 ")[1] 
                       for line in response.split("\n") 
                       if line.strip().startswith("🏢")]
            
            if not theaters:
                await update.message.reply_text(
                    "Sorry, no theaters are available at the moment. Please try again later.",
                    reply_markup=ReplyKeyboardRemove()
                )
                return ConversationHandler.END

            keyboard = [[theater] for theater in theaters]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
            
            await update.message.reply_text(
                "Please select a theater:",
                reply_markup=reply_markup
            )
            return SELECT_THEATER

        except Exception as e:
            console.print(f"[bold red]Error getting theaters: {str(e)}[/bold red]")
            await update.message.reply_text(
                "Sorry, there was an error getting theater information. Please try again later.",
                reply_markup=ReplyKeyboardRemove()
            )
            return ConversationHandler.END

    async def select_showtime(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle showtime selection and show available seats."""
        user_id = update.effective_user.id
        self.user_contexts[user_id]["selected_theater"] = update.message.text

        
        try:
            # Get showtimes through coordinator
            response = await self.booking_system.coordinator.process_input(
                "Show available showtimes",
                self.user_contexts[user_id]
            )
            
            # Extract showtimes from response
            showtimes = [line.split("🕒 ")[1] 
                        for line in response.split("\n") 
                        if line.strip().startswith("🕒")]
            
            if not showtimes:
                await update.message.reply_text(
                    "Sorry, no showtimes are available for this movie and theater.",
                    reply_markup=ReplyKeyboardRemove()
                )
                return ConversationHandler.END

            keyboard = [[showtime] for showtime in showtimes]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
            
            await update.message.reply_text(
                "Please select a showtime:",
                reply_markup=reply_markup
            )
            return SELECT_SHOWTIME

        except Exception as e:
            console.print(f"[bold red]Error getting showtimes: {str(e)}[/bold red]")
            await update.message.reply_text(
                "Sorry, there was an error getting showtime information. Please try again later.",
                reply_markup=ReplyKeyboardRemove()
            )
            return ConversationHandler.END

    async def select_seats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle showtime selection and show available seats."""
        user_id = update.effective_user.id
        selection = update.message.text
        
        try:
            # If this is first time showing seats
            if "selected_seats" not in self.user_contexts[user_id]:
                self.user_contexts[user_id]["selected_seats"] = []
                self.user_contexts[user_id]["selected_showtime"] = selection
                
                # Get seat map through coordinator
                response = await self.booking_system.coordinator.process_input(
                    "Show available seats",
                    self.user_contexts[user_id]
                )
                
                # First send the seat map visualization
                await update.message.reply_text(response)
                
                # Extract available seats from response
                seats = [line.split("💺 ")[1] 
                        for line in response.split("\n") 
                        if line.strip().startswith("💺")]
                
                if not seats:
                    await update.message.reply_text(
                        "Sorry, no seats are available for this showtime.",
                        reply_markup=ReplyKeyboardRemove()
                    )
                    return ConversationHandler.END

                # Create keyboard with seats in rows of 5
                keyboard = [seats[i:i+5] for i in range(0, len(seats), 5)]
                keyboard.append(["Confirm Selection"])
                reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=False)
                
                await update.message.reply_text(
                    "Please select your seats (tap multiple times for multiple seats).\n"
                    "When done, press 'Confirm Selection':",
                    reply_markup=reply_markup
                )
                return SELECT_SEATS
                
            # Handle seat selection
            if selection == "Confirm Selection":
                if not self.user_contexts[user_id]["selected_seats"]:
                    await update.message.reply_text(
                        "Please select at least one seat before confirming.",
                        reply_markup=ReplyKeyboardMarkup([[s] for s in seats] + [["Confirm Selection"]])
                    )
                    return SELECT_SEATS
                    
                # Process booking through coordinator
                response = await self.booking_system.coordinator.process_input(
                    "Confirm booking",
                    self.user_contexts[user_id]
                )
                
                # Clean up context
                if user_id in self.user_contexts:
                    del self.user_contexts[user_id]
                
                await update.message.reply_text(
                    response,
                    reply_markup=ReplyKeyboardRemove()
                )
                return ConversationHandler.END
            else:
                # Add selected seat to context
                self.user_contexts[user_id]["selected_seats"].append(selection)
                
                await update.message.reply_text(
                    f"Seat {selection} selected. Select more seats or press 'Confirm Selection'.\n"
                    f"Currently selected seats: {', '.join(self.user_contexts[user_id]['selected_seats'])}"
                )
                return SELECT_SEATS

        except Exception as e:
            console.print(f"[bold red]Error handling seat selection: {str(e)}[/bold red]")
            await update.message.reply_text(
                "Sorry, there was an error processing your seat selection. Please try again.",
                reply_markup=ReplyKeyboardRemove()
            )
            return ConversationHandler.END

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel the conversation."""
        user_id = update.effective_user.id
        if user_id in self.user_contexts:
            del self.user_contexts[user_id]
            
        await update.message.reply_text(
            "Booking cancelled. Have a great day!",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    def run(self):
        """Run the bot."""
        # Create application and add handlers
        application = Application.builder().token(self.token).build()

        # Add conversation handler
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", self.start)],
            states={
                GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_name)],
                GET_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_email)],
                MOVIE_SEARCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.search_movies)],
                SELECT_MOVIE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.select_movie)],
                SELECT_THEATER: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.select_theater)],
                SELECT_SHOWTIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.select_showtime)],
                SELECT_SEATS: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.select_seats)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )

        application.add_handler(conv_handler)

        # Start the bot
        console.print("[bold green]Starting Telegram bot...[/bold green]")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    # Initialize and run the bot
    if MovieBookingSystem.verify_environment():
        TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
        if not TOKEN:
            console.print("[bold red]Error: TELEGRAM_BOT_TOKEN not set in environment variables[/bold red]")
        else:
            bot = TelegramMovieBot(TOKEN)
            bot.run()