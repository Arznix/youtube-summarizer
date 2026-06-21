---
name: telegram-notifier
description: Send notifications via Telegram Bot API. Use when building alert systems, monitoring notifications, or any application requiring real-time messaging through Telegram.
---

# Telegram Notifier

## Overview

Send notifications and messages via Telegram Bot API. This skill provides a complete integration with Telegram for sending formatted messages, documents, and alerts.

## When to Use

- Sending alerts and notifications
- Building monitoring systems
- Creating chatbots
- Delivering reports and summaries
- Real-time messaging applications

## Process

### 1. Create Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot`
3. Choose a name for your bot
4. Choose a username (must end with `bot`)
5. Copy the bot token (format: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

### 2. Get Chat ID

1. Send any message to your bot
2. Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
3. Find your chat ID in the response

### 3. Send Messages

Use the helper script or API directly:

```bash
python skills/telegram-notifier/examples/send_message.py "Hello World"
```

## Helper Scripts

### send_message.py

Send a message via Telegram bot:

```bash
# Basic message
python skills/telegram-notifier/examples/send_message.py "Hello World"

# With custom parse mode
python skills/telegram-notifier/examples/send_message.py "Bold text" --parse-mode HTML

# Silent notification
python skills/telegram-notifier/examples/send_message.py "Silent alert" --silent
```

## Integration Examples

### Basic Message Sending

```python
import requests

def send_telegram_message(bot_token, chat_id, message, parse_mode="Markdown"):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": parse_mode
    }
    
    response = requests.post(url, data=data)
    return response.json().get("ok", False)
```

### Formatted Messages

```python
def send_formatted_summary(bot_token, chat_id, title, summary, video_url=None):
    message = f"*{title}*\n\n{summary}"
    
    if video_url:
        message += f"\n\n[Watch Video]({video_url})"
    
    return send_telegram_message(bot_token, chat_id, message)
```

### Error Notifications

```python
import time

def send_error_alert(bot_token, chat_id, error_message, context=None):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    message = f"🚨 *Error Alert*\n\n*Error:* {error_message}"
    
    if context:
        message += f"\n*Context:* {context}"
    
    message += f"\n\n_Time: {timestamp}_"
    
    return send_telegram_message(bot_token, chat_id, message)
```

## Message Formatting

### Markdown Formatting

```python
# Bold
message = "*Bold text*"

# Italic
message = "_Italic text_"

# Code
message = "`Code snippet`"

# Links
message = "[Link text](https://example.com)"
```

### HTML Formatting

```python
# Bold
message = "<b>Bold text</b>"

# Italic
message = "<i>Italic text</i>"

# Code
message = "<code>Code snippet</code>"

# Links
message = '<a href="https://example.com">Link text</a>'
```

## Error Handling

### Common Issues

1. **Invalid Token**
   - Check token format (numbers:letters)
   - Regenerate token with @BotFather

2. **Chat Not Found**
   - Send at least one message to bot first
   - Verify chat ID is correct

3. **Rate Limiting**
   - Telegram allows 30 messages per second
   - Implement delays for bulk messages

4. **Message Too Long**
   - Maximum message length: 4096 characters
   - Split long messages

### Error Handling Code

```python
import requests
from requests.exceptions import RequestException

def safe_send_message(bot_token, chat_id, message, max_retries=3):
    for attempt in range(max_retries):
        try:
            result = send_telegram_message(bot_token, chat_id, message)
            if result:
                return True
            
            print(f"Attempt {attempt + 1} failed")
            
        except RequestException as e:
            print(f"Network error on attempt {attempt + 1}: {e}")
        
        # Wait before retry
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)  # Exponential backoff
    
    return False
```

## Best Practices

1. **Token Security**: Never commit bot tokens to version control
2. **Rate Limiting**: Implement delays for bulk messages
3. **Error Handling**: Always handle network errors gracefully
4. **Message Length**: Split long messages (max 4096 chars)
5. **Parse Mode**: Choose appropriate parse mode (Markdown/HTML)

## Security Considerations

- Store bot tokens in environment variables
- Never log bot tokens
- Use HTTPS for all API calls
- Validate chat IDs before sending
- Implement rate limiting

## See Also

- [Telegram Bot API Documentation](https://core.telegram.org/bots/api)
- [BotFather Documentation](https://core.telegram.org/bots#6-botfather)
- [Message Formatting](https://core.telegram.org/bots/api#formatting-options)