import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
import subprocess
from config import BRAND_CONFIG

def get_audio_duration_safe(mp3_path: str) -> float:
    if not os.path.exists(mp3_path) or os.path.getsize(mp3_path) < 100:
        return 5.0
    try:
        from moviepy import AudioFileClip
        clip = AudioFileClip(mp3_path)
        dur = clip.duration
        clip.close()
        return max(3.0, dur)
    except Exception:
        return max(3.0, round(os.path.getsize(mp3_path) / 7500.0, 1))

def draw_minimal_slide(
    scene_data: dict,
    output_image_path: str,
    width: int = 1920,
    height: int = 1080
) -> str:
    """
    Renders a STUNNING, modern, high-end 1920x1080 slide image with beautiful visual aesthetics.
    """
    # Beautiful Soft Slate-Blue Ambient Gradient Background
    image = Image.new("RGB", (width, height), "#F1F5F9")
    draw = ImageDraw.Draw(image)
    
    # Top Subtle Glow
    draw.rectangle([0, 0, width, 180], fill="#E2E8F0")
    draw.rectangle([0, 0, width, 8], fill="#0284C7")
    
    try:
        title_font = ImageFont.truetype("arial.ttf", 56)
        subtitle_font = ImageFont.truetype("arial.ttf", 32)
        body_font = ImageFont.truetype("arial.ttf", 30)
        badge_font = ImageFont.truetype("arial.ttf", 22)
    except IOError:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        body_font = ImageFont.load_default()
        badge_font = ImageFont.load_default()

    # 1. Top Badge Pill (Modern Floating Tag)
    scene_type = scene_data.get("scene_type", "MICRO-LESSON").upper()
    draw.rounded_rectangle([100, 50, 360, 95], radius=20, fill="#0284C7")
    draw.text((120, 60), f"★  {scene_type}", fill="#FFFFFF", font=badge_font)
    
    # 2. Main Title & Subtitle
    title_text = scene_data.get("slide_title", "Modern e-Learning Slide")
    draw.text((100, 130), title_text, fill="#0F172A", font=title_font)
    
    subtitle_text = scene_data.get("subtitle", "")
    if subtitle_text:
        draw.text((100, 215), subtitle_text, fill="#475569", font=subtitle_font)

    # 3. Main Glassmorphic Content Card (Left Container)
    c_left, c_top, c_right, c_bottom = 100, 290, 1160, 950
    # Card Background with Soft Drop Shadow Effect
    draw.rounded_rectangle([c_left+6, c_top+6, c_right+6, c_bottom+6], radius=20, fill="#CBD5E1")
    draw.rounded_rectangle([c_left, c_top, c_right, c_bottom], radius=20, fill="#FFFFFF", outline="#E2E8F0", width=2)
    
    # Render Bullet Cards
    bullets = scene_data.get("slide_bullets", [])
    y_pos = c_top + 40
    for bullet in bullets:
        # Bullet Pill Item Card
        b_right = c_right - 40
        draw.rounded_rectangle([c_left + 30, y_pos, b_right, y_pos + 80], radius=12, fill="#F8FAFC", outline="#E2E8F0", width=1)
        # Bullet Icon Dot
        draw.ellipse([c_left + 55, y_pos + 28, c_left + 75, y_pos + 48], fill="#0284C7")
        draw.text((c_left + 95, y_pos + 22), bullet, fill="#0F172A", font=body_font)
        y_pos += 105

    # 4. Highlight Callout Card (Right Container)
    hl_left, hl_top, hl_right, hl_bottom = 1210, 290, 1820, 950
    draw.rounded_rectangle([hl_left+6, hl_top+6, hl_right+6, hl_bottom+6], radius=20, fill="#CBD5E1")
    draw.rounded_rectangle([hl_left, hl_top, hl_right, hl_bottom], radius=20, fill="#FFFFFF", outline="#38BDF8", width=3)
    
    # Top Accent Ribbon
    draw.rounded_rectangle([hl_left, hl_top, hl_right, hl_top + 16], radius=10, fill="#D97706")
    
    draw.text((hl_left + 35, hl_top + 45), "💡 KEY TAKEAWAY", fill="#D97706", font=badge_font)
    
    highlight_text = scene_data.get("highlight_box", "สรุปประเด็นหลักเพื่อการปฏิบัติตามมาตรฐานองค์กร")
    lines = [highlight_text[i:i+22] for i in range(0, len(highlight_text), 22)]
    hl_y = hl_top + 110
    for line in lines:
        draw.text((hl_left + 35, hl_y), line, fill="#0F172A", font=body_font)
        hl_y += 55

    # 5. Bottom Modern Progress Bar
    draw.rectangle([0, height - 14, width, height], fill="#E2E8F0")
    draw.rectangle([0, height - 14, int(width * 0.75), height], fill="#0284C7")
    
    image.save(output_image_path)
    return output_image_path

def render_scene_video(
    image_path: str,
    audio_path: str,
    output_mp4_path: str,
    fps: int = 30
) -> str:
    """
    Renders a valid H.264 MP4 video file combining the slide image and audio using FFmpeg/OpenCV.
    """
    temp_silent_video = output_mp4_path.replace(".mp4", "_silent.mp4")
    duration = get_audio_duration_safe(audio_path)
    total_frames = int(duration * fps)
    
    img = cv2.imread(image_path)
    h, w, _ = img.shape
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_silent_video, fourcc, fps, (w, h))
    for _ in range(total_frames):
        out.write(img)
    out.release()
    
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    if os.path.exists(audio_path) and os.path.getsize(audio_path) > 100:
        cmd = [
            ffmpeg_exe, "-y",
            "-i", temp_silent_video,
            "-i", audio_path,
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-shortest",
            output_mp4_path
        ]
    else:
        cmd = [
            ffmpeg_exe, "-y",
            "-i", temp_silent_video,
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            output_mp4_path
        ]
        
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    if os.path.exists(temp_silent_video):
        try:
            os.remove(temp_silent_video)
        except Exception:
            pass
            
    return output_mp4_path

def concat_scene_videos(video_paths: list[str], final_mp4_path: str) -> str:
    """
    Concatenates scene MP4 clips into a seamless H.264 video.
    """
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    concat_list_file = final_mp4_path.replace(".mp4", "_list.txt")
    
    with open(concat_list_file, "w", encoding="utf-8") as f:
        for vp in video_paths:
            f.write(f"file '{os.path.abspath(vp)}'\n")
            
    cmd = [
        ffmpeg_exe, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list_file,
        "-c", "copy",
        final_mp4_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    if os.path.exists(concat_list_file):
        try:
            os.remove(concat_list_file)
        except Exception:
            pass
            
    return final_mp4_path
