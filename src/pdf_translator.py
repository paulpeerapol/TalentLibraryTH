import os
import json
import requests
import fitz  # PyMuPDF
from concurrent.futures import ThreadPoolExecutor, as_completed

# We define the font path inside the workspace assets directory
WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(WORKSPACE_DIR, "assets", "fonts")
FONT_PATH = os.path.join(FONT_DIR, "Sarabun-Regular.ttf")
FONT_URL = "https://github.com/google/fonts/raw/main/ofl/sarabun/Sarabun-Regular.ttf"

def ensure_sarabun_font():
    """
    Ensures that the Sarabun-Regular.ttf font is downloaded and available in assets/fonts/
    """
    if not os.path.exists(FONT_PATH):
        os.makedirs(FONT_DIR, exist_ok=True)
        print(f"Downloading Sarabun font from {FONT_URL}...")
        try:
            response = requests.get(FONT_URL, timeout=30)
            response.raise_for_status()
            with open(FONT_PATH, "wb") as f:
                f.write(response.content)
            print(f"Sarabun font successfully downloaded and saved to {FONT_PATH}")
        except Exception as e:
            print(f"Error downloading Sarabun font: {e}")
            # Fallback check if it's already in the system (e.g. C:\Windows\Fonts)
            system_paths = [
                "C:/Windows/Fonts/Sarabun-Regular.ttf",
                "C:/Windows/Fonts/THSarabunNew.ttf",
                "C:/Windows/Fonts/tahoma.ttf"
            ]
            for p in system_paths:
                if os.path.exists(p):
                    print(f"Using fallback system font: {p}")
                    return p
            raise FileNotFoundError(f"Could not download Sarabun font and no system fallback was found. Error: {e}")
    return FONT_PATH

def sRGB_to_rgb(srgb):
    """
    Converts PyMuPDF sRGB integer color to an RGB tuple of floats (0.0 to 1.0).
    """
    if srgb is None:
        return (0, 0, 0)
    # Extract RGB components from integer
    r = ((srgb >> 16) & 0xFF) / 255.0
    g = ((srgb >> 8) & 0xFF) / 255.0
    b = (srgb & 0xFF) / 255.0
    return (r, g, b)

def translate_blocks_gemini(blocks_text: list[dict], api_key: str) -> dict:
    """
    Sends a list of blocks to Gemini API to translate them to Thai in one go.
    blocks_text: list of dict with 'id' and 'text'
    """
    if not api_key:
        raise ValueError("Gemini API key is required for translation.")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={api_key}"
    
    prompt = f"""
    You are a professional book translator. Translate the following English text segments into natural, polite, and easy-to-understand Thai.
    Make sure the translation flows naturally for Thai readers, adjusting sentence structures as needed, but keeping the core meaning intact.
    Keep technical terms, proper nouns, or brand names in English if that is standard, or translate them contextually.
    
    Return the output ONLY as a JSON array of objects with the exact same 'id' and the translated 'text' in Thai.
    Do not add any markdown formatting (like ```json) or explanation outside the JSON array.
    
    JSON input to translate:
    {json.dumps(blocks_text, ensure_ascii=False)}
    """
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "response_mime_type": "application/json",
            "response_schema": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "id": {"type": "INTEGER"},
                        "text": {"type": "STRING"}
                    },
                    "required": ["id", "text"]
                }
            },
            "temperature": 0.3
        }
    }

    
    try:
        response = requests.post(url, json=payload, timeout=45)
        if response.status_code == 200:
            res_data = response.json()
            text_response = res_data["candidates"][0]["content"]["parts"][0]["text"]
            translated_list = json.loads(text_response)
            # Convert to dict for fast lookup
            return {item["id"]: item["text"] for item in translated_list if "id" in item and "text" in item}
        else:
            print(f"Gemini API Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Gemini API Exception during translation: {e}")
    return {}

def translate_chunk_worker(chunk: list, api_key: str) -> dict:
    """
    Worker function to translate a chunk of blocks concurrently.
    chunk: list of (page_num, block_idx, text, meta)
    """
    # Map local indices (0 to len(chunk)-1) to translation items
    translate_queue = [{"id": i, "text": item[2]} for i, item in enumerate(chunk)]
    
    translations = translate_blocks_gemini(translate_queue, api_key)
    
    # Map back to global page_num and block_idx keys
    results = {}
    for i, item in enumerate(chunk):
        page_num, block_idx, _, _ = item
        translated_text = translations.get(i)
        if translated_text:
            results[(page_num, block_idx)] = translated_text
    return results

