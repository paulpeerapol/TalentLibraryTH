import os
import asyncio
import edge_tts
from src.tts_engine import get_audio_duration
from config import TTS_CONFIG

def generate_notebooklm_podcast_dialogue(module_title: str, core_text: str) -> list[dict]:
    """
    Generates a NotebookLM-style Audio Overview dialogue script between 2 AI Co-Hosts.
    Host 1 (Male - Niwat): Main Presenter & Core Concepts.
    Host 2 (Female - Premwadee): Co-Host, Nuance & Practical Examples.
    """
    paragraphs = [p.strip() for p in core_text.split("\n\n") if p.strip()]
    intro_text = paragraphs[0][:150] if paragraphs else core_text[:150]
    detail_text = paragraphs[1][:150] if len(paragraphs) > 1 else intro_text
    
    dialogue = [
        {
            "speaker": "Host 1 (ชาย)",
            "voice": TTS_CONFIG["voice_male"],
            "text": f"สวัสดีครับทุกคน วันนี้เรามาเจาะลึกบทเรียนเรื่อง {module_title} กันครับ ประเด็นนี้น่าสนใจมากและเป็นแก่นความรู้ที่นำไปปรับใช้ในองค์กรได้ทันทีครับ"
        },
        {
            "speaker": "Host 2 (หญิง)",
            "voice": TTS_CONFIG["voice_female"],
            "text": f"ใช่ค่ะ! เรื่องนี้สำคัญมาก เพราะหลายคนอาจจะมองข้ามไป แต่ถ้าลองดูรายละเอียดแล้ว {intro_text} จะเห็นเลยว่าสร้างผลลัพธ์ที่แตกต่างอย่างเห็นได้ชัดค่ะ"
        },
        {
            "speaker": "Host 1 (ชาย)",
            "voice": TTS_CONFIG["voice_male"],
            "text": f"ถูกต้องเลยครับ! และอีกจุดหนึ่งที่ผมชอบมากในบทนี้คือ {detail_text} ซึ่งช่วยให้เราทำงานได้อย่างมีประสิทธิภาพและลดความผิดพลาดลงได้เยอะมากครับ"
        },
        {
            "speaker": "Host 2 (หญิง)",
            "voice": TTS_CONFIG["voice_female"],
            "text": "จริงค่ะ! สรุปแล้วถ้านำแนวคิดนี้ไปปรับใช้ร่วมกันทั้งทีม รับรองว่าจะช่วยยกระดับการทำงานและสร้างความประทับใจได้อย่างแน่นอนค่ะ"
        }
    ]
    return dialogue

def synthesize_podcast_audio_track(dialogue: list[dict], output_mp3_path: str) -> float:
    """
    Synthesizes multi-speaker NotebookLM audio dialogue track and combines into a single MP3.
    """
    temp_clips = []
    temp_dir = os.path.dirname(output_mp3_path)
    
    async def _synth_line(text, voice, out_p):
        comm = edge_tts.Communicate(text, voice)
        await comm.save(out_p)
        
    for idx, line in enumerate(dialogue):
        part_path = os.path.join(temp_dir, f"podcast_part_{idx:02d}.mp3")
        asyncio.run(_synth_line(line["text"], line["voice"], part_path))
        temp_clips.append(part_path)
        
    # Combine audio clips
    combined_data = bytearray()
    for cp in temp_clips:
        if os.path.exists(cp):
            with open(cp, "rb") as f:
                combined_data.extend(f.read())
            try:
                os.remove(cp)
            except Exception:
                pass
                
    with open(output_mp3_path, "wb") as f:
        f.write(combined_data)
        
    return get_audio_duration(output_mp3_path)
