# YouTube Summarizer

A locally hosted, privacy-focused YouTube subscription summarizer that monitors your YouTube subscriptions via RSS feeds, extracts transcripts, generates AI-powered summaries using Ollama/Qwen, and delivers them to your Telegram.

## Features

- **Privacy-First**: All processing happens locally - no data sent to external AI services
- **RSS Feed Monitoring**: No YouTube API quota required
- **Local AI Summarization**: Uses Ollama with Qwen 2.5 (7B) model
- **Telegram Notifications**: Delivers formatted summaries directly to your chat
- **State Management**: SQLite database tracks processed videos
- **Background Scheduling**: Automatic monitoring with configurable intervals
- **Modular Architecture**: Agent Skills pattern for reusability

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    YouTube Summarizer Pipeline                    │
├─────────────────────────────────────────────────────────────────┤
│  YouTube RSS Feeds  →  Transcript Extraction  →  Ollama/Qwen   │
│         ↓                      ↓                      ↓         │
│  State Manager  →  Agent Orchestrator  →  Telegram Notifier    │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Prerequisites
- Python 3.8+
- Ollama with qwen2.5:7b model
- Telegram bot token and chat ID
- YouTube channel IDs

See [PREREQUISITES.md](PREREQUISITES.md) for detailed setup instructions.

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/youtube-summarizer.git
cd youtube-summarizer

# Install dependencies
pip install -r requirements.txt

# Run setup wizard
python src/setup.py
```

### 3. Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
YOUTUBE_CHANNEL_IDS=channel_id_1,channel_id_2
```

### 4. Usage

```bash
# Run once to process new videos
python src/agent_orchestrator.py --once

# Run as background service (checks every 60 minutes)
python src/agent_orchestrator.py --interval 60

# Check status
python src/agent_orchestrator.py --status
```

## Project Structure

```
youtube-summarizer/
├── src/                          # Source code
│   ├── config.py                # Configuration management
│   ├── state_manager.py         # SQLite state tracking
│   ├── mcp_server_youtube.py    # YouTube RSS & transcripts
│   ├── ollama_client.py         # Ollama API client
│   ├── mcp_server_notifier.py   # Telegram notifications
│   ├── agent_orchestrator.py    # Main application logic
│   └── setup.py                 # Interactive setup wizard
├── skills/                       # Agent Skills (reusable components)
│   ├── youtube-rss-reader/      # YouTube RSS parsing skill
│   └── telegram-notifier/       # Telegram notification skill
├── .env.example                 # Configuration template
├── requirements.txt             # Python dependencies
├── test_agent.py                # Automated tests
├── PREREQUISITES.md             # Setup guide
└── README.md                    # This file
```

## Agent Skills

This project implements the Agent Skills pattern for modular, reusable components:

### YouTube RSS Reader Skill
- Parse YouTube channel RSS feeds
- Extract video metadata
- No API quotas required

### Telegram Notifier Skill
- Send formatted messages
- Support Markdown/HTML formatting
- Document and photo sending

See `skills/*/SKILL.md` for detailed documentation.

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | Telegram bot token from @BotFather |
| `TELEGRAM_CHAT_ID` | Yes | Your Telegram chat ID |
| `OLLAMA_HOST` | Yes | Ollama server URL (default: http://localhost:11434) |
| `OLLAMA_MODEL` | No | Model name (default: qwen2.5:7b) |
| `YOUTUBE_CHANNEL_IDS` | Yes | Comma-separated YouTube channel IDs |
| `LOG_LEVEL` | No | Logging level (default: INFO) |

### Security Features

- **Credential Isolation**: All secrets stored in `.env` file
- **Prompt Injection Defense**: System prompt anchoring for LLM
- **Resource Bounds**: Transcript truncation at 12,000 characters
- **Input Validation**: Sanitization of external data

## Testing

```bash
# Run all tests
python test_agent.py

# Run specific test class
python -m unittest test_agent.TestStateManager

# Run with coverage
pip install pytest-cov
pytest --cov=src test_agent.py
```

## Development

### Code Style
- Follow PEP 8 guidelines
- Use type hints
- Write docstrings for all public functions

### Adding New Skills

1. Create directory: `skills/your-skill-name/`
2. Add `SKILL.md` with YAML frontmatter
3. Include helper scripts in `scripts/` or `examples/`
4. Document usage and integration examples

## Troubleshooting

### Common Issues

1. **Ollama not connecting**
   - Ensure Ollama is running: `ollama serve`
   - Check if model is pulled: `ollama list`

2. **Telegram bot not responding**
   - Verify token in `.env`
   - Send at least one message to bot first
   - Check chat ID is correct

3. **YouTube RSS feed errors**
   - Verify channel ID is correct
   - Test with known working channel
   - Check network connectivity

### Debug Mode

Set `LOG_LEVEL=DEBUG` in `.env` for verbose logging.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Ollama](https://ollama.com/) for local LLM hosting
- [Telegram Bot API](https://core.telegram.org/bots/api) for messaging
- [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api) for transcript extraction
- [feedparser](https://feedparser.readthedocs.io/) for RSS parsing

## Support

For issues and questions:
- Check [PREREQUISITES.md](PREREQUISITES.md) for setup help
- Review [Troubleshooting](#troubleshooting) section
- Open an issue on GitHub