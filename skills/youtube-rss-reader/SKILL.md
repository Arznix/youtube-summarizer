---
name: youtube-rss-reader
description: Parse YouTube channel RSS feeds to discover new videos without API quotas. Use when monitoring YouTube channels for new content, extracting video metadata, or building feed-based applications.
---

# YouTube RSS Reader

## Overview

Parse YouTube channel RSS feeds to discover new videos without YouTube Data API quotas. This skill provides privacy-friendly access to YouTube channel updates using standard RSS feeds.

## When to Use

- Monitoring YouTube channels for new videos
- Building RSS feed readers for YouTube content
- Extracting video metadata without API keys
- Creating automated video discovery systems
- Avoiding YouTube Data API quota limits

## Process

### 1. Find Channel ID

First, you need the YouTube channel ID. Use the helper script:

```bash
python skills/youtube-rss-reader/scripts/find_channel_id.py @channelname
```

Or manually:
1. Go to the YouTube channel page
2. View page source (Ctrl+U)
3. Search for `channel_id=` in RSS feed link
4. The channel ID looks like: `UC-lHJZR3Gqxm24_Vd_AJ5Yw`

### 2. Construct RSS Feed URL

YouTube RSS feed URL format:
```
https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID
```

### 3. Parse the Feed

Use the `feedparser` library to parse the RSS feed:

```python
import feedparser

feed_url = "https://www.youtube.com/feeds/videos.xml?channel_id=UC-lHJZR3Gqxm24_Vd_AJ5Yw"
feed = feedparser.parse(feed_url)

for entry in feed.entries:
    video_id = entry.yt_videoid
    title = entry.title
    published = entry.published
    link = entry.link
```

### 4. Extract Video Information

Each feed entry contains:
- `yt_videoid`: YouTube video ID
- `title`: Video title
- `published`: Publication timestamp
- `link`: Video URL
- `summary`: Video description
- `media_thumbnail`: Thumbnail URL

## Helper Scripts

### find_channel_id.py

Converts YouTube channel handle to channel ID:

```bash
# Basic usage
python skills/youtube-rss-reader/scripts/find_channel_id.py @veritasium

# With custom timeout
python skills/youtube-rss-reader/scripts/find_channel_id.py @3blue1brown --timeout 10
```

## Integration Examples

### Basic RSS Feed Reader

```python
from skills.youtube_rss_reader import YouTubeRSSReader

reader = YouTubeRSSReader()
videos = reader.get_latest_videos("UC-lHJZR3Gqxm24_Vd_AJ5Yw")

for video in videos:
    print(f"New video: {video['title']}")
    print(f"URL: {video['link']}")
```

### With State Management

```python
import feedparser
from state_manager import StateManager

def check_new_videos(channel_id, state_manager):
    feed = feedparser.parse(f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}")
    
    new_videos = []
    for entry in feed.entries:
        video_id = entry.yt_videoid
        if not state_manager.video_exists(video_id):
            new_videos.append({
                'video_id': video_id,
                'title': entry.title,
                'link': entry.link
            })
    
    return new_videos
```

## Error Handling

### Common Issues

1. **Invalid Channel ID**
   - Verify channel ID is 24 characters long
   - Starts with `UC` (usually)
   - Check for typos

2. **Feed Not Found**
   - Channel may be invalid or private
   - RSS feed may be disabled
   - Check network connectivity

3. **Rate Limiting**
   - YouTube may temporarily block requests
   - Implement exponential backoff
   - Cache feed responses

### Error Handling Code

```python
import feedparser
import requests
from requests.exceptions import RequestException

def safe_fetch_feed(channel_id, timeout=30):
    try:
        feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        response = requests.get(feed_url, timeout=timeout)
        response.raise_for_status()
        
        feed = feedparser.parse(response.content)
        if feed.bozo and not feed.entries:
            raise ValueError(f"Invalid feed: {feed.bozo_exception}")
        
        return feed
        
    except RequestException as e:
        print(f"Network error: {e}")
        return None
    except Exception as e:
        print(f"Error parsing feed: {e}")
        return None
```

## Best Practices

1. **Cache Responses**: Cache feed responses to avoid repeated requests
2. **Rate Limiting**: Implement delays between requests (1-2 seconds)
3. **Error Handling**: Always handle network errors gracefully
4. **User-Agent**: Set appropriate User-Agent header
5. **Timeouts**: Use reasonable timeouts (30 seconds default)

## Security Considerations

- RSS feeds are public and don't require authentication
- Channel IDs are not sensitive information
- No API keys needed for basic RSS access
- Be aware of YouTube's Terms of Service

## See Also

- [YouTube RSS Feed Format](https://www.youtube.com/rss)
- [Feedparser Documentation](https://feedparser.readthedocs.io/)
- [YouTube Data API](https://developers.google.com/youtube/v3) (for more features)