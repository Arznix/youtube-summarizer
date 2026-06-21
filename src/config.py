import os
from pathlib import Path
from typing import Optional
import re

from dotenv import load_dotenv


class ConfigError(Exception):
    """Configuration error exception."""
    pass


class Config:
    """Configuration manager for the YouTube summarizer pipeline."""
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            env_file: Path to .env file. If None, uses default .env in project root.
        """
        self.project_root = Path(__file__).parent.parent
        
        if env_file is None:
            env_file = self.project_root / ".env"
        
        # Load environment variables
        load_dotenv(env_file)
        
        # Validate and set configuration
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate required configuration variables."""
        required_vars = [
            "TELEGRAM_BOT_TOKEN",
            "TELEGRAM_CHAT_ID",
            "OLLAMA_HOST"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ConfigError(
                f"Missing required environment variables: {', '.join(missing_vars)}\n"
                f"Please copy .env.example to .env and fill in the values."
            )
        
        # Validate Telegram bot token format
        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        if not re.match(r'^\d+:[A-Za-z0-9_-]+$', telegram_token):
            raise ConfigError("Invalid Telegram bot token format")
        
        # Validate Ollama host URL
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        if not ollama_host.startswith(("http://", "https://")):
            raise ConfigError("OLLAMA_HOST must start with http:// or https://")
    
    @property
    def telegram_bot_token(self) -> str:
        """Get Telegram bot token."""
        return os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    @property
    def telegram_chat_id(self) -> str:
        """Get Telegram chat ID."""
        return os.getenv("TELEGRAM_CHAT_ID", "")
    
    @property
    def ollama_host(self) -> str:
        """Get Ollama host URL."""
        return os.getenv("OLLAMA_HOST", "http://localhost:11434")
    
    @property
    def ollama_model(self) -> str:
        """Get Ollama model name."""
        return os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
    
    @property
    def database_path(self) -> Path:
        """Get database file path."""
        db_dir = self.project_root / "data"
        db_dir.mkdir(exist_ok=True)
        return db_dir / "subscriptions_state.db"
    
    @property
    def youtube_channel_ids(self) -> list:
        """Get list of YouTube channel IDs."""
        channel_ids_str = os.getenv("YOUTUBE_CHANNEL_IDS", "")
        if not channel_ids_str:
            return []
        return [cid.strip() for cid in channel_ids_str.split(",") if cid.strip()]
    
    def get_all_config(self) -> dict:
        """Get all configuration as dictionary (masks sensitive values)."""
        return {
            "telegram_bot_token": "***" if self.telegram_bot_token else "",
            "telegram_chat_id": self.telegram_chat_id,
            "ollama_host": self.ollama_host,
            "ollama_model": self.ollama_model,
            "database_path": str(self.database_path),
            "youtube_channel_ids": self.youtube_channel_ids,
            "project_root": str(self.project_root)
        }
    
    def print_config(self) -> None:
        """Print configuration (masking sensitive values)."""
        config = self.get_all_config()
        print("Configuration:")
        for key, value in config.items():
            print(f"  {key}: {value}")


def load_config(env_file: Optional[str] = None) -> Config:
    """
    Load and validate configuration.
    
    Args:
        env_file: Path to .env file. If None, uses default .env in project root.
        
    Returns:
        Config object with validated configuration.
        
    Raises:
        ConfigError: If configuration is invalid or missing required variables.
    """
    return Config(env_file)


if __name__ == "__main__":
    # Test configuration loading
    try:
        config = load_config()
        config.print_config()
        print("\nConfiguration loaded successfully!")
    except ConfigError as e:
        print(f"Configuration error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")