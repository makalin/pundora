# 🎭 Pundora

**Pundora** is an AI-powered Dad Joke generator that delivers groan-worthy humor in both text and voice. Think of it as opening Pandora's box—except instead of chaos, you unleash endless puns and cheesy one-liners! 😂

## ✨ Features
- 📝 **Text Mode**: Generates dad jokes instantly on screen
- 🔊 **Voice Mode**: Uses AI text-to-speech to deliver jokes out loud
- 🎛️ **Settings**: Adjust humor level (mild, medium, extra cringe)
- 🌍 **Categories**: Puns, knock-knock jokes, wordplay, dad classics, food, animals, technology
- 🎲 **Randomizer**: Never hear the same joke twice
- 🎙️ **Custom Voice**: Choose funny voices (robot, dad, dramatic narrator, cheerful)
- 🌐 **Web Interface**: Beautiful, modern UI with real-time joke generation
- 💻 **CLI**: Command-line interface for terminal users
- 🤖 **AI Powered**: Uses OpenAI for dynamic joke generation with fallback jokes

## 🛠️ Tech Stack
- **Backend**: Python (FastAPI)
- **AI Text**: OpenAI GPT-3.5-turbo for dynamic joke generation
- **Voice**: ElevenLabs API for realistic text-to-speech
- **Frontend**: Vanilla JavaScript + Tailwind CSS
- **CLI**: Python with argparse
- **Configuration**: Environment variables with .env support

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/pundora.git
cd pundora

# Install dependencies
pip install -r requirements.txt

# Or use the quick start script
python run.py
```

### 2. Configuration

Copy the example environment file and add your API keys:

```bash
cp .env.example .env
```

Edit `.env` with your API keys:
```env
OPENAI_API_KEY=your_openai_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

### 3. Run the Application

#### Web Interface
```bash
python main.py
```
Then open http://localhost:8000 in your browser.

#### Command Line Interface
```bash
# Generate a random joke
pundora --joke

# Generate a pun joke with extra cringe
pundora --joke --category puns --level extra

# Generate a joke with voice
pundora --joke --voice --voice-type robot

# List available categories
pundora --list-categories

# List available voices
pundora --list-voices
```

## 📖 Usage Examples

### Web Interface
1. Open http://localhost:8000
2. Select your preferred category and humor level
3. Choose voice settings if desired
4. Click "Generate Joke" or "Joke + Voice"
5. Enjoy the cringe! 😂

### CLI Examples

```bash
# Basic joke generation
pundora --joke

# Category-specific jokes
pundora --joke --category knock-knock
pundora --joke --category food --level extra

# Voice generation
pundora --joke --voice --voice-type dramatic

# Custom prompts
pundora --joke --prompt "Make a joke about programming"

# List options
pundora --list-categories
pundora --list-levels
pundora --list-voices
```

### API Usage

The application also provides a REST API:

```bash
# Get a joke
curl "http://localhost:8000/api/joke?category=puns&humor_level=extra"

# Get a joke with voice
curl "http://localhost:8000/api/voice?text=Why don't scientists trust atoms? Because they make up everything!&voice=dad" --output joke.mp3

# Health check
curl "http://localhost:8000/api/health"
```

## 🎯 Available Categories
- **General**: Classic dad jokes
- **Puns**: Pun-based humor
- **Knock-Knock**: Traditional knock-knock jokes
- **Wordplay**: Clever wordplay and double entendres
- **Dad Classics**: Timeless dad joke formats
- **Food**: Food-related puns and jokes
- **Animals**: Animal-themed humor
- **Technology**: Programming and tech jokes

## 🎭 Humor Levels
- **Mild**: Family-friendly, mildly punny
- **Medium**: Moderately cringy and punny (default)
- **Extra**: Maximum cringe, groan-worthy, over-the-top punny

## 🎙️ Voice Options
- **Dad**: Warm, fatherly voice perfect for dad jokes
- **Robot**: Mechanical voice for tech jokes
- **Dramatic**: Overly dramatic narrator voice
- **Cheerful**: Upbeat, happy voice

## 🛠️ Development

### Project Structure
```
pundora/
├── pundora/
│   ├── __init__.py
│   ├── api.py              # FastAPI backend
│   ├── cli.py              # Command-line interface
│   ├── config.py           # Configuration management
│   ├── joke_generator.py   # AI joke generation
│   └── tts_service.py      # Text-to-speech service
├── templates/
│   └── index.html          # Web interface
├── main.py                 # Application entry point
├── run.py                  # Quick start script
├── requirements.txt        # Python dependencies
├── setup.py               # Package setup
└── README.md              # This file
```

### Running in Development
```bash
# Install in development mode
pip install -e .

# Run with auto-reload
python main.py

# Or use uvicorn directly
uvicorn pundora.api:app --reload --host 0.0.0.0 --port 8000
```

## 🔧 Configuration

### Environment Variables
- `OPENAI_API_KEY`: Required for AI joke generation
- `ELEVENLABS_API_KEY`: Required for voice generation
- `ELEVENLABS_VOICE_ID`: Optional, specific voice ID
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `DEBUG`: Debug mode (default: True)

### API Keys Setup
1. **OpenAI**: Get your API key from https://platform.openai.com/api-keys
2. **ElevenLabs**: Get your API key from https://elevenlabs.io/app/settings/api-keys

## 🐛 Troubleshooting

### Common Issues
1. **"Joke generator not available"**: Check your OpenAI API key
2. **"TTS service not available"**: Check your ElevenLabs API key
3. **Voice not working**: Ensure ElevenLabs API key is valid and has credits
4. **Port already in use**: Change the PORT in .env file

### Fallback Mode
If API keys are not available, the application will run in fallback mode with pre-defined jokes.

## 🤝 Contributing

Pull requests are welcome! Here are some ways to contribute:

1. **Add new joke categories** - Extend the joke templates
2. **Improve voice options** - Add new voice configurations
3. **Enhance the web UI** - Make it even more beautiful
4. **Add new features** - Joke ratings, favorites, sharing, etc.
5. **Fix bugs** - Help make Pundora more stable
6. **Write tests** - Improve code quality

### Development Setup
```bash
# Fork and clone the repository
git clone https://github.com/yourusername/pundora.git
cd pundora

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .

# Run tests (when available)
python -m pytest

# Run the application
python main.py
```

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for the amazing GPT models
- ElevenLabs for realistic text-to-speech
- FastAPI for the excellent web framework
- All the dad joke enthusiasts who inspired this project

---

😂 **Open the box. Unleash the puns. Welcome to Pundora!** 🎭

*Made with ❤️ and lots of dad jokes*