import os
import sys
import json

from config import OUTPUT_DIR, TEMP_DIR, SCORM_DIR
from src.ingestion import extract_text_from_file, chunk_content_into_modules
from src.scriptwriter import generate_minimal_slides_from_text
from src.tts_engine import generate_thai_speech_sync, get_audio_duration, generate_srt_subtitles
from src.slide_motion import draw_minimal_slide, render_scene_video, concat_scene_videos
from src.scorm_packager import create_scorm_package

def run_pipeline_for_module(module_data: dict, module_index: int = 1) -> dict:
    """
    Executes full pipeline for a single micro-learning module.
    """
    title = module_data["title"]
    text = module_data["text"]
    mod_id = f"module_{module_index:02d}"
    
    print(f"\n==========================================")
    print(f"🚀 Processing: [{mod_id}] {title}")
    print(f"==========================================")
    
    # Step 1: Generate Minimal Clean Scenes & Thai Script
    print("📝 Step 1: Generating Minimal Clean Scenes & Thai Script...")
    scenes = generate_minimal_slides_from_text(title, text)
    
    mod_temp_dir = os.path.join(TEMP_DIR, mod_id)
    os.makedirs(mod_temp_dir, exist_ok=True)
    
    scene_video_paths = []
    
    # Step 2: Render Slides & Synthesize Audio per Scene
    for scene in scenes:
        scene_id = scene["scene_id"]
        print(f"   🎬 Processing Scene {scene_id}/{len(scenes)}: {scene['slide_title']}")
        
        # Draw Slide Image
        img_path = os.path.join(mod_temp_dir, f"slide_{scene_id:02d}.png")
        draw_minimal_slide(scene, img_path)
        
        # Synthesize Thai TTS
        audio_path = os.path.join(mod_temp_dir, f"audio_{scene_id:02d}.mp3")
        generate_thai_speech_sync(scene["audio_script_th"], audio_path)
        scene["audio_duration"] = get_audio_duration(audio_path)
        
        # Render Video Scene Clip
        clip_path = os.path.join(mod_temp_dir, f"clip_{scene_id:02d}.mp4")
        try:
            render_scene_video(img_path, audio_path, clip_path)
            scene_video_paths.append(clip_path)
        except Exception as e:
            print(f"   ⚠️ MoviePy video render skipped ({e}). Image & Audio generated.")
            
    # Step 3: Concatenate Final Module Video
    final_video_path = os.path.join(OUTPUT_DIR, f"{mod_id}_video.mp4")
    srt_path = os.path.join(OUTPUT_DIR, f"{mod_id}_subtitles.srt")
    
    # Subtitles
    generate_srt_subtitles(scenes, srt_path)
    
    if scene_video_paths:
        print("📹 Step 3: Merging scene clips into final module MP4...")
        concat_scene_videos(scene_video_paths, final_video_path)
    else:
        print("⚠️ Video merging skipped. Outputs ready in temp folder.")
        
    # Step 4: SCORM Package Export
    print("📦 Step 4: Exporting SCORM 1.2 Package for LMS...")
    scorm_zip_path = os.path.join(SCORM_DIR, f"{mod_id}_SCORM.zip")
    create_scorm_package(title, final_video_path, srt_path, scorm_zip_path)
    
    print(f"✅ Finished [{mod_id}]!")
    print(f"   - Video MP4: {final_video_path}")
    print(f"   - SCORM ZIP: {scorm_zip_path}")
    
    return {
        "module_id": mod_id,
        "title": title,
        "video_path": final_video_path,
        "scorm_path": scorm_zip_path,
        "scenes": scenes
    }

if __name__ == "__main__":
    # Sample Test Content
    sample_text = """
    Instructional Design in the Modern Enterprise.
    Modern learning and development requires creating micro-learning content that engages employees.
    By breaking down dense eBooks into bite-sized video modules, organizations can dramatically increase completion rates.
    
    Key Strategy 1: Focus on Actionable Insights.
    Always begin with a strong hook and clear learning objective.
    Use minimal clean visual slides to highlight core KPIs and concepts without cluttering the screen.
    
    Key Strategy 2: Enterprise Integration.
    Ensure every module exports to SCORM standards so that your LMS like Moodle or SuccessFactors can track employee completion effortlessly.
    """
    
    print("🚀 Starting eBook-to-eLearning Production Pipeline...")
    chunks = chunk_content_into_modules(sample_text, target_word_count=200)
    for idx, chunk in enumerate(chunks, start=1):
        run_pipeline_for_module(chunk, idx)
