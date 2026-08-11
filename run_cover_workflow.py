import os
import sys
import glob
import shutil
import argparse
from config import BASE_DIR, GEMINI_API_KEY
from src.cover_generator import (
    translate_title_youtube_style,
    extract_frame,
    create_cover_image,
    create_cover_video,
    merge_videos
)

def main():
    # Set console encoding to UTF-8 to prevent encoding errors on Windows when printing Thai
    if sys.platform == "win32":
        try:
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="Automated Course Cover & Intro Video Workflow")
    parser.add_argument("--library-path", default="H:\\4 TalentLibrary", help="Path to the TalentLibrary root directory")
    parser.add_argument("--timestamp", type=float, default=16.0, help="Timestamp in seconds to extract highlight frame")
    parser.add_argument("--force", action="store_true", help="Force recreate cover images and videos even if they exist")
    args = parser.parse_args()

    library_path = args.library_path
    if not os.path.exists(library_path):
        print(f"Error: Library path does not exist: {library_path}")
        sys.exit(1)

    font_path = os.path.join(BASE_DIR, "assets", "fonts", "Sarabun-Regular.ttf")
    if not os.path.exists(font_path):
        print(f"Warning: Sarabun font not found at {font_path}. Using fallback system font.")
        font_path = "arial.ttf"

    print("=" * 60)
    print("STARTING AUTOMATED COVER & INTRO VIDEO WORKFLOW (MODERN YOUTUBE STYLE)")
    print(f"Target Library: {library_path}")
    print(f"Highlight Timestamp: {args.timestamp}s")
    print(f"Font Path: {font_path}")
    print("=" * 60)

    # Walk through the library to find course folders
    course_dirs = []
    for root, dirs, files in os.walk(library_path):
        has_trailer = any(f.endswith("_trailer.mp4") for f in files)
        has_first_unit = "1.mp4" in files
        if has_trailer and has_first_unit:
            course_dirs.append(root)

    if not course_dirs:
        print("No course directories containing both a trailer video (*_trailer.mp4) and a first unit (1.mp4) were found.")
        return

    print(f"Found {len(course_dirs)} course(s) to process:")
    for d in course_dirs:
        print(f"  - {os.path.relpath(d, library_path)}")
    print("-" * 60)

    for i, c_dir in enumerate(course_dirs):
        course_name_en = os.path.basename(c_dir)
        print(f"\n[{i+1}/{len(course_dirs)}] Processing Course: {course_name_en}")

        # Find the trailer video path
        trailer_files = glob.glob(os.path.join(c_dir, "*_trailer.mp4"))
        if not trailer_files:
            print("  Trailer file not found, skipping.")
            continue
        trailer_path = trailer_files[0]
        main_video_path = os.path.join(c_dir, "1.mp4")

        # Define outputs in the course directory
        static_cover_path = os.path.join(c_dir, f"{course_name_en}_cover_th.png")
        final_video_path = os.path.join(c_dir, "1_with_cover.mp4")

        # Skip if already generated and force is not set
        if os.path.exists(static_cover_path) and os.path.exists(final_video_path) and not args.force:
            print("  Outputs already exist, skipping. Use --force to regenerate.")
            continue

        try:
            # 1. Translate Title to Thai YouTube Style using Gemini
            print(f"  Translating course title to Thai YouTube Style...")
            title_dict = translate_title_youtube_style(course_name_en, GEMINI_API_KEY)
            
            # Use safe printing for Thai characters on Windows terminal
            try:
                print(f"    - Thai L1: {title_dict.get('line1')}")
                print(f"    - Thai L2: {title_dict.get('line2')} (Highlight)")
                print(f"    - Thai L3: {title_dict.get('line3')}")
            except UnicodeEncodeError:
                print(f"    - Thai Title: [Unicode Encoding Error on Terminal]")
            print(f"    - English Subtitle: {title_dict.get('subtitle_en')}")

            # Create temp files
            temp_dir = os.path.join(BASE_DIR, "temp")
            os.makedirs(temp_dir, exist_ok=True)
            extracted_frame_path = os.path.join(temp_dir, f"frame_{course_name_en}.png")
            temp_cover_video = os.path.join(temp_dir, f"intro_{course_name_en}.mp4")

            # 2. Background Handling: Use custom_bg.jpg if it exists, otherwise extract from trailer
            custom_bg_path = os.path.join(c_dir, "custom_bg.jpg")
            if os.path.exists(custom_bg_path):
                print("  🖼️ Found custom background image (custom_bg.jpg), using it instead of trailer frame...")
                shutil.copy(custom_bg_path, extracted_frame_path)
            else:
                print(f"  Extracting frame at {args.timestamp}s from trailer...")
                extract_frame(trailer_path, args.timestamp, extracted_frame_path)
                print("    - Frame extracted.")

            # 3. Create static cover image (16:9 YouTube style)
            print("  Creating static cover image...")
            create_cover_image(extracted_frame_path, title_dict, font_path, static_cover_path)
            print(f"    - Static cover saved: {static_cover_path}")

            # 4. Create 3-second cover intro video (with Ken Burns Zoom)
            print("  Rendering 3-second intro video (with zoom effect)...")
            create_cover_video(extracted_frame_path, title_dict, font_path, temp_cover_video, duration=3.0, zoom_effect=True)
            print("    - Intro video rendered.")

            # 5. Merge intro video with main e-learning video
            print("  Merging cover video with main video (1.mp4)...")
            merge_videos(temp_cover_video, main_video_path, final_video_path)
            print(f"    - Final video saved: {final_video_path}")

            # Cleanup temp files
            if os.path.exists(extracted_frame_path):
                os.remove(extracted_frame_path)
            if os.path.exists(temp_cover_video):
                os.remove(temp_cover_video)

            print("  Course processed successfully!")

        except Exception as e:
            print(f"  Error processing course: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("WORKFLOW COMPLETED!")
    print("=" * 60)

if __name__ == "__main__":
    main()
