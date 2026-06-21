import os
import sys
from pathlib import Path
from typing import Optional, List
import re
import requests

from dotenv import load_dotenv, set_key


class SetupError(Exception):
    """Setup error exception."""
    pass


class SetupWizard:
    """Interactive setup wizard for YouTube Summarizer."""
    
    def __init__(self):
        """Initialize the setup wizard."""
        self.project_root = Path(__file__).parent.parent
        self.env_file = self.project_root / ".env"
        self.env_example = self.project_root / ".env.example"
        
        # Ensure .env.example exists
        self._create_env_example()
    
    def _create_env_example(self) -> None:
        """Create .env.example file if it doesn't exist."""
        if not self.env_example.exists():
            example_content = """# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b

# YouTube Channel IDs (comma-separated)
YOUTUBE_CHANNEL_IDS=channel_id_1,channel_id_2

# Optional: Database path (default: data/subscriptions_state.db)
# DATABASE_PATH=data/subscriptions_state.db
"""
            self.env_example.write_text(example_content)
            print(f"Created {self.env_example}")
    
    def clear_screen(self) -> None:
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self) -> None:
        """Print setup wizard header."""
        self.clear_screen()
        print("=" * 60)
        print("YouTube Summarizer Setup Wizard")
        print("=" * 60)
        print()
    
    def prompt_input(self, prompt: str, default: Optional[str] = None, required: bool = True) -> str:
        """
        Prompt user for input with optional default value.
        
        Args:
            prompt: Input prompt message
            default: Default value if user presses Enter
            required: Whether input is required
            
        Returns:
            User input or default value
        """
        while True:
            if default:
                user_input = input(f"{prompt} [{default}]: ").strip()
                if not user_input:
                    user_input = default
            else:
                user_input = input(f"{prompt}: ").strip()
            
            if user_input or not required:
                return user_input
            
            print("This field is required. Please enter a value.")
    
    def validate_telegram_token(self, token: str) -> bool:
        """
        Validate Telegram bot token format.
        
        Args:
            token: Telegram bot token
            
        Returns:
            True if valid, False otherwise
        """
        return bool(re.match(r'^\d+:[A-Za-z0-9_-]+$', token))
    
    def validate_ollama_host(self, host: str) -> bool:
        """
        Validate Ollama host URL.
        
        Args:
            host: Ollama host URL
            
        Returns:
            True if valid, False otherwise
        """
        return host.startswith(("http://", "https://"))
    
    def extract_channel_id_from_url(self, url: str) -> Optional[str]:
        """
        Extract YouTube channel ID from a URL.
        
        Supports formats:
        - https://www.youtube.com/channel/UCxxxxxx
        - https://www.youtube.com/c/ChannelName
        - https://www.youtube.com/@ChannelHandle
        - https://youtube.com/channel/UCxxxxxx
        
        Args:
            url: YouTube channel URL
            
        Returns:
            Channel ID or None if extraction fails
        """
        url = url.strip()
        
        # Pattern 1: Direct channel ID URL (e.g., /channel/UCxxxxxx)
        channel_match = re.search(r'youtube\.com/channel/(UC[a-zA-Z0-9_-]{22})', url)
        if channel_match:
            return channel_match.group(1)
        
        # Pattern 2: Custom URL or handle - need to scrape
        try:
            # Add headers to mimic a browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Look for channel ID in page source
            # YouTube embeds channel ID in various places
            patterns = [
                r'"channelId":"(UC[a-zA-Z0-9_-]{22})"',
                r'"externalId":"(UC[a-zA-Z0-9_-]{22})"',
                r'channel_id=(UC[a-zA-Z0-9_-]{22})',
                r'/channel/(UC[a-zA-Z0-9_-]{22})',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, response.text)
                if match:
                    return match.group(1)
            
            # Try to find via RSS feed link
            rss_match = re.search(r'rss\.youtube\.com.*channel_id=(UC[a-zA-Z0-9_-]{22})', response.text)
            if rss_match:
                return rss_match.group(1)
            
            return None
            
        except Exception as e:
            print(f"Error fetching URL: {e}")
            return None
    
    def is_valid_channel_id(self, channel_id: str) -> bool:
        """
        Validate YouTube channel ID format.
        
        Args:
            channel_id: Channel ID to validate
            
        Returns:
            True if valid format, False otherwise
        """
        return bool(re.match(r'^UC[a-zA-Z0-9_-]{22}$', channel_id))
    
    def setup_telegram(self) -> dict:
        """Setup Telegram configuration."""
        print("\n--- Telegram Configuration ---")
        print("You need a Telegram bot token and chat ID.")
        print("1. Open Telegram and search for @BotFather")
        print("2. Send /newbot and follow the instructions")
        print("3. Copy the bot token")
        print("4. Send a message to your bot, then visit:")
        print("   https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates")
        print("   to find your chat ID")
        print()
        
        # Get bot token
        while True:
            token = self.prompt_input("Enter Telegram bot token")
            if self.validate_telegram_token(token):
                break
            print("Invalid token format. Expected format: 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
        
        # Get chat ID
        while True:
            chat_id = self.prompt_input("Enter Telegram chat ID")
            if chat_id.isdigit():
                break
            print("Chat ID must be a number")
        
        return {
            "TELEGRAM_BOT_TOKEN": token,
            "TELEGRAM_CHAT_ID": chat_id
        }
    
    def setup_ollama(self) -> dict:
        """Setup Ollama configuration."""
        print("\n--- Ollama Configuration ---")
        print("Ollama should be installed and running locally.")
        print("Default host: http://localhost:11434")
        print("Default model: qwen2.5:7b")
        print()
        
        # Get Ollama host
        while True:
            host = self.prompt_input("Enter Ollama host URL", "http://localhost:11434")
            if self.validate_ollama_host(host):
                break
            print("Invalid URL format. Must start with http:// or https://")
        
        # Get model name
        model = self.prompt_input("Enter Ollama model name", "qwen2.5:7b")
        
        return {
            "OLLAMA_HOST": host,
            "OLLAMA_MODEL": model
        }
    
    def setup_youtube_channels(self) -> dict:
        """Setup YouTube channel configuration (up to 100 channels)."""
        print("\n--- YouTube Channel Configuration ---")
        print("Enter YouTube channel IDs or URLs (comma-separated).")
        print("You can add up to 100 channels.")
        print()
        print("Supported URL formats:")
        print("  - https://www.youtube.com/channel/UCxxxxxx")
        print("  - https://www.youtube.com/c/ChannelName")
        print("  - https://www.youtube.com/@ChannelHandle")
        print("  - Or just enter the channel ID directly (UCxxxxxx)")
        print()
        
        channel_input = self.prompt_input(
            "Enter YouTube channel IDs or URLs (comma-separated)",
            required=False
        )
        
        # Clean up input
        if channel_input:
            items = [item.strip() for item in channel_input.split(",") if item.strip()]
            channel_ids = []
            
            for item in items:
                # Check if it's a URL or a channel ID
                if item.startswith(("http://", "https://", "www.")):
                    print(f"Extracting channel ID from URL: {item}")
                    channel_id = self.extract_channel_id_from_url(item)
                    if channel_id:
                        print(f"  [OK] Found channel ID: {channel_id}")
                        channel_ids.append(channel_id)
                    else:
                        print(f"  [ERROR] Could not extract channel ID from URL")
                        print(f"    Please enter the channel ID manually (UCxxxxxx)")
                elif self.is_valid_channel_id(item):
                    # It's already a valid channel ID
                    channel_ids.append(item)
                else:
                    print(f"Invalid channel ID or URL: {item}")
                    print("  Channel IDs should start with 'UC' and be 24 characters long")
            
            # Limit to 100 channels
            if len(channel_ids) > 100:
                print(f"Warning: You entered {len(channel_ids)} channels. Limiting to 100.")
                channel_ids = channel_ids[:100]
            
            # Remove duplicates while preserving order
            seen = set()
            unique_channel_ids = []
            for cid in channel_ids:
                if cid not in seen:
                    seen.add(cid)
                    unique_channel_ids.append(cid)
            
            if len(unique_channel_ids) < len(channel_ids):
                print(f"Removed {len(channel_ids) - len(unique_channel_ids)} duplicate(s)")
            
            print(f"\nTotal channels: {len(unique_channel_ids)}")
            channel_ids_str = ",".join(unique_channel_ids)
        else:
            channel_ids_str = ""
        
        return {
            "YOUTUBE_CHANNEL_IDS": channel_ids_str
        }
    
    def setup_scheduling(self) -> dict:
        """Setup scheduling configuration."""
        print("\n--- Scheduling Configuration ---")
        print("Configure how often to check for new videos.")
        print()
        
        # Get start time
        print("Start time options:")
        print("  - Enter a time in HH:MM format (24-hour) to start at that time daily")
        print("  - Press Enter to start 5 minutes after setup completes")
        print()
        
        start_time = self.prompt_input(
            "Enter start time (HH:MM format, e.g., 06:30)",
            required=False
        )
        
        # Validate start time format
        if start_time:
            while not re.match(r'^([01]\d|2[0-3]):([0-5]\d)$', start_time):
                print("Invalid time format. Please use HH:MM format (24-hour), e.g., 06:30")
                start_time = self.prompt_input(
                    "Enter start time (HH:MM format)",
                    required=False
                )
                if not start_time:
                    break
        
        # Get frequency
        print("\nFrequency options:")
        print("  - How often to check for new videos (1-24 hours)")
        print("  - Example: 6 means check every 6 hours")
        print()
        
        frequency = self.prompt_input(
            "Enter check frequency in hours (1-24)",
            "6"
        )
        
        # Validate frequency
        try:
            frequency = int(frequency)
            if frequency < 1 or frequency > 24:
                print("Invalid frequency. Setting to 6 hours.")
                frequency = 6
        except ValueError:
            print("Invalid number. Setting to 6 hours.")
            frequency = 6
        
        config = {
            "SCHEDULE_FREQUENCY_HOURS": str(frequency)
        }
        
        if start_time:
            config["SCHEDULE_START_TIME"] = start_time
        
        return config
    
    def save_configuration(self, config: dict) -> None:
        """
        Save configuration to .env file.
        
        Args:
            config: Configuration dictionary
        """
        # Create or update .env file
        for key, value in config.items():
            set_key(str(self.env_file), key, value)
        
        print(f"\nConfiguration saved to {self.env_file}")
    
    def test_configuration(self) -> bool:
        """Test the configuration by loading it."""
        print("\n--- Testing Configuration ---")
        
        try:
            # Import here to avoid circular imports
            sys.path.insert(0, str(self.project_root / "src"))
            from config import load_config
            
            config = load_config(str(self.env_file))
            print("✓ Configuration loaded successfully!")
            
            # Test Ollama connection
            print("\nTesting Ollama connection...")
            import requests
            try:
                response = requests.get(f"{config.ollama_host}/api/tags", timeout=5)
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    model_names = [m.get("name") for m in models]
                    if config.ollama_model in model_names:
                        print(f"✓ Ollama model '{config.ollama_model}' found")
                    else:
                        print(f"⚠ Ollama model '{config.ollama_model}' not found")
                        print(f"  Available models: {model_names}")
                        print(f"  Run: ollama pull {config.ollama_model}")
                else:
                    print("✗ Cannot connect to Ollama")
            except requests.exceptions.RequestException as e:
                print(f"✗ Ollama connection failed: {e}")
            
            return True
            
        except Exception as e:
            print(f"✗ Configuration test failed: {e}")
            return False
    
    def run(self) -> None:
        """Run the setup wizard."""
        self.print_header()
        
        print("This wizard will help you configure the YouTube Summarizer.")
        print("Press Enter to accept default values (shown in brackets).")
        print()
        
        # Check if .env already exists
        if self.env_file.exists():
            response = input("Configuration file already exists. Overwrite? (y/N): ").strip().lower()
            if response != 'y':
                print("Setup cancelled.")
                return
        
        # Gather configuration
        config = {}
        
        # Telegram setup
        config.update(self.setup_telegram())
        
        # Ollama setup
        config.update(self.setup_ollama())
        
        # YouTube channels setup
        config.update(self.setup_youtube_channels())
        
        # Scheduling setup
        config.update(self.setup_scheduling())
        
        # Save configuration
        self.save_configuration(config)
        
        # Test configuration
        if self.test_configuration():
            print("\n" + "=" * 60)
            print("Setup completed successfully!")
            print("=" * 60)
            print("\nNext steps:")
            print("1. Ensure Ollama is running with the configured model")
            print("2. Run the orchestrator: python src/agent_orchestrator.py")
            print("3. Or run once: python src/agent_orchestrator.py --once")
            print("\nScheduling:")
            print("- The scheduler will start at the configured time")
            print("- Videos will be checked at the configured frequency")
            print("- All channels are checked together on the same schedule")
        else:
            print("\nSetup completed with warnings. Please check the configuration.")


def main():
    """Main entry point for setup wizard."""
    try:
        wizard = SetupWizard()
        wizard.run()
    except KeyboardInterrupt:
        print("\nSetup cancelled by user.")
    except Exception as e:
        print(f"Setup error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()