import speech_recognition as sr
import pyttsx3
import subprocess
import os
import webbrowser
import datetime
import psutil
import json
import threading
import time
import requests
from pathlib import Path
import re
import asyncio
import aiohttp
from typing import Optional, Dict, Any
import logging
from dataclasses import dataclass
from enum import Enum
import sys
import tkinter as tk
from tkinter import messagebox
import pystray
from PIL import Image, ImageDraw
import queue
import signal

# Optional imports with fallbacks
try:
    from googletrans import Translator
    TRANSLATION_AVAILABLE = True
except ImportError:
    TRANSLATION_AVAILABLE = False

try:
    import wikipedia
    WIKIPEDIA_AVAILABLE = True
except ImportError:
    WIKIPEDIA_AVAILABLE = False

try:
    import yfinance as yf
    STOCKS_AVAILABLE = True
except ImportError:
    STOCKS_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class ServiceStatus(Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    NOT_CONFIGURED = "not_configured"

@dataclass
class SystemInfo:
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    memory_available: float

class EnhancedBeastboy:
    def __init__(self):
        """Initialize the Beastboy assistant with background operation"""
        self.setup_logging()
        self.initialize_speech_components()
        self.load_configuration()
        self.setup_services()
        
        self.listening = False
        self.wake_words = ["hey bb", "bb", "hey b b", "b b","beasty","hey beasty", "beastboy"]
        self.current_language = 'en'
        self.session_active = False
        self.running = True
        self.paused = False
        
        # Background operation setup
        self.command_queue = queue.Queue()
        self.response_queue = queue.Queue()
        
        # System tray setup
        self.tray_icon = None
        self.setup_tray_icon()
        
        self.logger.info("Beastboy initialized successfully for background operation!")
        print("🤖 Beastboy is running in background! Minimizing to system tray...")
        
        # Initial greeting
        self.speak("Hello! I'm Beastboy, your voice assistant. I'm now running in the background. Say BB or Beasty To wake me up")

    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('beastboy.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def create_tray_image(self):
        """Create a simple icon for system tray"""
        # Create a simple icon
        width = 64
        height = 64
        image = Image.new('RGB', (width, height), color='blue')
        draw = ImageDraw.Draw(image)
        
        # Draw a simple "B" for Beastboy
        draw.rectangle([10, 10, 54, 54], fill='white')
        draw.text((20, 20), "BB", fill='blue')
        
        return image

    def setup_tray_icon(self):
        """Setup system tray icon and menu"""
        try:
            image = self.create_tray_image()
            
            menu = pystray.Menu(
                pystray.MenuItem("Beastboy Assistant", self.show_status, default=True),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Status", self.show_status),
                pystray.MenuItem("Pause/Resume", self.toggle_pause),
                pystray.MenuItem("Test Voice", self.test_voice),
                pystray.MenuItem("Show Logs", self.show_logs),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Settings", self.show_settings),
                pystray.MenuItem("About", self.show_about),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Exit", self.quit_application)
            )
            
            self.tray_icon = pystray.Icon("beastboy", image, "Beastboy Voice Assistant", menu)
        except Exception as e:
            self.logger.error(f"Failed to setup system tray: {e}")
            print("⚠️ System tray not available, running in console mode")

    def initialize_speech_components(self):
        """Initialize speech recognition and text-to-speech with better error handling"""
        try:
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            self.engine = pyttsx3.init()
            
            # Configure voice settings
            self.engine.setProperty('rate', 200)
            self.engine.setProperty('volume', 0.9)
            
            # Set voice preference
            voices = self.engine.getProperty('voices')
            if len(voices) > 1:
                self.engine.setProperty('voice', voices[1].id)
            
            # Initialize translator if available
            if TRANSLATION_AVAILABLE:
                self.translator = Translator()
            
            # Test microphone
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
        except Exception as e:
            self.logger.error(f"Failed to initialize speech components: {e}")
            raise

    def load_configuration(self):
        """Load configuration with improved structure"""
        config_file = "config.json"
        default_config = {
            "api_keys": {
                "openai_api_key": "your-openai-api-key-here"
            },
            "voice_settings": {
                "rate": 200,
                "volume": 0.9,
                "voice_index": 1
            },
            "features": {
                "weather_enabled": False,
                "news_enabled": False,
                "advanced_ai_enabled": True,
                "music_enabled": False,
                "email_enabled": False
            },
            "system": {
                "default_language": "en",
                "wake_words": ["hey bb", "bb", "beastboy"],
                "session_timeout": 300,
                "background_mode": True,
                "minimize_to_tray": True
            }
        }
        
        if not os.path.exists(config_file):
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=4)
            self.logger.info(f"Created default {config_file}")
        
        try:
            with open(config_file, 'r') as f:
                self.config = json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            self.config = default_config

    def setup_services(self):
        """Setup available services based on configuration"""
        self.services = {
            'weather': ServiceStatus.DISABLED,
            'news': ServiceStatus.DISABLED,
            'ai': ServiceStatus.DISABLED,
            'music': ServiceStatus.DISABLED,
            'email': ServiceStatus.DISABLED,
            'translation': ServiceStatus.ENABLED if TRANSLATION_AVAILABLE else ServiceStatus.DISABLED,
            'wikipedia': ServiceStatus.ENABLED if WIKIPEDIA_AVAILABLE else ServiceStatus.DISABLED,
            'stocks': ServiceStatus.ENABLED if STOCKS_AVAILABLE else ServiceStatus.DISABLED
        }
        
        # Setup OpenAI if available and configured
        self.setup_openai()
        
        self.logger.info(f"Services status: {self.services}")

    def setup_openai(self):
        """Setup OpenAI API if available and configured"""
        if not OPENAI_AVAILABLE:
            self.openai_enabled = False
            self.logger.info("OpenAI package not installed")
            return
        
        api_key = self.config.get("api_keys", {}).get("openai_api_key", "")
        if api_key and api_key.strip():
            try:
                openai.api_key = api_key
                self.openai_enabled = True
                self.services['ai'] = ServiceStatus.ENABLED
                self.logger.info("OpenAI API configured successfully")
            except Exception as e:
                self.logger.error(f"Failed to configure OpenAI: {e}")
                self.openai_enabled = False
        else:
            self.openai_enabled = False
            self.logger.info("OpenAI API key not provided")

    def get_ai_response(self, query: str) -> Optional[str]:
        """Get intelligent response using OpenAI"""
        if not self.openai_enabled:
            return None
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are Beastboy, a helpful Windows voice assistant running in the background. Provide concise, helpful responses. If the user asks you to perform a system action, clearly state what action should be taken. Keep responses under 50 words unless specifically asked for more detail."
                    },
                    {"role": "user", "content": query}
                ],
                max_tokens=150,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            self.logger.error(f"OpenAI API error: {e}")
            return None

    def speak(self, text: str, language: str = 'en'):
        """Enhanced text-to-speech with improved error handling"""
        try:
            if self.paused:
                return
                
            print(f"🤖 Beastboy: {text}")
            
            # Translate if not in English and translation is available
            if language != 'en' and TRANSLATION_AVAILABLE:
                try:
                    translated = self.translator.translate(text, dest=language)
                    text = translated.text
                except Exception as e:
                    self.logger.warning(f"Translation failed: {e}")
            
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            self.logger.error(f"Speech synthesis failed: {e}")
            print(f"🤖 Beastboy: {text}")  # Fallback to text only

    def listen(self, language: str = 'en-US', timeout: int = 2) -> str:
        """Enhanced listening with better error handling and timeout"""
        if self.paused:
            return ""
            
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=7)
            
            # Try Google Speech Recognition
            text = self.recognizer.recognize_google(audio, language=language).lower()
            self.logger.info(f"Voice input: {text}")
            
            # Auto-detect language and translate if needed
            if TRANSLATION_AVAILABLE:
                try:
                    detected_lang = self.translator.detect(text).lang
                    if detected_lang != 'en':
                        translated = self.translator.translate(text, dest='en')
                        english_text = translated.text.lower()
                        self.current_language = detected_lang
                        self.logger.info(f"Detected: {detected_lang}, Translated: {english_text}")
                        return english_text
                except Exception as e:
                    self.logger.warning(f"Language detection failed: {e}")
            
            return text
            
        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            self.logger.error(f"Speech recognition error: {e}")
            return ""

    # System tray menu functions
    def show_status(self, icon=None, item=None):
        """Show current status"""
        status = "🟢 Active" if not self.paused else "🟡 Paused"
        services_count = sum(1 for service in self.services.values() if service == ServiceStatus.ENABLED)
        
        message = f"""Beastboy Voice Assistant
        
Status: {status}
Services: {services_count} enabled
Uptime: {self.get_uptime()}
CPU: {psutil.cpu_percent():.1f}%
Memory: {psutil.virtual_memory().percent:.1f}%

Listening for: {', '.join(self.wake_words)}"""
        
        messagebox.showinfo("Beastboy Status", message)

    def toggle_pause(self, icon=None, item=None):
        """Pause or resume the assistant"""
        self.paused = not self.paused
        status = "paused" if self.paused else "resumed"
        self.logger.info(f"Assistant {status}")
        self.speak(f"I'm now {status}")

    def test_voice(self, icon=None, item=None):
        """Test voice output"""
        self.speak("Voice test successful! I'm working properly.")

    def show_logs(self, icon=None, item=None):
        """Open log file"""
        try:
            os.startfile("beastboy.log")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open logs: {e}")

    def show_settings(self, icon=None, item=None):
        """Open settings file"""
        try:
            os.startfile("config.json")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open settings: {e}")

    def show_about(self, icon=None, item=None):
        """Show about dialog"""
        about_text = """Beastboy Voice Assistant v2.0
        
A powerful AI-enhanced voice assistant for Windows
that runs silently in the background any make easy your's Work.

Features:
• Voice recognition with wake words
• AI-powered conversations
• System control and automation
• Multi-language support
• Background operation

Created with ❤️ by [DRK_ARSIYAN]
"""
        messagebox.showinfo("About Beastboy", about_text)

    def quit_application(self, icon=None, item=None):
        """Quit the application"""
        self.running = False
        if self.tray_icon:
            self.tray_icon.stop()
        self.cleanup()
        os._exit(0)

    def get_uptime(self):
        """Get application uptime"""
        return str(datetime.timedelta(seconds=int(time.time() - self.start_time)))

    # Voice processing methods (same as original but with background handling)
    async def get_weather_async(self, city: str = "London") -> str:
        """Get weather using free OpenWeather API"""
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        temp = data['main']['temp']
                        description = data['weather'][0]['description']
                        humidity = data['main']['humidity']
                        return f"Weather in {city}: {description}, {temp}°C, humidity {humidity}%"
                    else:
                        return f"Couldn't get weather for {city}"
        except Exception as e:
            self.logger.error(f"Weather API error: {e}")
            return f"Weather service temporarily unavailable: {str(e)}"

    def get_weather(self, city: str = "London") -> str:
        """Synchronous wrapper for weather"""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.get_weather_async(city))
        except Exception:
            return "Weather service not available"

    def get_stock_price(self, symbol: str) -> str:
        """Get stock price using yfinance"""
        if not STOCKS_AVAILABLE:
            return "Stock service not available. Please install yfinance: pip install yfinance"
        
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            current_price = info.get('currentPrice', info.get('regularMarketPrice'))
            company_name = info.get('shortName', symbol)
            
            if current_price:
                return f"{company_name} stock price is ${current_price:.2f}"
            else:
                return f"Couldn't get current price for {symbol}"
        except Exception as e:
            self.logger.error(f"Stock API error: {e}")
            return f"Couldn't get stock price for {symbol}: {str(e)}"

    def search_wikipedia(self, query: str) -> str:
        """Search Wikipedia for information"""
        if not WIKIPEDIA_AVAILABLE:
            return "Wikipedia service not available. Please install wikipedia: pip install wikipedia"
        
        try:
            summary = wikipedia.summary(query, sentences=2)
            return f"According to Wikipedia: {summary}"
        except wikipedia.exceptions.DisambiguationError:
            return f"Multiple results found for {query}. Please be more specific."
        except wikipedia.exceptions.PageError:
            return f"No Wikipedia page found for {query}"
        except Exception as e:
            self.logger.error(f"Wikipedia error: {e}")
            return f"Wikipedia search error: {str(e)}"

    def calculate_basic_math(self, expression: str) -> str:
        """Calculate basic mathematical expressions safely"""
        try:
            # Clean and validate expression
            expression = expression.replace('x', '*').replace('÷', '/').replace('^', '**')
            # Remove non-mathematical characters for safety
            allowed_chars = set('0123456789+-*/().,** ')
            if not all(c in allowed_chars for c in expression):
                return "Invalid mathematical expression"
            
            result = eval(expression)
            return f"The result is {result}"
        except ZeroDivisionError:
            return "Cannot divide by zero"
        except Exception as e:
            return f"Couldn't calculate: {str(e)}"

    def set_reminder(self, reminder_text: str, minutes: int) -> str:
        """Set a reminder with improved threading"""
        def remind():
            time.sleep(minutes * 60)
            if self.running:
                self.speak(f"Reminder: {reminder_text}")
                self.logger.info(f"Reminder triggered: {reminder_text}")
        
        thread = threading.Thread(target=remind, daemon=True)
        thread.start()
        return f"Reminder set for {minutes} minutes: {reminder_text}"

    def get_system_info(self) -> SystemInfo:
        """Get comprehensive system information"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return SystemInfo(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_percent=disk.percent,
                memory_available=round(memory.available / (1024**3), 2)
            )
        except Exception as e:
            self.logger.error(f"System info error: {e}")
            return SystemInfo(0, 0, 0, 0)

    def process_command(self, command: str) -> str:
        """Enhanced command processing with AI assistance"""
        command = command.lower().strip()
        
        # Remove wake words
        for wake_word in self.wake_words:
            if command.startswith(wake_word):
                command = command[len(wake_word):].strip()
                break
        
        # Try to understand command with AI first
        if self.openai_enabled:
            # Check if it's a complex query that would benefit from AI
            ai_keywords = ["how", "why", "what", "explain", "tell me", "advice", "help me", "should i"]
            if any(keyword in command for keyword in ai_keywords):
                ai_response = self.get_ai_response(command)
                if ai_response:
                    return ai_response
        
        # Weather commands
        if any(word in command for word in ["weather", "temperature", "forecast"]):
            city_match = re.search(r"weather (?:in |for )?([a-zA-Z\s]+)", command)
            city = city_match.group(1).strip() if city_match else "London"
            return self.get_weather(city)
        
        # Math/calculation commands
        elif any(word in command for word in ["calculate", "math", "compute", "solve"]):
            math_expr = re.sub(r".*(calculate|math|compute|solve)\s+", "", command)
            return self.calculate_basic_math(math_expr)
        
        # Stock price commands
        elif "stock" in command and "price" in command:
            symbol_match = re.search(r"stock (?:price )?(?:of |for )?([A-Z]{1,5})", command.upper())
            symbol = symbol_match.group(1) if symbol_match else "AAPL"
            return self.get_stock_price(symbol)
        
        # Wikipedia search
        elif any(phrase in command for phrase in ["wikipedia", "tell me about", "what is", "who is"]):
            query = re.sub(r".*(wikipedia|tell me about|what is|who is)\s+", "", command)
            return self.search_wikipedia(query)
        
        # Translation commands
        elif "translate" in command and TRANSLATION_AVAILABLE:
            translate_match = re.search(r"translate (.+?) to (\w+)", command)
            if translate_match:
                text = translate_match.group(1)
                target_lang = translate_match.group(2)
                try:
                    translated = self.translator.translate(text, dest=target_lang)
                    return f"Translation: {translated.text}"
                except Exception as e:
                    return f"Translation failed: {str(e)}"
            else:
                return "Please specify: translate text to language"
        
        # Reminder commands
        elif "remind me" in command or "set reminder" in command:
            reminder_match = re.search(r"remind me (?:to |about )?(.+?) in (\d+) minutes?", command)
            if reminder_match:
                reminder_text = reminder_match.group(1)
                minutes = int(reminder_match.group(2))
                return self.set_reminder(reminder_text, minutes)
            else:
                return "Please specify: remind me about something in X minutes"
        
        # Background control commands
        elif "pause" in command or "stop listening" in command:
            self.paused = True
            return "I'm paused. Right-click my tray icon to resume."
        
        elif "resume" in command or "start listening" in command:
            self.paused = False
            return "I'm now listening again!"
        
        elif "status" in command or "how are you" in command:
            services_count = sum(1 for service in self.services.values() if service == ServiceStatus.ENABLED)
            return f"I'm running in background mode with {services_count} services enabled. CPU usage: {psutil.cpu_percent():.1f}%"
        
        # Basic system commands
        else:
            basic_response = self.process_basic_command(command)
            # If basic command didn't understand and AI is available, try AI
            if "didn't understand" in basic_response and self.openai_enabled:
                ai_response = self.get_ai_response(command)
                return ai_response if ai_response else basic_response
            return basic_response

    def process_basic_command(self, command: str) -> str:
        """Process basic system commands with improved functionality"""
        # Application commands
        if command.startswith("open "):
            app_name = command[5:]
            if self.open_application(app_name):
                return f"Opening {app_name}"
            else:
                return f"Sorry, I couldn't open {app_name}"
        
        # Volume controls (Windows-specific)
        elif any(phrase in command for phrase in ["volume up", "increase volume"]):
            try:
                os.system("nircmd.exe changesysvolume 2000")
                return "Volume increased"
            except:
                return "Volume control not available"
        
        elif any(phrase in command for phrase in ["volume down", "decrease volume"]):
            try:
                os.system("nircmd.exe changesysvolume -2000")
                return "Volume decreased"
            except:
                return "Volume control not available"
        
        # System information
        elif any(phrase in command for phrase in ["system info", "system status", "performance"]):
            info = self.get_system_info()
            return f"System status: CPU {info.cpu_percent:.1f}%, Memory {info.memory_percent:.1f}%, Disk {info.disk_percent:.1f}%"
        
        # Time and date
        elif any(phrase in command for phrase in ["what time", "current time", "time"]):
            current_time = datetime.datetime.now().strftime("%I:%M %p")
            return f"The current time is {current_time}"
        
        elif any(phrase in command for phrase in ["what date", "today's date", "date"]):
            current_date = datetime.datetime.now().strftime("%B %d, %Y")
            return f"Today's date is {current_date}"
        
        # Web searches
        elif any(phrase in command for phrase in ["search for", "google", "look up"]):
            search_term = re.sub(r".*(search for|google|look up)\s+", "", command)
            if search_term:
                webbrowser.open(f"https://www.google.com/search?q={search_term}")
                return f"Searching for {search_term}"
            else:
                return "What would you like me to search for?"
        
        # System controls
        elif "shutdown" in command:
            os.system("shutdown /s /t 10")
            return "Shutting down the computer in 10 seconds"
        
        elif any(word in command for word in ["restart", "reboot"]):
            os.system("shutdown /r /t 10")
            return "Restarting the computer in 10 seconds"
        
        elif "lock" in command:
            os.system("rundll32.exe user32.dll,LockWorkStation")
            return "Locking the computer"
        
        # Help command
        elif "help" in command or "what can you do" in command:
            available_features = []
            if TRANSLATION_AVAILABLE:
                available_features.append("translations")
            if WIKIPEDIA_AVAILABLE:
                available_features.append("Wikipedia searches")
            if STOCKS_AVAILABLE:
                available_features.append("stock prices")
            if self.openai_enabled:
                available_features.append("AI-powered conversations")
            
            features_text = ", ".join(available_features) if available_features else "basic system controls"
            
            return f"""I'm running in background mode! I can help you with:
            • Opening applications and system controls
            • Volume control and system information
            • Time, date, and web searches
            • Math calculations and reminders
            • {features_text}
            • Background commands: pause, resume, status
            Just say Hey BB followed by your command!"""
        
        # Exit command
        elif any(word in command for word in ["goodbye", "exit", "quit", "stop"]):
            return "Goodbye! I'll keep running in the background. Right-click my tray icon to exit completely."
        
        else:
            return "I didn't understand that command. Say 'help' to see what I can do."

    def open_application(self, app_name: str) -> bool:
        """Open applications with improved app mapping"""
        app_mappings = {
            'notepad': 'notepad.exe',
            'calculator': 'calc.exe',
            'paint': 'mspaint.exe',
            'chrome': 'chrome.exe',
            'firefox': 'firefox.exe',
            'edge': 'msedge.exe',
            'explorer': 'explorer.exe',
            'file explorer': 'explorer.exe',
            'cmd': 'cmd.exe',
            'command prompt': 'cmd.exe',
            'powershell': 'powershell.exe',
            'task manager': 'taskmgr.exe',
            'control panel': 'control.exe',
            'settings': 'ms-settings:',
            'word': 'winword.exe',
            'excel': 'excel.exe',
            'powerpoint': 'powerpnt.exe',
            'vscode': 'code.exe',
            'visual studio code': 'code.exe'
        }
        
        app_name = app_name.lower()
        if app_name in app_mappings:
            try:
                if app_name == 'settings':
                    os.system('start ms-settings:')
                else:
                    subprocess.Popen(app_mappings[app_name], shell=True)
                return True
            except Exception as e:
                self.logger.error(f"Failed to open {app_name}: {e}")
                return False
        return False

    def background_voice_loop(self):
        """Background voice processing loop"""
        self.logger.info("Starting background voice processing")
        
        while self.running:
            try:
                if self.paused:
                    time.sleep(1)
                    continue
                
                # Listen for wake word
                if not self.listening:
                    text = self.listen(timeout=1)
                    if any(wake_word in text for wake_word in self.wake_words):
                        self.listening = True
                        self.session_active = True
                        self.speak("Yes, how can I help you?", self.current_language)
                        continue
                
                # Listen for command after wake word
                if self.listening:
                    command = self.listen(timeout=5)
                    if command:
                        response = self.process_command(command)
                        if "Goodbye!" in response:
                            self.speak(response, self.current_language)
                            # Don't exit, just reset listening state
                            self.listening = False
                        else:
                            self.speak(response, self.current_language)
                    
                    # Reset listening state
                    self.listening = False
                    self.current_language = 'en'
                    
            except Exception as e:
                self.logger.error(f"Error in background voice loop: {e}")
                time.sleep(1)  # Prevent rapid error loops

    def run_background(self):
        """Run the assistant in background mode"""
        self.start_time = time.time()
        self.logger.info("Starting Enhanced Beastboy in background mode")
        
        # Start voice processing in a separate thread
        voice_thread = threading.Thread(target=self.background_voice_loop, daemon=True)
        voice_thread.start()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        try:
            if self.tray_icon:
                # Run system tray (this blocks until exit)
                self.tray_icon.run()
            else:
                # Fallback: run in console mode
                print("🤖 Beastboy is running in background (console mode)")
                print("Press Ctrl+C to exit")
                while self.running:
                    time.sleep(1)
                    
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        except Exception as e:
            self.logger.error(f"Unexpected error in main loop: {e}")
        finally:
            self.cleanup()

    def signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown"""
        self.logger.info(f"Received signal {signum}")
        self.running = False
        if self.tray_icon:
            self.tray_icon.stop()

    def cleanup(self):
        """Cleanup resources"""
        self.logger.info("Cleaning up Enhanced Beastboy")
        self.running = False
        try:
            self.engine.stop()
        except:
            pass
        
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except:
                pass

