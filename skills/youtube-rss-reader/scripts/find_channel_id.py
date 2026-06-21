#!/usr/bin/env python3
"""
Find YouTube channel ID from channel handle.

This script converts YouTube channel handles (e.g., @channelname) to
channel IDs that can be used with YouTube RSS feeds.

Usage:
    python find_channel_id.py @channelname
    python find_channel_id.py channelname
    python find_channel_id.py https://www.youtube.com/@channelname
"""

import argparse
import re
import sys
from typing import Optional

import requests


def extract_channel_id_from_html(html: str) -> Optional[str]:
    """
    Extract channel ID from YouTube page HTML.
    
    Args:
        html: YouTube page HTML content
        
    Returns:
        Channel ID or None if not found
    """
    # Pattern 1: channelId in JSON
    patterns = [
        r'"channelId":"([^"]+)"',
        r'channel_id=([a-zA-Z0-9_-]+)',
        r'"externalId":"([^"]+)"',
        r'"browse_id":"([^"]+)"',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html)
        if match:
            channel_id = match.group(1)
            # Validate channel ID format (usually starts with UC and is 24 chars)
            if re.match(r'^UC[a-zA-Z0-9_-]{22}$', channel_id):
                return channel_id
    
    return None


def find_channel_id(channel_handle: str, timeout: int = 30) -> Optional[str]:
    """
    Find YouTube channel ID from channel handle.
    
    Args:
        channel_handle: YouTube channel handle (e.g., @channelname)
        timeout: HTTP request timeout in seconds
        
    Returns:
        Channel ID or None if not found
    """
    # Clean up the handle
    if channel_handle.startswith('@'):
        channel_handle = channel_handle[1:]
    
    # Remove URL prefix if present
    if 'youtube.com/' in channel_handle:
        match = re.search(r'youtube\.com/@?([^/]+)', channel_handle)
        if match:
            channel_handle = match.group(1)
    
    # Construct channel URL
    channel_url = f"https://www.youtube.com/@{channel_handle}"
    
    # Set headers to mimic a browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print(f"Fetching channel page: {channel_url}")
        response = requests.get(channel_url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        # Extract channel ID from page
        channel_id = extract_channel_id_from_html(response.text)
        
        if channel_id:
            return channel_id
        
        # Try alternative method: check RSS feed link
        rss_match = re.search(r'href="(https://www\.youtube\.com/feeds/videos\.xml\?channel_id=([^"]+))"', response.text)
        if rss_match:
            return rss_match.group(2)
        
        print(f"Could not find channel ID for: {channel_handle}")
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching channel page: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Find YouTube channel ID from channel handle',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s @veritasium
    %(prog)s 3blue1brown
    %(prog)s https://www.youtube.com/@veritasium
        """
    )
    
    parser.add_argument(
        'channel',
        help='YouTube channel handle (e.g., @channelname) or URL'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=30,
        help='HTTP request timeout in seconds (default: 30)'
    )
    
    args = parser.parse_args()
    
    # Find channel ID
    channel_id = find_channel_id(args.channel, args.timeout)
    
    if channel_id:
        print(f"\nChannel ID: {channel_id}")
        print(f"RSS Feed URL: https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}")
        sys.exit(0)
    else:
        print("\nFailed to find channel ID")
        sys.exit(1)


if __name__ == '__main__':
    main()