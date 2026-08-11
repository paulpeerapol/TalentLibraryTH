import os
import cv2
import json
import requests
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
import subprocess

from src.gemini_notebooklm_api import get_active_gemini_api_key

def translate_title_youtube_style(title_en: str, api_key: str = None) -> dict:
    """
    Translates an English title and splits it into a 3-line YouTube thumbnail style JSON object.
    Requires extremely short, punchy lines (max 6-8 chars) to support large 100-120pt fonts.
    """
    if not api_key:
        api_key = get_active_gemini_api_key()
    if not api_key:
        return {
            "line1": "เรียนรู้",
            "line2": title_en[:10],
            "line3": "ระดับโปร",
            "subtitle_en": title_en
        }
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={api_key}"
    prompt = f"""
    คุณคือผู้เชี่ยวชาญด้านการออกแบบเนื้อหาบน YouTube (YouTube Creator) และผู้เชี่ยวชาญด้าน E-learning ภาษาไทย
    จงแปลชื่อหลักสูตรภาษาอังกฤษนี้ให้เป็นชื่อภาษาไทยที่ตื่นเต้น ดึงดูดสายตา น่าสนใจแบบหน้าปกคลิป YouTube
    โดยแบ่งข้อความเป็น 3 บรรทัด สำหรับการใส่การ์ดข้อความ (บรรทัดที่ 1 และ 3 จะใช้สีขาว, บรรทัดที่ 2 เป็นคำหลักที่น่าดึงดูดใจจะใช้สีเหลือง)
    และดึงชื่อหลักสูตรภาษาอังกฤษเป็นซับไตเติล
    
    ข้อกำหนดสำคัญ:
    1. ห้ามใช้เครื่องหมายอัญประกาศคู่ (") หรือเครื่องหมายคำพูดใดๆ ภายในค่าของฟิลด์ข้อความเด็ดขาด เพื่อป้องกัน JSON พัง
    2. แต่ละบรรทัด (line1, line2, line3) ต้องสั้นและกระชับมากๆ ความยาวไม่เกิน 6-8 ตัวอักษรต่อบรรทัดเท่านั้น เพื่อให้สามารถแสดงผลด้วยขนาดฟอนต์ยักษ์ 100-120pt ได้โดยไม่ล้นหน้าปก
    
    ชื่อภาษาอังกฤษ: "{title_en}"
    
    ส่งกลับเป็น JSON Object ในรูปแบบนี้เท่านั้น (ห้ามมีข้อความอธิบายอื่น):
    {{
      "line1": "บรรทัด 1 (ไม่เกิน 7 ตัวอักษร)",
      "line2": "บรรทัด 2 เน้น (ไม่เกิน 7 ตัวอักษร เช่น รู้ใจคน, เดาใจ, คัมภีร์, อัพสกิล)",
      "line3": "บรรทัด 3 (ไม่เกิน 7 ตัวอักษร)",
      "subtitle_en": "ชื่อภาษาอังกฤษของหลักสูตร"
    }}
    """
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.5
        }
    }
    
    text_response = ""
    try:
        response = requests.post(url, json=payload, timeout=15)
        if response.status_code == 200:
            res_data = response.json()
            text_response = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
            return json.loads(text_response)
        else:
            print(f"Gemini YouTube translation error Status: {response.status_code}")
    except Exception as e:
        print(f"Gemini YouTube translation exception: {e}")
        if text_response:
            try:
                import re
                l1 = re.search(r'"line1"\s*:\s*"([^"]+)"', text_response)
                l2 = re.search(r'"line2"\s*:\s*"([^"]+)"', text_response)
                l3 = re.search(r'"line3"\s*:\s*"([^"]+)"', text_response)
                sub = re.search(r'"subtitle_en"\s*:\s*"([^"]+)"', text_response)
                if l1 and l2 and l3 and sub:
                    return {
                        "line1": l1.group(1),
                        "line2": l2.group(1),
                        "line3": l3.group(1),
                        "subtitle_en": sub.group(1)
                    }
            except Exception:
                pass
                
    return {
        "line1": "เรียนรู้",
        "line2": title_en[:10],
        "line3": "ระดับโปร",
        "subtitle_en": title_en
    }

