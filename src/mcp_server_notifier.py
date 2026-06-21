import requests
import json
from typing import Optional, Dict, Any, Union
import logging
import time
from urllib.parse import quote


class TelegramMCPServer:
    """Telegram Bot API MCP Server for sending notifications."""
    
    def __init__(self, bot_token: str, chat_id: str):
        """
        Initialize Telegram MCP Server.
        
        Args:
            bot_token: Telegram bot token
            chat_id: Target chat ID
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.logger = logging.getLogger(__name__)
        
        # API base URL
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        
        # Default message limits
        self.max_message_length = 4096
        self.max_caption_length = 1024
    
    def _make_request(self, method: str, data: Dict[str, Any], timeout: int = 30) -> Optional[Dict[str, Any]]:
        """
        Make HTTP request to Telegram Bot API.
        
        Args:
            method: API method name
            data: Request payload
            timeout: Request timeout in seconds
            
        Returns:
            Response JSON or None if failed
        """
        try:
            url = f"{self.base_url}/{method}"
            
            response = requests.post(
                url,
                data=data,
                timeout=timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            if not result.get("ok"):
                error_code = result.get("error_code", "Unknown")
                description = result.get("description", "No description")
                self.logger.error(f"Telegram API error {error_code}: {description}")
                return None
            
            return result
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Telegram API request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse Telegram response: {e}")
            return None
    
    def send_message(
        self,
        text: str,
        parse_mode: Optional[str] = "Markdown",
        disable_web_page_preview: bool = False,
        disable_notification: bool = False
    ) -> bool:
        """
        Send text message to Telegram.
        
        Args:
            text: Message text
            parse_mode: Parse mode (Markdown, HTML, or None)
            disable_web_page_preview: Disable web page preview
            disable_notification: Send silently
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not text:
            self.logger.warning("Empty message text, skipping")
            return False
        
        # Truncate if too long
        if len(text) > self.max_message_length:
            text = text[:self.max_message_length - 20] + "\n\n[Message truncated]"
            self.logger.info(f"Message truncated to {self.max_message_length} characters")
        
        data = {
            "chat_id": self.chat_id,
            "text": text,
            "disable_web_page_preview": disable_web_page_preview,
            "disable_notification": disable_notification
        }
        
        if parse_mode:
            data["parse_mode"] = parse_mode
        
        result = self._make_request("sendMessage", data)
        
        if result:
            self.logger.info(f"Message sent successfully to chat {self.chat_id}")
            return True
        else:
            self.logger.error(f"Failed to send message to chat {self.chat_id}")
            return False
    
    def send_markdown_message(
        self,
        text: str,
        disable_notification: bool = False
    ) -> bool:
        """
        Send Markdown formatted message.
        
        Args:
            text: Markdown formatted text
            disable_notification: Send silently
            
        Returns:
            True if sent successfully, False otherwise
        """
        return self.send_message(
            text=text,
            parse_mode="Markdown",
            disable_notification=disable_notification
        )
    
    def send_html_message(
        self,
        text: str,
        disable_notification: bool = False
    ) -> bool:
        """
        Send HTML formatted message.
        
        Args:
            text: HTML formatted text
            disable_notification: Send silently
            
        Returns:
            True if sent successfully, False otherwise
        """
        return self.send_message(
            text=text,
            parse_mode="HTML",
            disable_notification=disable_notification
        )
    
    def send_telegram_summary(
        self,
        title: str,
        channel: str,
        summary_body: str,
        video_url: Optional[str] = None
    ) -> bool:
        """
        Send formatted video summary to Telegram.
        
        Args:
            title: Video title
            channel: Channel name
            summary_body: Summary content
            video_url: Optional video URL
            
        Returns:
            True if sent successfully, False otherwise
        """
        # Build message
        message_parts = []
        
        # Header
        message_parts.append(f"🎬 *{self._escape_markdown(title)}*")
        message_parts.append(f"📺 Channel: {self._escape_markdown(channel)}")
        message_parts.append("")
        
        # Summary
        message_parts.append("*Summary:*")
        message_parts.append(summary_body)
        
        # Video link
        if video_url:
            message_parts.append("")
            message_parts.append(f"[Watch Video]({video_url})")
        
        # Join message
        message = "\n".join(message_parts)
        
        # Send message
        return self.send_markdown_message(message)
    
    def _escape_markdown(self, text: str) -> str:
        """
        Escape special Markdown characters.
        
        Args:
            text: Text to escape
            
        Returns:
            Escaped text
        """
        # Characters that need escaping in Markdown
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        
        escaped_text = text
        for char in special_chars:
            escaped_text = escaped_text.replace(char, f"\\{char}")
        
        return escaped_text
    
    def send_document(
        self,
        document: Union[str, bytes],
        caption: Optional[str] = None,
        disable_notification: bool = False
    ) -> bool:
        """
        Send document to Telegram.
        
        Args:
            document: File path or bytes
            caption: Optional caption
            disable_notification: Send silently
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            url = f"{self.base_url}/sendDocument"
            
            data = {
                "chat_id": self.chat_id,
                "disable_notification": disable_notification
            }
            
            if caption:
                if len(caption) > self.max_caption_length:
                    caption = caption[:self.max_caption_length - 20] + "..."
                data["caption"] = caption
            
            files = {}
            if isinstance(document, str):
                # File path
                files["document"] = open(document, "rb")
            else:
                # Bytes
                files["document"] = ("document.txt", document)
            
            response = requests.post(
                url,
                data=data,
                files=files,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            if files.get("document"):
                files["document"].close()
            
            if result.get("ok"):
                self.logger.info(f"Document sent successfully to chat {self.chat_id}")
                return True
            else:
                error_code = result.get("error_code", "Unknown")
                description = result.get("description", "No description")
                self.logger.error(f"Telegram API error {error_code}: {description}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to send document: {e}")
            return False
    
    def send_photo(
        self,
        photo: Union[str, bytes],
        caption: Optional[str] = None,
        disable_notification: bool = False
    ) -> bool:
        """
        Send photo to Telegram.
        
        Args:
            photo: Photo file path, URL, or bytes
            caption: Optional caption
            disable_notification: Send silently
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            url = f"{self.base_url}/sendPhoto"
            
            data = {
                "chat_id": self.chat_id,
                "disable_notification": disable_notification
            }
            
            if caption:
                if len(caption) > self.max_caption_length:
                    caption = caption[:self.max_caption_length - 20] + "..."
                data["caption"] = caption
            
            files = {}
            if isinstance(photo, str):
                if photo.startswith(("http://", "https://")):
                    # URL
                    data["photo"] = photo
                else:
                    # File path
                    files["photo"] = open(photo, "rb")
            else:
                # Bytes
                files["photo"] = ("photo.jpg", photo)
            
            response = requests.post(
                url,
                data=data,
                files=files if files else None,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            if files.get("photo"):
                files["photo"].close()
            
            if result.get("ok"):
                self.logger.info(f"Photo sent successfully to chat {self.chat_id}")
                return True
            else:
                error_code = result.get("error_code", "Unknown")
                description = result.get("description", "No description")
                self.logger.error(f"Telegram API error {error_code}: {description}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to send photo: {e}")
            return False
    
    def get_me(self) -> Optional[Dict[str, Any]]:
        """
        Get bot information.
        
        Returns:
            Bot information dictionary or None if failed
        """
        result = self._make_request("getMe", {})
        if result:
            return result.get("result")
        return None
    
    def get_updates(self, offset: Optional[int] = None, limit: int = 100) -> list:
        """
        Get updates from Telegram.
        
        Args:
            offset: Identifier of the first update to be returned
            limit: Limits the number of updates to be retrieved
            
        Returns:
            List of updates
        """
        data = {"limit": limit}
        if offset:
            data["offset"] = offset
        
        result = self._make_request("getUpdates", data)
        if result:
            return result.get("result", [])
        return []
    
    def test_connection(self) -> bool:
        """
        Test connection to Telegram Bot API.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            bot_info = self.get_me()
            if bot_info:
                self.logger.info(f"Telegram connection successful. Bot: {bot_info.get('username')}")
                return True
            else:
                self.logger.error("Telegram connection test failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Telegram connection test failed: {e}")
            return False
    
    def send_error_notification(self, error_message: str, context: Optional[str] = None) -> bool:
        """
        Send error notification to Telegram.
        
        Args:
            error_message: Error message
            context: Optional context information
            
        Returns:
            True if sent successfully, False otherwise
        """
        message_parts = ["🚨 *Error Notification*"]
        message_parts.append("")
        message_parts.append(f"*Error:* {self._escape_markdown(error_message)}")
        
        if context:
            message_parts.append("")
            message_parts.append(f"*Context:* {self._escape_markdown(context)}")
        
        message_parts.append("")
        message_parts.append(f"_Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}_")
        
        message = "\n".join(message_parts)
        return self.send_markdown_message(message)