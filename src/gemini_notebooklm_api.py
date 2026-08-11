import os
import json
import requests
from config import CORPORATE_GLOSSARY

def get_active_gemini_api_key() -> str:
    """
    Safely retrieves Gemini API key from config module or environment variable.
    """
    try:
        from config import GEMINI_API_KEY
        if GEMINI_API_KEY:
            return GEMINI_API_KEY
    except Exception:
        pass
    return os.environ.get("GEMINI_API_KEY", "")

def generate_notebooklm_podcast_with_gemini_api(ebook_text: str, api_key: str = None) -> list[dict]:
    """
    Direct Integration with Google Gemini 3.5 Flash API (Powering Google NotebookLM).
    Passes full eBook text to Gemini 3.5 model to generate a multi-speaker NotebookLM Audio Overview podcast script.
    """
    if not api_key:
        api_key = get_active_gemini_api_key()
        
    if not api_key:
        return None

    # Google Gemini 3.5 Flash REST API endpoint
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={api_key}"
    
    prompt = f"""
    คุณคือ AI Co-Host ประจำ Google NotebookLM 
    จงอ่านเนื้อหาหนังสือภาษาอังกฤษต่อไปนี้ และสังเคราะห์บทสนทนาพอดแคสต์ (Audio Overview) ภาษาไทยสไตล์ NotebookLM 
    ที่มีผู้ดำเนินรายการ 2 คน (Host 1: ชาย - คุณนิวัฒน์, Host 2: หญิง - คุณเปรมวดี)
    
    ข้อกำหนดสำคัญ:
    1. พูดสนทนาภาษาไทยเป็นธรรมชาติ กระชับ ไม่เยิ่นเย้อ มีการพูดรับส่งและต่อบทกันอย่างน่าติดตาม
    2. ส่งกลับเป็น JSON Array ในรูปแบบต่อไปนี้เท่านั้น (ไม่มีข้อความอื่นนอกเหนือจาก JSON):
    [
      {{"speaker": "Host 1 (ชาย)", "voice": "th-TH-NiwatNeural", "text": "ข้อความเปิดรายการ..."}},
      {{"speaker": "Host 2 (หญิง)", "voice": "th-TH-PremwadeeNeural", "text": "ข้อความตอบรับและเจาะลึก..."}}
    ]

    เนื้อหาหนังสือ:
    {ebook_text[:3500]}
    """
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.7
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            res_data = response.json()
            text_response = res_data["candidates"][0]["content"]["parts"][0]["text"]
            dialogue_json = json.loads(text_response)
            return dialogue_json
        else:
            print(f"Gemini API Error Status: {response.status_code} - {response.text[:200]}")
    except Exception as e:
        print(f"Gemini API Call Exception: {e}")
        
    return None