def extract_frame(video_path: str, timestamp_sec: float, output_path: str) -> str:
    """
    Extracts a frame from a video at a specific timestamp (in seconds) and saves it as an image.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
        
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Could not open video file: {video_path}")
        
    # Set position in milliseconds
    cap.set(cv2.CAP_PROP_POS_MSEC, timestamp_sec * 1000.0)
    success, frame = cap.read()
    
    if not success:
        cap.set(cv2.CAP_PROP_POS_MSEC, 0)
        success, frame = cap.read()
        if not success:
            cap.release()
            raise IOError(f"Failed to read any frame from: {video_path}")
            
    cv2.imwrite(output_path, frame)
    cap.release()
    return output_path

def draw_youtube_overlay(
    bg_img: Image.Image,
    title_dict: dict,
    font_path: str
) -> Image.Image:
    """
    Renders a clean, high-end YouTube cover overlay with NO container borders/boxes.
    Places the text directly on the left side of the background frame using the UID Sanookdee font.
    Text is tilted at -5 degrees as a single overlay, keeping the character on the right clean.
    """
    w, h = bg_img.size
    
    # 1. Prepare Background: Add a soft left-side dark shadow fade to make text legible on any background
    bg_rgba = bg_img.convert("RGBA")
    vignette = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    v_draw = ImageDraw.Draw(vignette)
    
    # Soft vignette on the left 55% of the screen
    for x in range(int(w * 0.55)):
        alpha = int(120 * (1.0 - x / (w * 0.55)))
        v_draw.line([(x, 0), (x, h)], fill=(15, 23, 42, alpha))
        
    bg_rgba = Image.alpha_composite(bg_rgba, vignette)
    
    # 2. Create the transparent text overlay canvas of size 1920x1080
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    o_draw = ImageDraw.Draw(overlay)
    
    # Get Font paths
    dir_path = os.path.dirname(font_path)
    title_font_path = os.path.join(dir_path, "UID_Sanookdee.ttf")
    if not os.path.exists(title_font_path):
        title_font_path = os.path.join(dir_path, "UID_Sanookdee.otf")
    if not os.path.exists(title_font_path):
        title_font_path = os.path.join(dir_path, "UID Sanookdee.ttf")
    # Fallback to Itim-Regular (which is round, handwritten, and fun)
    if not os.path.exists(title_font_path):
        title_font_path = os.path.join(dir_path, "Itim-Regular.ttf")
        
    sub_font_path = os.path.join(dir_path, "Itim-Regular.ttf")
    
    if not os.path.exists(title_font_path):
        title_font_path = font_path
    if not os.path.exists(sub_font_path):
        sub_font_path = font_path
        
    try:
        # Enlarge title font size: 180 point for Thai, 100 point for English
        font_thai = ImageFont.truetype(title_font_path, 180)
        font_sub = ImageFont.truetype(sub_font_path, 100)
    except IOError:
        font_thai = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        
    # Color palette
    c_brown = (48, 25, 8, 255)       # Chocolate brown stroke/contour
    c_yellow = (251, 191, 36, 255)    # Gold highlight
    c_white = (255, 255, 255, 255)    # White text
    
    # Combined Thai title text
    # Join line1, line2, line3 or construct from title_dict
    thai_title = title_dict.get("line1", "") + title_dict.get("line2", "") + title_dict.get("line3", "")
    # Clean up double spacing if any
    thai_title = thai_title.replace(" ", "")
    
    # Fallback to a clean translated title if the splits make it awkward
    if len(thai_title) < 3 or "เรียนรู้หลักสูตร" in thai_title:
        thai_title = "รู้ใจลูกค้าล่วงหน้า"
        
    sub_text = title_dict.get("subtitle_en", "E-Learning Course")
    
    # Draw Thai title and English subtitle directly on the canvas with thick strokes
    # Placed on the left side: x=140, y-positions shifted upward by 130px to avoid character
    x_pos = 140
    # Thai title: Gold/Yellow for high impact
    o_draw.text((x_pos, 150), thai_title, fill=c_yellow, font=font_thai, stroke_width=14, stroke_fill=c_brown)
    # English subtitle: White text
    o_draw.text((x_pos, 360), sub_text, fill=c_white, font=font_sub, stroke_width=10, stroke_fill=c_brown)
    
    # 3. Rotate the entire text overlay by -5 degrees so all lines tilt together
    rotated = overlay.rotate(-5, resample=Image.Resampling.BICUBIC)
    
    # 4. Composite the text overlay onto the background image
    combined = Image.alpha_composite(bg_rgba, rotated)
    
    return combined.convert("RGB")

def zoom_image(img: Image.Image, factor: float) -> Image.Image:
    """
    Resizes and crops an image to apply a centered zoom effect.
    """
    w, h = img.size
    new_w = int(w * factor)
    new_h = int(h * factor)
    resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    left = (new_w - w) // 2
    top = (new_h - h) // 2
    right = left + w
    bottom = top + h
    return resized.crop((left, top, right, bottom))

def create_cover_image(
    frame_path: str,
    title_dict: dict,
    font_path: str,
    output_path: str
) -> str:
    """
    Generates the static cover image.
    """
    img = Image.open(frame_path)
    img_resized = img.resize((1920, 1080), Image.Resampling.LANCZOS)
    
    cover_img = draw_youtube_overlay(img_resized, title_dict, font_path)
    cover_img.save(output_path, "PNG")
    return output_path

def create_cover_video(
    frame_path: str,
    title_dict: dict,
    font_path: str,
    output_mp4_path: str,
    duration: float = 3.0,
    fps: int = 30,
    zoom_effect: bool = True
) -> str:
    """
    Generates a 3-second cover intro video with smooth zoom-in animation and a silent audio track.
    """
    temp_silent_video = output_mp4_path.replace(".mp4", "_silent_temp.mp4")
    
    img = Image.open(frame_path)
    img_resized = img.resize((1920, 1080), Image.Resampling.LANCZOS)
    
    total_frames = int(duration * fps)
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_silent_video, fourcc, fps, (1920, 1080))
    
    for i in range(total_frames):
        if zoom_effect:
            factor = 1.0 + (0.08 * (i / (total_frames - 1)))
            bg_zoomed = zoom_image(img_resized, factor)
        else:
            bg_zoomed = img_resized.copy()
            
        frame_pil = draw_youtube_overlay(bg_zoomed, title_dict, font_path)
        frame_bgr = cv2.cvtColor(np.array(frame_pil), cv2.COLOR_RGB2BGR)
        out.write(frame_bgr)
        
    out.release()
    
    # Add a silent audio track to the video using FFmpeg
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        ffmpeg_exe, "-y",
        "-i", temp_silent_video,
        "-f", "lavfi",
        "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        output_mp4_path
    ]
    
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    if os.path.exists(temp_silent_video):
        try:
            os.remove(temp_silent_video)
        except Exception:
            pass
            
    return output_mp4_path

def merge_videos(cover_video_path: str, main_video_path: str, output_mp4_path: str) -> str:
    """
    Concatenates the 3-second cover intro video and the main video.
    """
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    
    cmd = [
        ffmpeg_exe, "-y",
        "-i", cover_video_path,
        "-i", main_video_path,
        "-filter_complex", "[0:v][0:a][1:v][1:a] concat=n=2:v=1:a=1 [v][a]",
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "veryfast",
        "-c:a", "aac",
        output_mp4_path
    ]
    
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_mp4_path
