import os
import asyncio
import edge_tts
from config import TTS_CONFIG

def generate_thai_speech_sync(text: str, output_mp3_path: str, voice: str = None) -> str:
    """
    Synthesizes ultra high-quality natural Thai Neural Audio Voice.
    """
    if not voice:
        voice = TTS_CONFIG.get("default_voice", "th-TH-NiwatNeural")
        
    rate = TTS_CONFIG.get("rate", "+0%")
    pitch = TTS_CONFIG.get("pitch", "+0Hz")
    
    async def _async_gen():
        communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
        await communicate.save(output_mp3_path)
        
    asyncio.run(_async_gen())
    return output_mp3_path

def get_audio_duration(mp3_path: str) -> float:
    """
    Calculates exact audio duration safely.
    """
    if not os.path.exists(mp3_path) or os.path.getsize(mp3_path) < 100:
        return 5.0
        
    try:
        from moviepy import AudioFileClip
        clip = AudioFileClip(mp3_path)
        dur = clip.duration
        clip.close()
        return max(3.0, dur)
    except Exception:
        try:
            from moviepy.editor import AudioFileClip
            clip = AudioFileClip(mp3_path)
            dur = clip.duration
            clip.close()
            return max(3.0, dur)
        except Exception:
            return max(3.0, round(os.path.getsize(mp3_path) / 7500.0, 1))

def generate_srt_subtitles(scenes_with_audio: list[dict], output_srt_path: str) -> str:
    """
    Generates a clean SubRip (.srt) subtitle file matching scenes audio timestamps.
    """
    current_time = 0.0
    srt_entries = []
    
    for idx, scene in enumerate(scenes_with_audio, start=1):
        duration = scene.get("audio_duration", 5.0)
        start_time = current_time
        end_time = current_time + duration
        current_time = end_time
        
        def format_time(seconds):
            hrs = int(seconds // 3600)
            mins = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            millis = int((seconds - int(seconds)) * 1000)
            return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"
            
        srt_text = scene.get("audio_script_th", "")
        srt_entries.append(
            f"{idx}\n{format_time(start_time)} --> {format_time(end_time)}\n{srt_text}\n"
        )
        
    with open(output_srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_entries))
        
    return output_srt_path
