import feedparser
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import re
from xml.etree import ElementTree as ET


class YouTubeMCPServer:
    """YouTube MCP Server for RSS feed parsing and transcript extraction."""
    
    def __init__(self, timeout: int = 30):
        """
        Initialize YouTube MCP Server.
        
        Args:
            timeout: HTTP request timeout in seconds
        """
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        
        # YouTube RSS feed base URL
        self.rss_base_url = "https://www.youtube.com/feeds/videos.xml"
        
        # YouTube video URL pattern
        self.video_url_pattern = re.compile(
            r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})'
        )
    
    def fetch_latest_videos_from_rss(self, channel_id: str) -> List[Dict[str, Any]]:
        """
        Fetch latest videos from YouTube channel RSS feed.
        
        Args:
            channel_id: YouTube channel ID
            
        Returns:
            List of video information dictionaries
        """
        try:
            # Construct RSS feed URL
            feed_url = f"{self.rss_base_url}?channel_id={channel_id}"
            
            self.logger.info(f"Fetching RSS feed for channel: {channel_id}")
            
            # Parse the feed
            feed = feedparser.parse(feed_url)
            
            if feed.bozo and not feed.entries:
                self.logger.error(f"Error parsing RSS feed for channel {channel_id}: {feed.bozo_exception}")
                return []
            
            videos = []
            
            for entry in feed.entries:
                try:
                    # Extract video ID from link
                    video_id = self._extract_video_id_from_url(entry.get('link', ''))
                    if not video_id:
                        continue
                    
                    # Extract video information
                    video_info = {
                        'video_id': video_id,
                        'title': entry.get('title', 'Unknown Title'),
                        'channel': self._extract_channel_name_from_feed(feed),
                        'published': entry.get('published', ''),
                        'updated': entry.get('updated', ''),
                        'link': entry.get('link', ''),
                        'summary': entry.get('summary', ''),
                        'media_thumbnail': self._extract_thumbnail(entry),
                        'yt_channel_id': channel_id
                    }
                    
                    videos.append(video_info)
                    
                except Exception as e:
                    self.logger.warning(f"Error processing entry: {e}")
                    continue
            
            self.logger.info(f"Found {len(videos)} videos for channel {channel_id}")
            return videos
            
        except Exception as e:
            self.logger.error(f"Error fetching RSS feed for channel {channel_id}: {e}")
            return []
    
    def _extract_video_id_from_url(self, url: str) -> Optional[str]:
        """
        Extract video ID from YouTube URL.
        
        Args:
            url: YouTube video URL
            
        Returns:
            Video ID or None if not found
        """
        match = self.video_url_pattern.search(url)
        if match:
            return match.group(1)
        
        # Try to extract from other URL formats
        if 'youtube.com' in url or 'youtu.be' in url:
            # Simple extraction for other formats
            if 'v=' in url:
                return url.split('v=')[1].split('&')[0]
        
        return None
    
    def _extract_channel_name_from_feed(self, feed: Any) -> str:
        """
        Extract channel name from feed data.
        
        Args:
            feed: Parsed feed object
            
        Returns:
            Channel name or 'Unknown Channel'
        """
        try:
            # Try to get from feed title
            if hasattr(feed, 'feed') and hasattr(feed.feed, 'title'):
                return feed.feed.title
            
            # Try to get from first entry
            if feed.entries:
                entry = feed.entries[0]
                if hasattr(entry, 'author'):
                    return entry.author
            
            return 'Unknown Channel'
            
        except Exception:
            return 'Unknown Channel'
    
    def _extract_thumbnail(self, entry: Any) -> Optional[str]:
        """
        Extract thumbnail URL from feed entry.
        
        Args:
            entry: Feed entry object
            
        Returns:
            Thumbnail URL or None
        """
        try:
            # Look for media_thumbnail
            if hasattr(entry, 'media_thumbnail'):
                thumbnails = entry.media_thumbnail
                if thumbnails and len(thumbnails) > 0:
                    return thumbnails[0].get('url', None)
            
            # Look for media_content
            if hasattr(entry, 'media_content'):
                media = entry.media_content
                for item in media:
                    if item.get('medium') == 'image':
                        return item.get('url', None)
            
            return None
            
        except Exception:
            return None
    
    def get_video_transcript(self, video_id: str, languages: List[str] = None) -> Optional[str]:
        """
        Extract video transcript using youtube-transcript-api.
        
        Args:
            video_id: YouTube video ID
            languages: List of preferred languages (default: ['en'])
            
        Returns:
            Transcript text or None if not available
        """
        if languages is None:
            languages = ['en']
        
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            
            self.logger.info(f"Fetching transcript for video: {video_id}")
            
            # Create API instance
            ytt_api = YouTubeTranscriptApi()
            
            # Try to get transcript
            try:
                transcript = ytt_api.fetch(video_id, languages=languages)
                
                # Combine transcript snippets
                transcript_text = ' '.join([snippet.text for snippet in transcript.snippets])
                
                self.logger.info(f"Successfully fetched transcript for video {video_id}")
                return transcript_text
                
            except Exception as e:
                self.logger.warning(f"Error fetching transcript for video {video_id}: {e}")
                
                # Try to list available transcripts and get any available
                try:
                    transcript_list = ytt_api.list(video_id)
                    
                    # Try to find any available transcript
                    for transcript in transcript_list:
                        try:
                            fetched_transcript = transcript.fetch()
                            transcript_text = ' '.join([snippet.text for snippet in fetched_transcript.snippets])
                            self.logger.info(f"Fetched transcript in alternative language for video {video_id}")
                            return transcript_text
                        except Exception:
                            continue
                    
                    # If no transcript found, return None
                    self.logger.warning(f"No transcript available for video {video_id}")
                    return None
                    
                except Exception as inner_e:
                    self.logger.error(f"Error listing transcripts for video {video_id}: {inner_e}")
                    return None
        
        except ImportError:
            self.logger.error("youtube-transcript-api not installed. Install with: pip install youtube-transcript-api")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error fetching transcript for video {video_id}: {e}")
            return None
    
    def get_video_metadata(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Get video metadata from YouTube page.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Video metadata dictionary or None
        """
        try:
            # Construct video URL
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            # Send request to YouTube
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(video_url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            # Extract basic metadata from page
            # Note: This is a simple extraction and may not work for all videos
            # For production use, consider using YouTube Data API or yt-dlp
            
            metadata = {
                'video_id': video_id,
                'url': video_url,
                'title': self._extract_title_from_html(response.text),
                'description': self._extract_description_from_html(response.text),
                'duration': self._extract_duration_from_html(response.text),
                'view_count': self._extract_view_count_from_html(response.text),
                'like_count': self._extract_like_count_from_html(response.text),
                'channel_name': self._extract_channel_from_html(response.text)
            }
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Error fetching metadata for video {video_id}: {e}")
            return None
    
    def _extract_title_from_html(self, html: str) -> Optional[str]:
        """Extract title from YouTube page HTML."""
        try:
            # Simple regex extraction
            title_match = re.search(r'"title":"([^"]*)"', html)
            if title_match:
                return title_match.group(1)
            
            # Alternative pattern
            title_match = re.search(r'<title>([^<]*)</title>', html)
            if title_match:
                return title_match.group(1).replace(' - YouTube', '')
            
            return None
            
        except Exception:
            return None
    
    def _extract_description_from_html(self, html: str) -> Optional[str]:
        """Extract description from YouTube page HTML."""
        try:
            # Simple regex extraction
            desc_match = re.search(r'"shortDescription":"([^"]*)"', html)
            if desc_match:
                description = desc_match.group(1)
                # Unescape JSON string
                description = description.replace('\\n', '\n').replace('\\"', '"')
                return description
            
            return None
            
        except Exception:
            return None
    
    def _extract_duration_from_html(self, html: str) -> Optional[str]:
        """Extract duration from YouTube page HTML."""
        try:
            # Look for duration in metadata
            duration_match = re.search(r'"lengthSeconds":"(\d+)"', html)
            if duration_match:
                seconds = int(duration_match.group(1))
                minutes = seconds // 60
                remaining_seconds = seconds % 60
                return f"{minutes}:{remaining_seconds:02d}"
            
            return None
            
        except Exception:
            return None
    
    def _extract_view_count_from_html(self, html: str) -> Optional[str]:
        """Extract view count from YouTube page HTML."""
        try:
            view_match = re.search(r'"viewCount":"(\d+)"', html)
            if view_match:
                return view_match.group(1)
            
            return None
            
        except Exception:
            return None
    
    def _extract_like_count_from_html(self, html: str) -> Optional[str]:
        """Extract like count from YouTube page HTML."""
        try:
            like_match = re.search(r'"likeCount":"(\d+)"', html)
            if like_match:
                return like_match.group(1)
            
            return None
            
        except Exception:
            return None
    
    def _extract_channel_from_html(self, html: str) -> Optional[str]:
        """Extract channel name from YouTube page HTML."""
        try:
            channel_match = re.search(r'"ownerChannelName":"([^"]*)"', html)
            if channel_match:
                return channel_match.group(1)
            
            return None
            
        except Exception:
            return None
    
    def find_channel_id(self, channel_handle: str) -> Optional[str]:
        """
        Find channel ID from channel handle.
        
        Args:
            channel_handle: YouTube channel handle (e.g., '@channelname')
            
        Returns:
            Channel ID or None if not found
        """
        try:
            # Remove @ if present
            if channel_handle.startswith('@'):
                channel_handle = channel_handle[1:]
            
            # Construct channel URL
            channel_url = f"https://www.youtube.com/@{channel_handle}"
            
            # Send request to YouTube
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(channel_url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            # Extract channel ID from page
            channel_id_match = re.search(r'"channelId":"([^"]*)"', response.text)
            if channel_id_match:
                return channel_id_match.group(1)
            
            # Alternative pattern
            channel_id_match = re.search(r'channel_id=([a-zA-Z0-9_-]+)', response.text)
            if channel_id_match:
                return channel_id_match.group(1)
            
            self.logger.warning(f"Could not find channel ID for handle: {channel_handle}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding channel ID for handle {channel_handle}: {e}")
            return None
    
    def test_connection(self) -> bool:
        """
        Test connection to YouTube.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Test RSS feed access
            test_url = "https://www.youtube.com/feeds/videos.xml?channel_id=UC-lHJZR3Gqxm24_Vd_AJ5Yw"
            response = requests.get(test_url, timeout=self.timeout)
            
            if response.status_code == 200:
                self.logger.info("YouTube connection test successful")
                return True
            else:
                self.logger.warning(f"YouTube connection test failed with status: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"YouTube connection test failed: {e}")
            return False