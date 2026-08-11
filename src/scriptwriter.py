import json
import re
from config import CORPORATE_GLOSSARY

def apply_corporate_glossary(text: str) -> str:
    """
    Replaces technical/business English terms with standard Thai corporate terms based on glossary config.
    """
    processed_text = text
    for en_term, th_term in CORPORATE_GLOSSARY.items():
        pattern = re.compile(re.escape(en_term), re.IGNORECASE)
        processed_text = pattern.sub(th_term, processed_text)
    return processed_text

def format_natural_spoken_thai(text: str) -> str:
    """
    Refines raw text into direct, natural spoken Thai (ภาษาพูดครูผู้สอน ไม่พร่ำเพรื่อ ไม่เยิ่นเย้อ ไร้ภาษาแปลแข็งๆ สไตล์ AI).
    """
    text = apply_corporate_glossary(text)
    
    # 1. Eliminate robotic AI filler phrases & stiff written Thai phrases
    replacements = [
        ("ในบทเรียนนี้เราจะมาเรียนรู้เกี่ยวกับเรื่อง", "สวัสดีครับ มาดูประเด็นสำคัญเรื่อง"),
        ("มันเป็นสิ่งสำคัญมากที่เราต้องทำการ", "เรื่องนี้สำคัญมากครับ เพราะเราต้อง"),
        ("ทำการประยุกต์ใช้", "ปรับใช้"),
        ("ทำการสกัด", "ย่อย"),
        ("มีความจำเป็นที่จะต้อง", "ต้อง"),
        ("ส่งผลทำให้เกิด", "ทำให้เกิด"),
        ("ในส่วนของเนื้อหาบทเรียนนี้", "ในบทนี้"),
        ("และนั่นคือสรุปทั้งหมดของเนื้อหาในบทเรียนนี้ครับ", "และนี่คือสรุปประเด็นหลักครับ"),
    ]
    
    for stiff_phrase, natural_phrase in replacements:
        text = text.replace(stiff_phrase, natural_phrase)
        
    # 2. Ensure concise and natural opener
    if not any(text.startswith(w) for w in ["สวัสดี", "มาดู", "สำหรับ", "ประเด็น"]):
        text = "มาดูประเด็นหลักกันครับ " + text
        
    return text.strip()

def generate_minimal_slides_from_text(module_title: str, text: str) -> list[dict]:
    """
    Converts module text into a structured list of minimal clean video scenes.
    Uses concise natural spoken Thai script.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    scenes = []
    
    # Scene 1: Hook & Objective
    scenes.append({
        "scene_id": 1,
        "scene_type": "Hook & Objective",
        "slide_title": module_title,
        "subtitle": "Overview & Key Takeaways",
        "slide_bullets": [
            "ย่อยเนื้อหากระชับ นำไปใช้ได้ทันที",
            "เทคนิคและแนวทางปฏิบัติจริง",
            "สรุปประเด็นสำคัญประจำบท"
        ],
        "highlight_box": "สรุปกระชับ นำไปปฏิบัติได้จริงทันที",
        "audio_script_th": format_natural_spoken_thai(
            f"สวัสดีครับ มาดูประเด็นสำคัญเรื่อง {module_title} ซึ่งเป็นเทคนิคที่นำไปปรับใช้ทำงานได้ทันทีครับ"
        )
    })
    
    # Scene 2 & 3: Core Concepts
    core_paragraphs = paragraphs[1:4] if len(paragraphs) > 1 else [text]
    for idx, p in enumerate(core_paragraphs, start=2):
        sentences = [s.strip() for s in p.replace(".", ".\n").split("\n") if s.strip()]
        headline = sentences[0][:50] if sentences else f"Key Concept {idx-1}"
        bullets = [s[:70] for s in sentences[1:4]] if len(sentences) > 1 else [p[:80]]
        
        scenes.append({
            "scene_id": idx,
            "scene_type": "Core Concept",
            "slide_title": headline,
            "subtitle": f"หลักการสำคัญที่ {idx-1}",
            "slide_bullets": bullets if bullets else ["สรุปแนวคิดหลักของประเด็นนี้"],
            "highlight_box": f"Key Point: {headline}",
            "audio_script_th": format_natural_spoken_thai(
                f"หัวใจสำคัญเรื่องนี้คือ {p}"
            )
        })
        
    # Final Scene: Summary
    scenes.append({
        "scene_id": len(scenes) + 1,
        "scene_type": "Summary",
        "slide_title": "สรุปประเด็นสำคัญ",
        "subtitle": "Action Plan",
        "slide_bullets": [
            "ทบทวนเป้าหมายหลักของบทเรียน",
            "นำแนวคิดไปปรับใช้ในการทำงาน",
            "วัดผลและพัฒนาอย่างต่อเนื่อง"
        ],
        "highlight_box": "กระชับ ตรงประเด็น สู่ผลลัพธ์ที่จับต้องได้",
        "audio_script_th": format_natural_spoken_thai(
            "และนี่คือสรุปประเด็นหลักครับ หวังว่าจะนำแนวคิดนี้ไปปรับใช้เพื่อสร้างผลลัพธ์ที่ดีขึ้นนะครับ"
        )
    })
    
    return scenes