def translate_pdf_layout(pdf_path: str, output_path: str, api_key: str, status_callback=None) -> str:
    """
    Translates an English PDF to Thai while preserving layout using the Sarabun font.
    Optimized to batch translation blocks and run queries concurrently using a ThreadPool.
    """
    font_file = ensure_sarabun_font()
    doc = fitz.open(pdf_path)
    font_obj = fitz.Font(fontname="sarabun", fontfile=font_file)
    
    if status_callback:
        status_callback("กำลังวิเคราะห์โครงสร้างเอกสารทั้งเล่ม...")
        
    all_blocks = []  # Tuples of (page_num, block_idx, text, meta)
    
    # Pass 1: Scan all pages and collect text blocks
    for page_num in range(len(doc)):
        page = doc[page_num]
        page_dict = page.get_text("dict")
        blocks = page_dict.get("blocks", [])
        
        for idx, block in enumerate(blocks):
            if block.get("type") == 0:  # Text block
                lines = block.get("lines", [])
                block_text_parts = []
                sizes = []
                colors = []
                dirs = []
                
                for line in lines:
                    line_dir = line.get("dir", (1.0, 0.0))
                    dirs.append(line_dir)
                    
                    spans = line.get("spans", [])
                    for span in spans:
                        span_text = span.get("text", "")
                        block_text_parts.append(span_text)
                        sizes.append(span.get("size", 11))
                        colors.append(span.get("color", 0))
                
                full_text = " ".join(block_text_parts).strip()
                if full_text and len(full_text) > 1 and not full_text.isdigit():
                    avg_size = sum(sizes) / len(sizes) if sizes else 11
                    common_color = max(set(colors), key=colors.count) if colors else 0
                    avg_dx = sum(d[0] for d in dirs) / len(dirs) if dirs else 1.0
                    avg_dy = sum(d[1] for d in dirs) / len(dirs) if dirs else 0.0
                    
                    meta = {
                        "bbox": block.get("bbox"),
                        "font_size": avg_size,
                        "color": common_color,
                        "dir": (avg_dx, avg_dy)
                    }
                    all_blocks.append((page_num, idx, full_text, meta))
                    
    if not all_blocks:
        doc.save(output_path)
        doc.close()
        return output_path
        
    # Group blocks into chunks of 50 to minimize API requests and prompt tokens overhead
    chunk_size = 50
    chunks = [all_blocks[i:i + chunk_size] for i in range(0, len(all_blocks), chunk_size)]
    
    if status_callback:
        status_callback(f"วิเคราะห์เจอข้อความ {len(all_blocks)} จุด. กำลังส่งแปลขนานกัน {len(chunks)} ชุดงาน...")
        
    global_translations = {}  # Map (page_num, block_idx) -> translated_text
    
    # Pass 2: Translate concurrently using ThreadPoolExecutor
    completed_chunks = 0
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(translate_chunk_worker, chunk, api_key): i for i, chunk in enumerate(chunks)}
        for future in as_completed(futures):
            chunk_idx = futures[future]
            try:
                chunk_results = future.result()
                global_translations.update(chunk_results)
                completed_chunks += 1
                if status_callback:
                    status_callback(f"แปลความหมายคืบหน้า: แปลแล้ว {completed_chunks}/{len(chunks)} ส่วน...")
            except Exception as e:
                print(f"Error in translating chunk {chunk_idx}: {e}")
                
    if status_callback:
        status_callback("เริ่มเขียนข้อความแปลกลับลงเอกสารทีละหน้า...")
        
    # Pass 3: Redact original texts and insert translated texts page-by-page
    for page_num in range(len(doc)):
        if status_callback:
            status_callback(f"กำลังจัดหน้าเอกสารแปล หน้า {page_num + 1}/{len(doc)}...")
            
        page = doc[page_num]
        page_blocks = [item for item in all_blocks if item[0] == page_num]
        
        for _, block_idx, _, meta in page_blocks:
            translated_text = global_translations.get((page_num, block_idx))
            if not translated_text:
                continue
                
            x0, y0, x1, y1 = meta["bbox"]
            dx, dy = meta["dir"]
            
            # Calculate rotation angle in degrees (0, 90, 180, 270)
            import math
            angle = math.degrees(math.atan2(dy, dx))
            angle = (angle + 360) % 360
            rotate = int(round(angle / 90.0) * 90) % 360
            
            # Calculate box dimensions
            box_width = x1 - x0
            box_height = y1 - y0
            
            # 1. Redact: Draw a white rectangle over the original text bounding box
            # We add a small 1.5px margin to fully mask the original English text
            rect = fitz.Rect(x0 - 1.5, y0 - 1.5, x1 + 1.5, y1 + 1.5)
            page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1), width=0)
            
            # 2. Adjust font size
            font_size = meta["font_size"] * 0.85
            font_factor = font_obj.ascender - font_obj.descender if font_obj.ascender else 1.3
            
            # If the text is rotated vertically, the line height is constrained by the box width
            if rotate in [90, 270]:
                font_size = min(font_size, box_width / (font_factor * 1.25))
                max_flow_length = box_height * 0.95
            else:
                # If horizontal, the line height is constrained by the box height
                if box_height > 5:
                    font_size = min(font_size, box_height / (font_factor * 1.25))
                max_flow_length = box_width * 0.95

            
            # For thin boxes (single line), we also dynamically shrink the font size
            # so the text doesn't overflow horizontally/vertically and cause bad wrapping
            thickness = box_width if rotate in [90, 270] else box_height
            is_single_line = thickness < (font_size * 2.2)
            
            if is_single_line:
                while font_size > 5.0:
                    text_len = font_obj.text_length(translated_text, fontsize=font_size)
                    if text_len <= max_flow_length:
                        break
                    font_size -= 0.5
            
            font_size = max(5.0, min(36.0, font_size))
            text_color = sRGB_to_rgb(meta["color"])
            
            # 3. Draw translated Thai text inside the box using the Sarabun font with rotation
            page.insert_textbox(
                rect,
                translated_text,
                fontname="sarabun",
                fontfile=font_file,
                fontsize=font_size,
                color=text_color,
                align=fitz.TEXT_ALIGN_LEFT,
                rotate=rotate
            )
            
    # Save the modified document
    doc.save(output_path)
    doc.close()
    return output_path
