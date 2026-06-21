#!/usr/bin/env python3
"""
Send a message via Telegram bot.

This script sends a message using the Telegram Bot API.
It can be used as a standalone script or imported as a module.

Usage:
    python send_message.py "Hello World"
    python send_message.py "Bold text" --parse-mode HTML
    python send_message.py "Silent alert" --silent
"""

import argparse
import os
import sys
from typing import Optional

import requests
from dotenv import load_dotenv


def send_telegram_message(
    bot_token: str,
    chat_id: str,
    message: str,
    parse_mode: Optional[str] = "Markdown",
    disable_notification: bool = False,
    disable_web_page_preview: bool = False
) -> bool:
    """
    Send a message via Telegram Bot API.
    
    Args:
        bot_token: Telegram bot token
        chat_id: Target chat ID
        message: Message text
        parse_mode: Parse mode (Markdown, HTML, or None)
        disable_notification: Send silently
        disable_web_page_preview: Disable web page preview
        
    Returns:
        True if sent successfully, False otherwise
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    data = {
        "chat_id": chat_id,
        "text": message,
        "disable_notification": disable_notification,
        "disable_web_page_preview": disable_web_page_preview
    }
    
    if parse_mode:
        data["parse_mode"] = parse_mode
    
    try:
        response = requests.post(url, data=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        if result.get("ok"):
            return True
        else:
            error_code = result.get("error_code", "Unknown")
            description = result.get("description", "No description")
            print(f"Telegram API error {error_code}: {description}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


def load_config():
    """Load configuration from environment variables."""
    load_dotenv()
    
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("Error: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set")
        print("Copy .env.example to .env and fill in your credentials")
        sys.exit(1)
    
    return bot_token, chat_id


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Send a message via Telegram bot',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s "Hello World"
    %(prog)s "Bold text" --parse-mode HTML
    %(prog)s "Silent alert" --silent
    %(prog)s "No preview" --no-preview
        """
    )
    
    parser.add_argument(
        'message',
        help='Message text to send'
    )
    
    parser.add_argument(
        '--parse-mode',
        choices=['Markdown', 'HTML', 'none'],
        default='Markdown',
        help='Parse mode for message formatting (default: Markdown)'
    )
    
    parser.add_argument(
        '--silent',
        action='store_true',
        help='Send notification silently'
    )
    
    parser.add_argument(
        '--no-preview',
        action='store_true',
        help='Disable web page preview'
    )
    
    parser.add_argument(
        '--token',
        help='Telegram bot token (overrides environment variable)'
    )
    
    parser.add_argument(
        '--chat-id',
        help='Telegram chat ID (overrides environment variable)'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    if args.token and args.chat_id:
        bot_token = args.token
        chat_id = args.chat_id
    else:
        bot_token, chat_id = load_config()
    
    # Prepare parse mode
    parse_mode = args.parse_mode if args.parse_mode != 'none' else None
    
    # Send message
    success = send_telegram_message(
        bot_token=bot_token,
        chat_id=chat_id,
        message=args.message,
        parse_mode=parse_mode,
        disable_notification=args.silent,
        disable_web_page_preview=args.no_preview
    )
    
    if success:
        print("Message sent successfully!")
        sys.exit(0)
    else:
        print("Failed to send message")
        sys.exit(1)


if __name__ == '__main__':
    main()