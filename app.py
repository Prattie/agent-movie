import os
import streamlit as st
from dotenv import load_dotenv
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from coordinator import CoordinatorAgent
import asyncio
from config_file import Config

# Load environment variables
load_dotenv()

# Initialize Streamlit page configuration
st.set_page_config(
    page_title="Movie Booking Assistant",
    page_icon="🎬",
    layout="wide"
)

class MovieBookingSystem:
    def __init__(self):
        # Configure global settings for LlamaIndex with OpenAI
        Settings.llm = OpenAI(
            model="gpt-3.5-turbo-0125",  # Latest GPT-3.5-Turbo model
            temperature=0.7,
            api_key=os.getenv("OPENAI_API_KEY"),
            system_prompt=Config.SYSTEM_MESSAGES["coordinator"]
        )
        
        # Configure OpenAI embeddings
        Settings.embed_model = OpenAIEmbedding(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Initialize coordinator agent
        self.coordinator = CoordinatorAgent()

    async def process_message(self, user_input: str, context: dict) -> str:
        """Process a single message"""
        return await self.coordinator.process_input(user_input, context)

def initialize_session_state():
    """Initialize session state variables"""
    if 'context' not in st.session_state:
        st.session_state.context = {
            "current_state": "greeting",
            "selected_movie": None,
            "selected_theater": None,
            "selected_showtime": None,
            "selected_seats": None,
            "customer_name": None,
            "customer_email": None
        }
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'booking_system' not in st.session_state:
        st.session_state.booking_system = MovieBookingSystem()

def main():
    st.title("🎬 Movie Booking Assistant")
    
    # Custom CSS for better styling
    st.markdown("""
        <style>
        .stChat {
            padding: 20px;
        }
        .user-avatar {
            background-color: #0066cc;
        }
        .assistant-avatar {
            background-color: #1abc9c;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    initialize_session_state()
    
    # Create columns for layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        
        # Initial greeting if no messages
        if not st.session_state.messages:
            with st.chat_message("assistant"):
                st.write("Hi, I am Max, your Movie Booking Assistant. May I know your name?")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "Hi, I am Max, your Movie Booking Assistant. May I know your name?"
                })
    
    with col2:
        # Show booking status and information
        if st.session_state.context.get("customer_name"):
            st.sidebar.subheader("Booking Information")
            st.sidebar.write(f"Customer: {st.session_state.context['customer_name']}")
            if st.session_state.context.get("customer_email"):
                st.sidebar.write(f"Email: {st.session_state.context['customer_email']}")
            if st.session_state.context.get("selected_movie"):
                st.sidebar.write(f"Movie: {st.session_state.context['selected_movie'].get('Title', '')}")
            if st.session_state.context.get("selected_theater"):
                st.sidebar.write(f"Theater: {st.session_state.context['selected_theater'].get('name', '')}")
            if st.session_state.context.get("selected_showtime"):
                st.sidebar.write(f"Time: {st.session_state.context['selected_showtime'].get('time', '')}")
            if st.session_state.context.get("selected_seats"):
                st.sidebar.write(f"Seats: {', '.join(st.session_state.context['selected_seats'])}")
    
    # Chat input
    if user_input := st.chat_input("Type your message here..."):
        # Display user message
        with st.chat_message("user"):
            st.write(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Get assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = asyncio.run(
                    st.session_state.booking_system.process_message(
                        user_input, 
                        st.session_state.context
                    )
                )
                st.write(response)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response
                })

        # Special handling for seat selection
        if st.session_state.context.get("current_state") == "seat_selection":
            if "available_seats" in st.session_state.context:
                with col2:
                    st.subheader("Seating Map")
                    seat_map = st.session_state.booking_system.coordinator.seating_agent.format_seat_map(
                        st.session_state.context["available_seats"]
                    )
                    st.text(seat_map)

if __name__ == "__main__":
    main()
