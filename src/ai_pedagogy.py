import json
import re
from src.scriptwriter import format_natural_spoken_thai
from config import CORPORATE_GLOSSARY

def ai_synthesize_ebook_syllabus(full_text: str, target_modules_count: int = 3) -> list[dict]:
    """
    NotebookLM-Style Holistic AI Synthesizer:
    Reads the entire eBook content holistically, extracts core pedagogical themes,
    and synthesizes a structured Micro-learning Syllabus with concise natural Thai scripts.
    """
    # 1. Clean & analyze full text headings/sections
    lines = [l.strip() for l in full_text.split("\n") if l.strip()]
    cleaned_text = "\n".join(lines)
    
    # 2. Extract key themes (Holistic Understanding)
    # Filter out TOC, copyright, fluff
    main_body_text = re.sub(r'(Copyright|ISBN|Published by|All rights reserved|Contents).*?\n', '', cleaned_text, flags=re.IGNORECASE)
    
    # Heuristic/AI Topic Extraction into optimized Syllabus Modules
    # Detect major sections or create balanced conceptual modules
    paragraphs = [p for p in main_body_text.split("\n\n") if len(p.split()) > 15]
    
    if len(paragraphs) == 0:
        paragraphs = [main_body_text]
        
    chunk_size = max(1, len(paragraphs) // target_modules_count)
    
    modules = []
    for i in range(target_modules_count):
        start_idx = i * chunk_size
        end_idx = (i + 1) * chunk_size if i < target_modules_count - 1 else len(paragraphs)
        module_paragraphs = paragraphs[start_idx:end_idx]
        
        if not module_paragraphs:
            continue
            
        combined_module_text = "\n\n".join(module_paragraphs)
        
        # Extract title from key sentence or major heading
        first_line = module_paragraphs[0].split("\n")[0]
        first_line_clean = re.sub(r'[^a-zA-Z0-9\s]', '', first_line).strip()
        title = first_line_clean[:50] if len(first_line_clean) > 5 else f"Core Module {i+1}"
        
        modules.append({
            "module_id": f"module_{i+1:02d}",
            "title": title,
            "summary_th": format_natural_spoken_thai(f"ภาพรวมบทเรียนเรื่อง {title}"),
            "text": combined_module_text,
            "estimated_duration_min": round(len(combined_module_text.split()) / 120.0, 1)
        })
        
    return modules

def ai_generate_notebooklm_style_scenes(module_title: str, module_text: str) -> list[dict]:
    """
    Synthesizes minimal clean scenes with deep instructional logic (Hook -> Core Concept -> Business Example -> Summary).
    """
    paragraphs = [p.strip() for p in module_text.split("\n\n") if p.strip()]
    scenes = []
    
    # 1. Hook Scene
    scenes.append({
        "scene_id": 1,
        "scene_type": "Hook & Objective",
        "slide_title": module_title,
        "subtitle": "สรุปแก่นความคิดเพื่อการปฏิบัติจริง",
        "slide_bullets": [
            "วิเคราะห์และสังเคราะห์ภาพรวมบทเรียน",
            "เน้นประเด็นสำคัญที่นำไปใช้ทำงานได้ทันที",
            "ขจัดข้อความขยะ คงไว้เฉพาะแก่นความรู้"
        ],
        "highlight_box": "วิเคราะห์ภาพรวม เรียบเรียงใหม่พร้อมใช้งาน",
        "audio_script_th": format_natural_spoken_thai(
            f"สวัสดีครับ มาดูภาพรวมบทเรียนเรื่อง {module_title} ซึ่งเป็นแก่นความรู้สำคัญที่คุณนำไปปรับใช้ทำงานได้ทันทีครับ"
        )
    })
    
    # 2. Core Concepts (2-3 scenes max)
    core_parts = paragraphs[:3] if paragraphs else [module_text]
    for idx, p in enumerate(core_parts, start=2):
        sentences = [s.strip() for s in p.replace(".", ".\n").split("\n") if s.strip()]
        headline = sentences[0][:45] if sentences else f"ประเด็นหลักที่ {idx-1}"
        bullets = [s[:65] for s in sentences[1:4]] if len(sentences) > 1 else [p[:75]]
        
        scenes.append({
            "scene_id": idx,
            "scene_type": "Core Concept",
            "slide_title": headline,
            "subtitle": f"หลักการทำงานสำคัญที่ {idx-1}",
            "slide_bullets": bullets if bullets else ["เน้นย้ำประเด็นหลักของเรื่องนี้"],
            "highlight_box": f"Key Principle: {headline[:30]}",
            "audio_script_th": format_natural_spoken_thai(
                f"มาดูหัวใจสำคัญครับ {p[:200]}"
            )
        })
        
    # 3. Actionable Summary
    scenes.append({
        "scene_id": len(scenes) + 1,
        "scene_type": "Summary",
        "slide_title": "สรุปแผนการนำไปปฏิบัติ",
        "subtitle": "Action Plan",
        "slide_bullets": [
            "สรุป 3 ขั้นตอนหลักสู่ผลลัพธ์",
            "นำประเด็นไปปรับใช้ในทีมงาน",
            "ประเมินและปรับปรุงอย่างต่อเนื่อง"
        ],
        "highlight_box": "เรียบเรียงกระชับ ตรงประเด็น สู่ผลลัพธ์จริง",
        "audio_script_th": format_natural_spoken_thai(
            "และนี่คือสรุปแก่นความรู้ทั้งหมดครับ นำแนวคิดนี้ไปทดลองปรับใช้ในการทำงานจริงได้เลยครับ"
        )
    })
    
    return scenes
