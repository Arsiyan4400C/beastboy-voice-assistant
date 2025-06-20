# 🤖 Beastboy Voice Assistant

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)

A powerful, AI-enhanced voice assistant for Windows that runs silently in the background, responding to voice commands with natural language processing capabilities.

## ✨ Features

### Core Functionality
- 🎤 **Voice Recognition** - Always listening for wake words ("Hey BB", "BB", "Beastboy")
- 🔊 **Text-to-Speech** - Natural voice responses with multiple voice options
- 🖥️ **System Control** - Application launching, volume control, system information
- 🌐 **Web Integration** - Google searches, web browsing
- ⏰ **Reminders & Time** - Set reminders, get current time and date
- 🧮 **Math Calculator** - Solve mathematical expressions

### Enhanced Features (Optional Dependencies)
- 🤖 **AI-Powered Conversations** - OpenAI GPT integration for intelligent responses
- 🌍 **Multi-language Support** - Auto-detect and translate languages
- 📚 **Wikipedia Search** - Quick information lookup
- 📈 **Stock Prices** - Real-time stock market data
- 🌤️ **Weather Updates** - Current weather conditions
- 📊 **System Monitoring** - CPU, memory, and disk usage

### Background Operation
- 🔄 **Always Running** - Operates silently in the background
- 🎯 **Low Resource Usage** - Optimized for minimal system impact
- 📱 **System Tray Integration** - Easy access and control
- 🔧 **Configurable Settings** - Customizable through config.json

## 🚀 Quick Start

### Prerequisites
- Windows 10/11
- Python 3.7 or higher
- Working microphone and speakers

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/Arsiyan4400C/beastboy-voice-assistant.git
cd beastboy-voice-assistant
```

2. **Install required dependencies:**
```bash
# Core requirements (mandatory)
pip install speechrecognition pyttsx3 psutil pyaudio requests pathlib

# Optional features
pip install googletrans wikipedia yfinance aiohttp openai
```

3. **Install PyAudio (if issues occur):**
```bash
# For Windows, download the appropriate wheel from:
# https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
pip install PyAudio-0.2.11-cp39-cp39-win_amd64.whl  # Example for Python 3.9
```

4. **Run the assistant:**
```bash
python beastboy.py
```

## ⚙️ Configuration

The assistant creates a `config.json` file on first run. Customize it for your needs:

```json
{
    "api_keys": {
        "openai_api_key": "your-openai-api-key-here"
    },
    "voice_settings": {
        "rate": 200,
        "volume": 0.9,
        "voice_index": 1
    },
    "features": {
        "weather_enabled": false,
        "news_enabled": false,
        "advanced_ai_enabled": true,
        "music_enabled": false,
        "email_enabled": false
    },
    "system": {
        "default_language": "en",
        "wake_words": ["hey bb", "bb", "beastboy"],
        "session_timeout": 300
    }
}
```

### Getting API Keys

**OpenAI API (for AI features):**
1. Visit [OpenAI API](https://platform.openai.com/api-keys)
2. Create an account and generate an API key
3. Add it to your `config.json` file

## 🎯 Usage

### Basic Commands

**Wake up the assistant:**
- "Hey BB" or "BB" or "Beastboy"

**System Control:**
- "Open calculator"
- "Open notepad"
- "Volume up/down"
- "What time is it?"
- "System status"

**Web & Search:**
- "Search for Python tutorials"
- "Google artificial intelligence"

**Math & Calculations:**
- "Calculate 15 * 23 + 45"
- "Solve 100 / 4"

**Information:**
- "Tell me about Python programming"
- "Wikipedia search for machine learning"
- "Stock price for AAPL"
- "Weather in New York"

**Reminders:**
- "Remind me to take a break in 30 minutes"

**AI Conversations:**
- "How do I learn programming?"
- "Explain quantum computing"
- "What should I do today?"

### Running in Background

The assistant runs in the background and responds to wake words. To minimize to system tray:

1. Run the application
2. It will automatically minimize to system tray
3. Right-click the tray icon for options
4. Use voice commands normally - it's always listening!

## 📁 Project Structure

```
beastboy-voice-assistant/
├── beastboy.py              # Main application file
├── config.json              # Configuration file (auto-generated)
├── beastboy.log            # Application logs
├── requirements.txt         # Python dependencies
├── README.md               # This file
└── assets/                 # Icons and resources
    └── icon.ico            # System tray icon
