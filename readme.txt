# Movie Booking AI Assistant

A Streamlit-based conversational AI assistant for booking movie tickets, powered by OpenAI's GPT-3.5 Turbo.

## Features
- 🎭 Natural language movie search and recommendations
- 🏟️ Theater and showtime selection
- 💺 Interactive seat booking system
- 🎫 Real-time booking status
- 🤖 OpenAI-powered conversational AI
- 🎬 OMDB API integration for movie data
- 📱 Modern web interface with Streamlit

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
- Windows:
```bash
.\venv\Scripts\activate
```
- Unix/MacOS:
```bash
source venv/bin/activate
```

3. Install requirements:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with your API keys:
```env
OPENAI_API_KEY=your_openai_api_key
OMDB_API_KEY=your_omdb_api_key
```

5. Run the Streamlit application:
```bash
streamlit run app.py
```

## Project Structure
```
movie_booking_agent/
├── config/
│   └── config.py         # Configuration settings
├── agents/
│   ├── coordinator.py    # Main coordinator agent
│   ├── movie_agent.py    # Movie information agent
│   ├── seating_agent.py  # Seating management
│   └── booking_agent.py  # Booking process
├── database/
│   └── mockdb.py        # Mock database
├── utils/
│   ├── omdb_client.py   # OMDB API client
│   └── helpers.py       # Utility functions
├── app.py               # Streamlit web interface
├── requirements.txt     # Dependencies
└── .env                # Environment variables
```

## Development Setup

For development, install additional tools:
```bash
pip install black pylint pytest pytest-asyncio
```

## User Interface Features
- 💬 Chat-based interface for natural conversations
- 📊 Real-time booking status display
- 🗺️ Visual seat map representation
- 📱 Responsive design for all devices
- 🔄 Persistent session management

## Usage Flow
1. **Start the Application**
   ```bash
   streamlit run app.py
   ```

2. **Booking Process**
   - Enter your name and email
   - Share movie preferences
   - Search or select recommended movies
   - Choose theater and showtime
   - Select seats using the visual seating map
   - Confirm booking

## API Integrations
- OpenAI GPT-3.5-Turbo for natural language processing
- OMDB API for movie information
- Custom mock database for booking management

## Testing
Run tests with:
```bash
pytest tests/
```

## Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Requirements
- Python 3.8+
- OpenAI API key
- OMDB API key
- Streamlit 1.32.0+
- Other dependencies listed in requirements.txt

## Known Issues and Limitations
- Using mock database for demonstrations
- Limited to OMDB API movie selection
- Simplified payment process

## Future Enhancements
- Real database integration
- Additional payment gateways
- Multiple theater chain support
- User authentication
- Booking history
- Email confirmations

## License
This project is licensed under the MIT License - see the LICENSE file for details.
