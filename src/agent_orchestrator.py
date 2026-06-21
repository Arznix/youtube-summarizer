import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import schedule
import signal
import sys

from config import load_config, Config
from state_manager import StateManager
from mcp_server_youtube import YouTubeMCPServer
from ollama_client import OllamaClient
from mcp_server_notifier import TelegramMCPServer


class AgentOrchestrator:
    """Background scheduler daemon for YouTube summarizer pipeline."""
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the orchestrator.
        
        Args:
            config: Configuration object. If None, loads from default .env file.
        """
        self.config = config or load_config()
        self.state_manager = StateManager(self.config.database_path)
        self.youtube_server = YouTubeMCPServer()
        self.ollama_client = OllamaClient(self.config.ollama_host, self.config.ollama_model)
        self.telegram_server = TelegramMCPServer(
            self.config.telegram_bot_token,
            self.config.telegram_chat_id
        )
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('orchestrator.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Control flag for graceful shutdown
        self.running = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def check_new_videos(self) -> List[Dict[str, Any]]:
        """
        Check for new videos from subscribed channels.
        
        Returns:
            List of new video information.
        """
        self.logger.info("Checking for new videos...")
        
        new_videos = []
        channel_ids = self.config.youtube_channel_ids
        
        if not channel_ids:
            self.logger.warning("No YouTube channel IDs configured")
            return []
        
        for channel_id in channel_ids:
            try:
                # Fetch latest videos from RSS feed
                videos = self.youtube_server.fetch_latest_videos_from_rss(channel_id)
                
                for video in videos:
                    video_id = video.get('video_id')
                    if not video_id:
                        continue
                    
                    # Check if video already processed
                    if not self.state_manager.video_exists(video_id):
                        self.logger.info(f"New video found: {video.get('title', 'Unknown')}")
                        new_videos.append(video)
                    
            except Exception as e:
                self.logger.error(f"Error checking channel {channel_id}: {e}")
                continue
        
        return new_videos
    
    def process_video(self, video: Dict[str, Any]) -> bool:
        """
        Process a single video: extract transcript, summarize, send to Telegram.
        
        Args:
            video: Video information dictionary.
            
        Returns:
            True if processing succeeded, False otherwise.
        """
        video_id = video.get('video_id')
        title = video.get('title', 'Unknown Title')
        channel = video.get('channel', 'Unknown Channel')
        
        self.logger.info(f"Processing video: {title} ({video_id})")
        
        try:
            # Add video to state as pending
            self.state_manager.add_video(
                video_id=video_id,
                channel_name=channel,
                video_title=title,
                published_timestamp=video.get('published', datetime.now().isoformat())
            )
            
            # Update status to processing
            self.state_manager.update_video_status(video_id, 'PROCESSING')
            
            # Extract transcript
            self.logger.info(f"Extracting transcript for {video_id}")
            transcript = self.youtube_server.get_video_transcript(video_id)
            
            if not transcript:
                self.logger.warning(f"No transcript found for video {video_id}")
                self.state_manager.update_video_status(video_id, 'FAILED')
                return False
            
            # Truncate transcript if too long (12,000 characters safety limit)
            max_transcript_length = 12000
            if len(transcript) > max_transcript_length:
                transcript = transcript[:max_transcript_length] + "\n[Transcript truncated due to length]"
                self.logger.info(f"Transcript truncated to {max_transcript_length} characters")
            
            # Generate summary using Ollama
            self.logger.info(f"Generating summary for {video_id}")
            summary = self.ollama_client.generate_summary(
                transcript=transcript,
                video_title=title,
                channel_name=channel
            )
            
            if not summary:
                self.logger.error(f"Failed to generate summary for video {video_id}")
                self.state_manager.update_video_status(video_id, 'FAILED')
                return False
            
            # Send summary to Telegram
            self.logger.info(f"Sending summary to Telegram for {video_id}")
            success = self.telegram_server.send_telegram_summary(
                title=title,
                channel=channel,
                summary_body=summary
            )
            
            if success:
                self.state_manager.update_video_status(video_id, 'COMPLETED')
                self.logger.info(f"Successfully processed video: {title}")
                return True
            else:
                self.logger.error(f"Failed to send Telegram message for video {video_id}")
                self.state_manager.update_video_status(video_id, 'FAILED')
                return False
                
        except Exception as e:
            self.logger.error(f"Error processing video {video_id}: {e}")
            if video_id:
                self.state_manager.update_video_status(video_id, 'FAILED')
            return False
    
    def run_pipeline(self) -> None:
        """Run the complete pipeline: check for new videos and process them."""
        self.logger.info("Starting pipeline run...")
        
        try:
            # Check for new videos
            new_videos = self.check_new_videos()
            
            if not new_videos:
                self.logger.info("No new videos found")
                return
            
            self.logger.info(f"Found {len(new_videos)} new videos to process")
            
            # Process each video
            processed_count = 0
            for video in new_videos:
                if not self.running:
                    break
                
                success = self.process_video(video)
                if success:
                    processed_count += 1
                
                # Small delay between processing to avoid rate limiting
                time.sleep(1)
            
            self.logger.info(f"Pipeline run completed. Processed {processed_count}/{len(new_videos)} videos")
            
        except Exception as e:
            self.logger.error(f"Pipeline run failed: {e}")
    
    def start_scheduler(self, check_interval_minutes: int = 60) -> None:
        """
        Start the background scheduler.
        
        Args:
            check_interval_minutes: How often to check for new videos (in minutes).
        """
        self.logger.info(f"Starting scheduler with {check_interval_minutes} minute interval")
        self.running = True
        
        # Schedule the pipeline run
        schedule.every(check_interval_minutes).minutes.do(self.run_pipeline)
        
        # Run once immediately
        self.run_pipeline()
        
        # Keep running until shutdown signal
        while self.running:
            schedule.run_pending()
            time.sleep(1)
        
        self.logger.info("Scheduler stopped")
    
    def run_once(self) -> None:
        """Run the pipeline once and exit."""
        self.logger.info("Running pipeline once...")
        self.run_pipeline()
        self.logger.info("Single run completed")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of the orchestrator.
        
        Returns:
            Status dictionary with statistics.
        """
        stats = self.state_manager.get_statistics()
        
        return {
            "running": self.running,
            "channels_configured": len(self.config.youtube_channel_ids),
            "database_path": str(self.config.database_path),
            "ollama_host": self.config.ollama_host,
            "ollama_model": self.config.ollama_model,
            "telegram_chat_id": self.config.telegram_chat_id,
            "statistics": stats
        }


def main():
    """Main entry point for the orchestrator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="YouTube Summarizer Orchestrator")
    parser.add_argument("--once", action="store_true", help="Run pipeline once and exit")
    parser.add_argument("--interval", type=int, default=60, help="Check interval in minutes (default: 60)")
    parser.add_argument("--status", action="store_true", help="Show status and exit")
    parser.add_argument("--env", type=str, help="Path to .env file")
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        config = load_config(args.env)
        
        # Create orchestrator
        orchestrator = AgentOrchestrator(config)
        
        if args.status:
            # Show status
            status = orchestrator.get_status()
            print("Orchestrator Status:")
            for key, value in status.items():
                print(f"  {key}: {value}")
            return
        
        if args.once:
            # Run once
            orchestrator.run_once()
        else:
            # Start scheduler
            orchestrator.start_scheduler(args.interval)
            
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()