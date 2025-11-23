import os
import tempfile
import httpx
from typing import List, Optional
import PIL.Image

# Monkeypatch ANTIALIAS for moviepy compatibility with Pillow 10+
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

from moviepy.editor import VideoFileClip, ImageClip, concatenate_videoclips, AudioFileClip, CompositeVideoClip, vfx
from services.s3 import S3Service

class VideoService:
    """Service for video processing and compilation"""

    def __init__(self, s3_service: S3Service):
        self.s3_service = s3_service

    async def create_compilation(self, media_files: List[dict], output_filename: str = "compilation.mp4") -> Optional[str]:
        """
        Create a video compilation from a list of media files (images and videos).
        
        Args:
            media_files: List of dicts with 'url' and 'type' ('image' or 'video')
            output_filename: Name of the output file
            
        Returns:
            S3 URL of the generated video
        """
        if not media_files:
            return None

        temp_dir = tempfile.mkdtemp()
        clips = []
        downloaded_files = []

        try:
            print(f"[VIDEO_SERVICE] Processing {len(media_files)} media files...")
            
            # Download and process files
            async with httpx.AsyncClient() as client:
                for i, media in enumerate(media_files):
                    url = media['url']
                    media_type = media['type']
                    
                    # Handle S3 URLs if needed (presigned)
                    if url.startswith("s3://"):
                        url = self.s3_service.generate_presigned_url(url)

                    # Download file
                    ext = ".jpg" if media_type == "image" else ".mp4"
                    local_path = os.path.join(temp_dir, f"media_{i}{ext}")
                    
                    try:
                        response = await client.get(url)
                        if response.status_code != 200:
                            print(f"[VIDEO_SERVICE] Failed to download {url}")
                            continue
                            
                        with open(local_path, "wb") as f:
                            f.write(response.content)
                        
                        downloaded_files.append(local_path)
                        
                        # Create clip
                        if media_type == "image":
                            # Image clip: 3 seconds duration, resize to 720p height
                            # Pass duration to constructor to avoid set_duration issues
                            clip = ImageClip(local_path, duration=3)
                            
                            # Resize using vfx
                            clip = clip.fx(vfx.resize, height=720)
                            
                            # Add fade in/out
                            clip = clip.crossfadein(0.5)
                        else:
                            # Video clip: limit to 5 seconds, resize to 720p height
                            clip = VideoFileClip(local_path)
                            if clip.duration > 5:
                                clip = clip.subclip(0, 5)
                            
                            # Resize using vfx
                            clip = clip.fx(vfx.resize, height=720)
                            
                            # Add fade in/out
                            clip = clip.crossfadein(0.5)
                            
                        # Center crop to 9:16 aspect ratio (vertical video) or 16:9? 
                        # Let's stick to keeping aspect ratio but centered on a black background 1280x720
                        # For simplicity now, just concatenation
                        
                        clips.append(clip)
                        
                    except Exception as e:
                        print(f"[VIDEO_SERVICE] Error processing file {url}: {e}")
                        continue

            if not clips:
                print("[VIDEO_SERVICE] No valid clips created")
                return None

            print(f"[VIDEO_SERVICE] Concatenating {len(clips)} clips...")
            
            # Concatenate clips
            # method="compose" is safer for different sizes, but we should try to ensure consistency
            try:
                final_clip = concatenate_videoclips(clips, method="compose")
            except Exception as e:
                print(f"[VIDEO_SERVICE] Error concatenating clips: {e}")
                raise e
            
            # Write output file
            output_path = os.path.join(temp_dir, output_filename)
            print(f"[VIDEO_SERVICE] Writing video to {output_path}...")
            
            try:
                final_clip.write_videofile(
                    output_path, 
                    fps=24, 
                    codec='libx264', 
                    audio_codec='aac',
                    logger='bar' # Show progress bar in logs
                )
            except Exception as e:
                print(f"[VIDEO_SERVICE] Error writing video file (ffmpeg issue?): {e}")
                # Check if ffmpeg is installed
                import shutil
                if not shutil.which("ffmpeg"):
                    print("[VIDEO_SERVICE] CRITICAL: ffmpeg binary not found in PATH")
                raise e
            
            print(f"[VIDEO_SERVICE] Video generated at {output_path}")
            
            # Check if file exists and has size
            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                print("[VIDEO_SERVICE] Output file is missing or empty")
                return None
            
            # Upload to S3
            print(f"[VIDEO_SERVICE] Uploading to S3...")
            with open(output_path, "rb") as f:
                video_data = f.read()
                
            s3_url = await self.s3_service.upload_video(video_data, f"compilations/{output_filename}")
            
            print(f"[VIDEO_SERVICE] Video uploaded to {s3_url}")
            return s3_url

        except Exception as e:
            print(f"[VIDEO_SERVICE] Error creating compilation: {e}")
            import traceback
            traceback.print_exc()
            return None
            
        finally:
            # Cleanup
            print("[VIDEO_SERVICE] Cleaning up temp files...")
            for clip in clips:
                try:
                    clip.close()
                except:
                    pass
            
            for f in downloaded_files:
                try:
                    os.remove(f)
                except:
                    pass
            try:
                os.rmdir(temp_dir)
            except:
                pass
