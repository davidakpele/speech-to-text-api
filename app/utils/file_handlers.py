import os
import subprocess
from pathlib import Path
try:
    import magic
except ImportError:
    magic = None
from app.config import settings

def format_duration(seconds: float) -> str:
    """Converts a duration in seconds to a human-readable mm:ss format."""
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"

def format_file_size(size_bytes: int) -> str:
    """Convert file size to human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def get_file_metadata(file_path: Path) -> dict:
    """Get comprehensive file metadata using os and ffprobe."""
    try:
        file_size = os.path.getsize(file_path)
        size_formatted = format_file_size(file_size)
        
        mime_type = "unknown"
        if magic:
            try:
                mime_type = magic.from_file(str(file_path), mime=True)
            except Exception:
                pass
        
        duration = "N/A"
        try:
            result = subprocess.run([
                'ffprobe', '-v', 'error', '-show_entries', 
                'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', 
                str(file_path)
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                duration_seconds = float(result.stdout.strip())
                duration = format_duration(duration_seconds)
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, ValueError):
            pass
        
        return {
            "size": size_formatted,
            "format": mime_type,
            "duration": duration
        }
    except Exception as e:
        print(f"Error getting file metadata: {e}")
        return {
            "size": "unknown",
            "format": "unknown",
            "duration": "unknown"
        }

def convert_audio_to_wav(input_path: Path, output_path: Path) -> bool:
    """Converts an audio file to WAV format using FFmpeg."""
    try:
        subprocess.run(['ffmpeg', '-version'], check=True, capture_output=True, text=True)
        print(f"Converting '{input_path.name}' to WAV...")
        
        command = [
            'ffmpeg', '-i', str(input_path.resolve()),
            '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1',
            '-y',
            str(output_path.resolve())
        ]
        
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=300 
        )
        print("✅ Conversion successful.")
        return True
    except FileNotFoundError:
        print("❌ FFmpeg not found. Please ensure it's installed.")
        return False
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg conversion failed: {e.stderr}")
        return False
    except subprocess.TimeoutExpired:
        print("❌ FFmpeg conversion timed out.")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during conversion: {e}")
        return False