if __name__ == "__main__":
    # Hide console window for background operation
    import ctypes
    import sys
    
    def hide_console():
        """Hide the console window"""
        try:
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        except:
            pass
    
    def show_console():
        """Show the console window"""
        try:
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 1)
        except:
            pass
    
    print("🚀 Starting Enhanced Beastboy Assistant in Background Mode...")
    print("📋 Core requirements: speechrecognition, pyttsx3, psutil, pyaudio, pystray, pillow")
    print("📋 Optional features: googletrans, wikipedia, yfinance, aiohttp, openai")
    print("🎤 Make sure your microphone is working!")
    print("🔑 Add your OpenAI API key to config.json for AI features")
    print("🖥️ Assistant will minimize to system tray...")
    print("-" * 70)
    
    try:
        assistant = EnhancedBeastboy()
        
        # Hide console after 3 seconds
        time.sleep(3)
        hide_console()
        
        # Run in background
        assistant.run_background()
        
    except ImportError as e:
        show_console()
        print(f"❌ Missing required package: {e}")
        print("📦 Please install required packages:")
        print("pip install speechrecognition pyttsx3 psutil pyaudio pystray pillow")
        print("pip install openai googletrans wikipedia yfinance aiohttp  # For optional features")
        input("Press Enter to exit...")
    except Exception as e:
        show_console()
        print(f"❌ Error starting Enhanced Beastboy: {e}")
        input("Press Enter to exit...")