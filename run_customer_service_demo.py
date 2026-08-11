import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from src.ingestion import chunk_content_into_modules
from src.scriptwriter import generate_minimal_slides_from_text
from src.quiz_generator import generate_pre_test, generate_post_test, generate_knowledge_check
from src.tts_engine import generate_thai_speech_sync, get_audio_duration, generate_srt_subtitles
from src.slide_motion import draw_minimal_slide, render_scene_video, concat_scene_videos
from src.scorm_packager import create_scorm_package
from config import OUTPUT_DIR, TEMP_DIR, REVIEW_VIDEOS_DIR, SCORM_DIR

EBOOK_SAMPLE_TEXT = """
WHY CUSTOMER SERVICE MATTERS

Customer Contact & Everyone's Role
Customer service matters because everybody in every organization either helps customers directly or helps colleagues (internal customers) who serve the paying customer. Whether you work in commercial companies, public sector utilities, or government departments, everyone has customers.

Your Personal Needs vs Organisation Needs
Delivering good customer service gives you personal job satisfaction, reduces rework, and gives you more control of your workload. For the organization, great service creates a sustainable competitive advantage, increases profitability, and builds a stress-free work environment.
"""

def run_customer_service_demo_with_real_h264_mp4():
    print("=" * 60)
    print("[DEMO] Rendering Real H.264 MP4 Videos & SCORM Packages")
    print("=" * 60)
    
    modules = chunk_content_into_modules(EBOOK_SAMPLE_TEXT, target_word_count=180)
    print(f"Created {len(modules)} Micro-learning Modules!")
    
    pre_test = generate_pre_test(EBOOK_SAMPLE_TEXT)
    post_test = generate_post_test(EBOOK_SAMPLE_TEXT)
    
    review_summary = []
    
    for idx, mod in enumerate(modules, start=1):
        mod_title = mod["title"]
        safe_title = "".join(c for c in mod_title if c.isalnum() or c in (' ', '_')).rstrip().replace(" ", "_")
        print(f"\nProcessing Module {idx}: '{mod_title}'")
        
        scenes = generate_minimal_slides_from_text(mod_title, mod["text"])
        kc = generate_knowledge_check(mod_title, mod["text"])
        
        mod_dir = os.path.join(TEMP_DIR, f"cs_module_{idx:02d}")
        os.makedirs(mod_dir, exist_ok=True)
        
        scene_clips = []
        for sc in scenes:
            slide_img = os.path.join(mod_dir, f"slide_{sc['scene_id']:02d}.png")
            audio_file = os.path.join(mod_dir, f"audio_{sc['scene_id']:02d}.mp3")
            clip_file = os.path.join(mod_dir, f"clip_{sc['scene_id']:02d}.mp4")
            
            draw_minimal_slide(sc, slide_img)
            generate_thai_speech_sync(sc["audio_script_th"], audio_file)
            sc["audio_duration"] = get_audio_duration(audio_file)
            
            # Render H.264 Video Clip
            render_scene_video(slide_img, audio_file, clip_file)
            scene_clips.append(clip_file)
            
        # Standalone Video & Subtitle Export
        review_video_path = os.path.join(REVIEW_VIDEOS_DIR, f"Module_{idx:02d}_{safe_title}_FOR_REVIEW.mp4")
        review_srt_path = os.path.join(REVIEW_VIDEOS_DIR, f"Module_{idx:02d}_{safe_title}_Subtitles.srt")
        
        concat_scene_videos(scene_clips, review_video_path)
        generate_srt_subtitles(scenes, review_srt_path)
        
        print(f"   [REAL H.264 VIDEO RENDERED]: {review_video_path}")
        print(f"   [SUBTITLE EXPORTED]: {review_srt_path}")
        
        # SCORM Package
        scorm_zip = os.path.join(SCORM_DIR, f"Customer_Service_Module_{idx:02d}_SCORM.zip")
        create_scorm_package(
            f"Customer Service - {mod_title}",
            review_video_path,
            review_srt_path,
            scorm_zip,
            quiz_data={"pre_test": pre_test, "post_test": post_test, "knowledge_check": kc}
        )
        
        review_summary.append({
            "module_id": f"Module_{idx:02d}",
            "title": mod_title,
            "review_video_path": review_video_path,
            "review_srt_path": review_srt_path,
            "scorm_zip_path": scorm_zip
        })
        
    print("\n" + "=" * 60)
    print("[SUCCESS] REAL H.264 VIDEOS & SCORM PACKAGES EXPORTED!")
    print(f"Location: {REVIEW_VIDEOS_DIR}")
    print("=" * 60)
    return review_summary

if __name__ == "__main__":
    run_customer_service_demo_with_real_h264_mp4()