```

## 🔧 Dependencies

### Required (Core Functionality)
```
speechrecognition>=3.8.1
pyttsx3>=2.90
psutil>=5.8.0
pyaudio>=0.2.11
requests>=2.25.1
```

### Optional (Enhanced Features)
```
openai>=0.27.0          # AI-powered responses
googletrans>=4.0.0      # Language translation
wikipedia>=1.4.0        # Wikipedia search
yfinance>=0.1.70        # Stock prices
aiohttp>=3.8.0          # Async HTTP requests
```

## 🛠️ Development

### Setting up Development Environment

1. Fork the repository
2. Create a virtual environment:
```bash
python -m venv beastboy-env
beastboy-env\Scripts\activate  # Windows
```

3. Install development dependencies:
```bash
pip install -r requirements.txt
pip install pytest black flake8  # Development tools
```

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black beastboy.py
flake8 beastboy.py
```

## 🔒 Security & Privacy

- **Local Processing**: Core functionality works entirely offline
- **API Calls**: Optional features may send data to third-party APIs
- **Voice Data**: Voice is processed locally; only text is sent to APIs
- **Logs**: Check `beastboy.log` for activity logs
- **API Keys**: Store securely in `config.json` (never commit to version control)

## 🐛 Troubleshooting

### Common Issues

**"No module named 'pyaudio'"**
```bash
# Install Microsoft Visual C++ Build Tools first
# Then install pyaudio from wheel file
pip install pipwin
pipwin install pyaudio
```

**"Microphone not working"**
- Check Windows microphone permissions
- Ensure microphone is set as default recording device
- Test with Windows Voice Recorder

**"Speech recognition not working"**
- Check internet connection (Google Speech API)
- Verify microphone input levels
- Try speaking closer to microphone

**"Assistant not responding to wake words"**
- Speak clearly and loudly
- Check microphone sensitivity
- Try different wake words from config

**"High CPU usage"**
- Adjust `session_timeout` in config
- Disable unused features
- Check for background processes

## 📝 Changelog

### v2.0.0 (Current)
- ✅ Background operation with system tray
- ✅ Enhanced AI integration
- ✅ Multi-language support
- ✅ Improved error handling
- ✅ Configuration system
- ✅ Logging system

### v1.0.0
- ✅ Basic voice recognition
- ✅ System commands
- ✅ Text-to-speech
- ✅ Application launching

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Contribution Guidelines
- Follow PEP 8 style guidelines
- Add tests for new features
- Update documentation
- Ensure backward compatibility

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **SpeechRecognition**: For voice recognition capabilities
- **pyttsx3**: For text-to-speech functionality
- **OpenAI**: For AI-powered conversations
- **Python Community**: For excellent libraries and tools

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Arsiyan4400C/beastboy-voice-assistant/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Arsiyan4400C/beastboy-voice-assistant/discussions)
- **Email**: siyanarsiyan19@gmail.com

## 🔮 Future Features

- [ ] Home automation integration
- [ ] Email management
- [ ] Calendar integration
- [ ] Music streaming control
- [ ] Smart device control
- [ ] Plugin system
- [ ] Mobile companion app
- [ ] Voice training for better recognition

---

**Made with ❤️ by [𝙳𝚁𝙺_𝙰𝚁𝚂𝙸𝚈𝙰𝙽]**

*Beastboy Voice Assistant - Your intelligent Windows companion*
