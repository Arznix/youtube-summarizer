#!/usr/bin/env python3
"""
Extract YouTube Channel ID from URL

This script helps you extract YouTube channel IDs from channel URLs.
It supports various URL formats including:
- https://www.youtube.com/channel/UCxxxxxx
- https://www.youtube.com/c/ChannelName
- https://www.youtube.com/@ChannelHandle

Usage:
    python extract_channel_id.py <URL>
    python extract_channel_id.py https://www.youtube.com/@veritasium

Author: YouTube Summarizer Project
"""

import sys
import re
import requests
from typing import Optional


def extract_channel_id_from_url(url: str) -> Optional[str]:
    """
    Extract YouTube channel ID from a URL.
    
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
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        print(f"Fetching URL: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Look for channel ID in page source
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


def is_valid_channel_id(channel_id: str) -> bool:
    """
    Validate YouTube channel ID format.
    
    Args:
        channel_id: Channel ID to validate
        
    Returns:
        True if valid format, False otherwise
    """
    return bool(re.match(r'^UC[a-zA-Z0-9_-]{22}$', channel_id))


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("YouTube Channel ID Extractor")
        print("=" * 40)
        print()
        print("Usage:")
        print("  python extract_channel_id.py <URL>")
        print()
        print("Examples:")
        print("  python extract_channel_id.py https://www.youtube.com/@veritasium")
        print("  python extract_channel_id.py https://www.youtube.com/c/Veritasium")
        print("  python extract_channel_id.py https://www.youtube.com/channel/UCenyoq-ygS6aa1RBamUFqBw")
        print()
        print("Supported URL formats:")
        print("  - https://www.youtube.com/channel/UCxxxxxx")
        print("  - https://www.youtube.com/c/ChannelName")
        print("  - https://www.youtube.com/@ChannelHandle")
        print()
        
        # Interactive mode
        url = input("Enter YouTube channel URL: ").strip()
        if not url:
            print("No URL provided. Exiting.")
            sys.exit(1)
    else:
        url = sys.argv[1]
    
    # Extract channel ID
    channel_id = extract_channel_id_from_url(url)
    
    if channel_id:
        print()
        print("=" * 40)
        print(f"[OK] Channel ID: {channel_id}")
        print("=" * 40)
        print()
        print("Add this to your .env file:")
        print(f"YOUTUBE_CHANNEL_IDS={channel_id}")
    else:
        print()
        print("[ERROR] Could not extract channel ID from URL")
        print()
        print("Troubleshooting:")
        print("1. Make sure the URL is a valid YouTube channel URL")
        print("2. Try opening the URL in a browser first")
        print("3. You can find the channel ID manually by:")
        print("   - Going to the channel page")
        print("   - Viewing page source (Ctrl+U)")
        print("   - Searching for 'channelId' or 'externalId'")
        sys.exit(1)


if __name__ == "__main__":
    main()
