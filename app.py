import os
import glob
import json
import streamlit as st

from config import BRAND_CONFIG, TTS_CONFIG, CORPORATE_GLOSSARY, REVIEW_VIDEOS_DIR, SCORM_DIR, OUTPUT_DIR, TEMP_DIR, GEMINI_API_KEY

from src.ingestion import chunk_content_into_modules, extract_text_from_file
from src.ai_pedagogy import ai_synthesize_ebook_syllabus, ai_generate_notebooklm_style_scenes
from src.notebooklm_audio import generate_notebooklm_podcast_dialogue, synthesize_podcast_audio_track
from src.gemini_notebooklm_api import generate_notebooklm_podcast_with_gemini_api
from src.scriptwriter import generate_minimal_slides_from_text, apply_corporate_glossary
from src.quiz_generator import generate_pre_test, generate_post_test, generate_knowledge_check
from src.tts_engine import generate_thai_speech_sync, get_audio_duration, generate_srt_subtitles
from src.slide_motion import draw_minimal_slide, render_scene_video, concat_scene_videos
from src.scorm_packager import create_scorm_package
import importlib
import src.pdf_translator
importlib.reload(src.pdf_translator)
from src.pdf_translator import translate_pdf_layout


st.set_page_config(

    page_title="eBook to e-Learning Studio (Google Gemini / NotebookLM)",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# High-Contrast UI Styling
st.markdown("""
<style>
    .stApp { background-color: #F8FAFC !important; color: #0F172A !important; }
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: #FFFFFF !important; color: #0F172A !important; border: 2px solid #94A3B8 !important; border-radius: 8px !important; font-weight: 600 !important;
    }
    .stExpander { background-color: #FFFFFF !important; border: 2px solid #CBD5E1 !important; border-radius: 10px !important; margin-bottom: 12px !important; }
    .stExpander summary { color: #0F172A !important; font-weight: 700 !important; font-size: 1.1rem !important; }
    .main-header { font-size: 2.3rem; font-weight: 800; color: #0284C7; margin-bottom: 0.2rem; }
    .sub-header { font-size: 1.1rem; font-weight: 600; color: #334155; margin-bottom: 1.5rem; }
    .stButton>button { background-color: #0284C7 !important; color: #FFFFFF !important; font-weight: 700 !important; font-size: 1.05rem !important; border-radius: 8px !important; border: none !important; }
    .stButton>button:hover { background-color: #0369A1 !important; }
    .stAlert { background-color: #E0F2FE !important; color: #0369A1 !important; border: 1px solid #7DD3FC !important; border-radius: 8px !important; font-weight: 600 !important; }
</style>
""", unsafe_allow_html=True)

# State Init
if "project_name" not in st.session_state:
    st.session_state.project_name = "Customer_Service_Pocketbook"
if "ebook_text" not in st.session_state:
    st.session_state.ebook_text = ""
if "modules" not in st.session_state:
    st.session_state.modules = []
if "module_scenes" not in st.session_state:
    st.session_state.module_scenes = {}
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = {"pre_test": [], "post_test": [], "knowledge_check": {}}
if "approved_modules" not in st.session_state:
    st.session_state.approved_modules = set()
if "gemini_api_key" not in st.session_state:
    st.session_state.gemini_api_key = GEMINI_API_KEY


# Header
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown('<div class="main-header">🎓 eBook to e-Learning Studio (Google Gemini API Powered)</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">รองรับการเชื่อมต่อ Google Gemini API (ตัวขับเคลื่อน NotebookLM) โดยตรง</div>', unsafe_allow_html=True)
with col_h2:
    st.session_state.project_name = st.text_input("📁 ชื่อโครงการ", st.session_state.project_name)

st.markdown("---")

# Sidebar - Gemini API Key & Audio Config
st.sidebar.markdown("## 🔑 ตั้งค่า Google Gemini API")
st.session_state.gemini_api_key = st.sidebar.text_input(
    "Google Gemini API Key (ใส่เพื่อดึง AI NotebookLM โดยตรง)",
    st.session_state.gemini_api_key,
    type="password",
    help="หากไม่ใส่ระบบจะใช้มอดูลสังเคราะห์พอดแคสต์ภาษาไทยอัตโนมัติ"
)

st.sidebar.markdown("---")
st.sidebar.markdown("## ⚙️ ตั้งค่าสไลด์ & เสียงพากย์")
st.session_state.audio_mode = st.sidebar.radio(
    "รูปแบบเสียงพากย์ (Audio Style)",
    ["NotebookLM Podcast (2 Co-Hosts ชาย-หญิง)", "เสียงพากย์ผู้สอนคนเดียว (Single Presenter)"]
)

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "1. 🧠 AI วิเคราะห์เนื้อหาแบบ NotebookLM",
    "2. 🎨 ภาพสไลด์สวยงาม & เสียงพากย์ Podcast",
    "3. 📝 แบบทดสอบ Quiz",
    "4. 🎬 ตรวจวิดีโอ (Review)",
    "5. ⬇️ ศูนย์ดาวน์โหลด",
    "6. 🌐 แปล PDF ภาษาอังกฤษ -> ไทย"
])


# TAB 1: Ingestion
with tab1:
    st.markdown("### Step 1: โหลด eBook & ให้ AI อ่านวิเคราะห์ภาพรวมแบบ NotebookLM")
    col_u1, col_u2 = st.columns([1, 1])
    with col_u1:
        up_file = st.file_uploader("อัปโหลดไฟล์ eBook (PDF / TXT / Markdown)", type=["pdf", "txt", "md"])
        if up_file:
            temp_p = os.path.join(TEMP_DIR, up_file.name)
            with open(temp_p, "wb") as f:
                f.write(up_file.getbuffer())
            st.session_state.ebook_text = extract_text_from_file(temp_p)
            st.success(f"สกัดข้อความหนังสือทั้งหมดสำเร็จ! ({len(st.session_state.ebook_text)} ตัวอักษร)")
            
    with col_u2:
        num_mods = st.slider("จำนวนบทเรียนย่อยที่ต้องการจัดเรียบเรียงใหม่", 2, 6, 3)

    st.session_state.ebook_text = st.text_area("เนื้อหาหนังสือทั้งหมด (Full eBook Content)", st.session_state.ebook_text or """WHY CUSTOMER SERVICE MATTERS

Customer Contact & Everyone's Role
Customer service matters because everybody in every organization either helps customers directly or helps colleagues (internal customers) who serve the paying customer. Whether you work in commercial companies, public sector utilities, or government departments, everyone has customers.

Your Personal Needs vs Organisation Needs
Delivering good customer service gives you personal job satisfaction, reduces rework, and gives you more control of your workload. For the organization, great service creates a sustainable competitive advantage, increases profitability, and builds a stress-free work environment.""", height=220)
    
    if st.button("🧠 รัน AI วิเคราะห์ภาพรวมหนังสือ & จัดเรียบเรียงหลักสูตรใหม่ (NotebookLM AI Synthesizer)", type="primary"):
        with st.spinner("AI กำลังอ่านหนังสือทั้งเล่ม คัดแยกข้อความขยะ และสังเคราะห์โครงสร้างบทเรียนใหม่..."):
            synth_modules = ai_synthesize_ebook_syllabus(st.session_state.ebook_text, target_modules_count=num_mods)
            st.session_state.modules = synth_modules
            st.session_state.module_scenes = {}
            st.session_state.quiz_data["knowledge_check"] = {}
            
            for m in synth_modules:
                m_id = m["module_id"]
                scenes = ai_generate_notebooklm_style_scenes(m["title"], m["text"])
                st.session_state.module_scenes[m_id] = scenes
                st.session_state.quiz_data["knowledge_check"][m_id] = generate_knowledge_check(m["title"], m["text"])
                
            st.session_state.quiz_data["pre_test"] = generate_pre_test(st.session_state.ebook_text)
            st.session_state.quiz_data["post_test"] = generate_post_test(st.session_state.ebook_text)
            st.balloons()
            st.success(f"AI วิเคราะห์ภาพรวมสำเร็จ! สังเคราะห์ได้ {len(synth_modules)} บทเรียนย่อยเรียบร้อยแล้วครับ")

# TAB 2: Beautiful Slides & Podcast Voiceover
with tab2:
    st.markdown("### Step 2: ภาพสไลด์สวยงาม & เสียงพากย์ NotebookLM Podcast")
    if st.session_state.modules:
        mod_titles = [f"[{m['module_id']}] {m['title']}" for m in st.session_state.modules]
        sel_idx = st.selectbox("เลือกบทเรียนย่อย", range(len(mod_titles)), format_func=lambda i: mod_titles[i])
        selected_mod = st.session_state.modules[sel_idx]
        mod_id = selected_mod["module_id"]
        scenes = st.session_state.module_scenes.get(mod_id, [])
        
        st.markdown(f"#### 🎨 ภาพสไลด์และเสียงพากย์บทเรียน: **{selected_mod['title']}**")
        
        for idx, sc in enumerate(scenes):
            with st.expander(f"📌 ฉากที่ {sc['scene_id']}: {sc['slide_title']}", expanded=True):
                col_s1, col_s2 = st.columns([1, 1])
                with col_s1:
                    sc['slide_title'] = st.text_input("หัวข้อหลัก (Slide Title)", sc['slide_title'], key=f"t_{mod_id}_{idx}")
                    sc['subtitle'] = st.text_input("หัวข้อย่อย (Subtitle)", sc['subtitle'], key=f"sub_{mod_id}_{idx}")
                    sc['highlight_box'] = st.text_area("Highlight Card", sc['highlight_box'], key=f"hl_{mod_id}_{idx}")
                    b_str = "\n".join(sc['slide_bullets'])
                    new_b = st.text_area("Bullet Points", b_str, key=f"bul_{mod_id}_{idx}")
                    sc['slide_bullets'] = [b.strip() for b in new_b.split("\n") if b.strip()]
                with col_s2:
                    sc['audio_script_th'] = st.text_area("สคริปต์พูดสอนภาษาไทย", sc['audio_script_th'], height=150, key=f"aud_{mod_id}_{idx}")
                    col_p1, col_p2 = st.columns([1, 1])
                    with col_p1:
                        if st.button(f"🎨 พรีวิวสไลด์สวยงาม (1080p)", key=f"img_{mod_id}_{idx}"):
                            ip = os.path.join(TEMP_DIR, f"prev_{mod_id}_{idx}.png")
                            draw_minimal_slide(sc, ip)
                            st.image(ip, caption="ภาพสไลด์ 1920x1080 Glassmorphism", use_column_width=True)
                    with col_p2:
                        if st.button(f"🎙️ พรีวิวเสียงพากย์ Podcast", key=f"aud_btn_{mod_id}_{idx}"):
                            ap = os.path.join(TEMP_DIR, f"prev_{mod_id}_{idx}.mp3")
                            
                            # Check if Gemini API Key is available
                            dialogue = None
                            if st.session_state.gemini_api_key:
                                dialogue = generate_notebooklm_podcast_with_gemini_api(sc['audio_script_th'], st.session_state.gemini_api_key)
                                
                            if not dialogue:
                                dialogue = generate_notebooklm_podcast_dialogue(sc['slide_title'], sc['audio_script_th'])
                                
                            synthesize_podcast_audio_track(dialogue, ap)
                            st.audio(ap)

        if st.button("💾 บันทึกสไลด์ & เรนเดอร์วิดีโอ MP4 H.264 (NotebookLM Podcast)", type="primary"):
            with st.spinner("กำลังตัดต่อวิดีโอสไลด์สวยงาม และสังเคราะห์เสียงพากย์คู่ NotebookLM Podcast..."):
                m_dir = os.path.join(TEMP_DIR, mod_id)
                os.makedirs(m_dir, exist_ok=True)
                clips = []
                
                for sc in scenes:
                    ip = os.path.join(m_dir, f"slide_{sc['scene_id']:02d}.png")
                    ap = os.path.join(m_dir, f"audio_{sc['scene_id']:02d}.mp3")
                    cp = os.path.join(m_dir, f"clip_{sc['scene_id']:02d}.mp4")
                    
                    draw_minimal_slide(sc, ip)
                    
                    dialogue = None
                    if st.session_state.gemini_api_key:
                        dialogue = generate_notebooklm_podcast_with_gemini_api(sc['audio_script_th'], st.session_state.gemini_api_key)
                        
                    if not dialogue:
                        dialogue = generate_notebooklm_podcast_dialogue(sc['slide_title'], sc['audio_script_th'])
                        
                    synthesize_podcast_audio_track(dialogue, ap)
                    sc["audio_duration"] = get_audio_duration(ap)
                    render_scene_video(ip, ap, cp)
                    clips.append(cp)
                    
                rv_path = os.path.join(REVIEW_VIDEOS_DIR, f"{st.session_state.project_name}_{mod_id}_FOR_REVIEW.mp4")
                rv_srt = os.path.join(REVIEW_VIDEOS_DIR, f"{st.session_state.project_name}_{mod_id}_Subtitles.srt")
                concat_scene_videos(clips, rv_path)
                generate_srt_subtitles(scenes, rv_srt)
                
                st.balloons()
                st.success("เรนเดอร์วิดีโอสไลด์สวยงาม + เสียงพากย์ Podcast สำเร็จแล้ว! ไปที่ Tab 4 เพื่อดูวิดีโอได้เลยครับ")
    else:
        st.info("กรุณารัน AI วิเคราะห์เนื้อหาใน Tab 1 ก่อนครับ")

# TAB 3: Quizzes
with tab3:
    st.markdown("### Step 3: จัดการแบบทดสอบ Quiz")
    q1, q2, q3 = st.tabs(["Pre-test (5 ข้อ)", "Post-test (5 ข้อ)", "Knowledge Check ท้ายบท"])
    with q1:
        for idx, q in enumerate(st.session_state.quiz_data.get("pre_test", [])):
            st.markdown(f"**ข้อ {idx+1}: {q['question']}**")
    with q2:
        for idx, q in enumerate(st.session_state.quiz_data.get("post_test", [])):
            st.markdown(f"**ข้อ {idx+1}: {q['question']}**")
    with q3:
        for m_id, kc_list in st.session_state.quiz_data.get("knowledge_check", {}).items():
            st.markdown(f"##### บทเรียน [{m_id}]")
            for idx, q in enumerate(kc_list):
                st.caption(f"• **{q['question']}** ({q.get('explanation','')})")

# TAB 4: Video Review
with tab4:
    st.markdown("### Step 4: 🎬 ตรวจวิดีโอภาพสไลด์สวยงาม & เสียงพากย์ Podcast")
    r_files = glob.glob(os.path.join(REVIEW_VIDEOS_DIR, "*.mp4"))
    if r_files:
        sel_v = st.selectbox("เลือกวิดีโอ MP4 H.264", r_files, format_func=lambda p: os.path.basename(p))
        st.video(sel_v)
        if st.button("✅ อนุมัติวิดีโอนี้ (Approve for SCORM)", type="primary"):
            st.session_state.approved_modules.add(sel_v)
            st.success("อนุมัติเรียบร้อย!")
    else:
        st.warning("ยังไม่มีวิดีโอที่เรนเดอร์สำเร็จ กรุณากดเรนเดอร์ใน Tab 2 ก่อนครับ")

# TAB 5: Download Center
with tab5:
    st.markdown("### Step 5: ศูนย์ดาวน์โหลดสื่อการเรียนรู้")
    if st.button("🔨 รวมแพ็กเกจ SCORM 1.2 ZIP ล่าสุด"):
        os.makedirs(SCORM_DIR, exist_ok=True)
        for m in st.session_state.modules:
            m_id = m["module_id"]
            title = m["title"]
            vp = os.path.join(REVIEW_VIDEOS_DIR, f"{st.session_state.project_name}_{m_id}_FOR_REVIEW.mp4")
            sp = os.path.join(REVIEW_VIDEOS_DIR, f"{st.session_state.project_name}_{m_id}_Subtitles.srt")
            zp = os.path.join(SCORM_DIR, f"{st.session_state.project_name}_{m_id}_SCORM.zip")
            create_scorm_package(f"{st.session_state.project_name} - {title}", vp, sp, zp, quiz_data=st.session_state.quiz_data)
        st.success("สร้างไฟล์ SCORM สำเร็จ!")
        
    s_files = glob.glob(os.path.join(SCORM_DIR, "*.zip"))
    for sf in s_files:
        fn = os.path.basename(sf)
        with open(sf, "rb") as f:
            st.download_button(f"⬇️ ดาวน์โหลด {fn}", f, file_name=fn, mime="application/zip", key=f"dl_{fn}")

# TAB 6: PDF Layout Translator
with tab6:
    st.markdown("### Step 6: 🌐 แปลไฟล์ PDF ภาษาอังกฤษเป็นไทย โดยคงโครงสร้างการจัดหน้า (Layout)")
    st.markdown("ระบบจะดึงเนื้อหาจาก PDF ทีละหน้า แปลด้วย Gemini API เป็นกลุ่มข้อความ และใช้ฟอนต์ **Sarabun** วาดคำแปลลงบนโครงสร้างเดิม")
    
    col_pdf1, col_pdf2 = st.columns([1, 1])
    with col_pdf1:
        pdf_uploader = st.file_uploader("อัปโหลดไฟล์ PDF ภาษาอังกฤษ", type=["pdf"], key="pdf_translator_uploader")
        
        # Verify API Key exists
        api_key = st.session_state.get("gemini_api_key", "")
        
        if pdf_uploader:
            if not api_key:
                st.warning("⚠️ กรุณากรอก Google Gemini API Key ในแถบด้านซ้าย (Sidebar) ก่อนเพื่อเริ่มทำการแปล")
            else:
                if st.button("🚀 เริ่มการแปลภาษาและคงดีไซน์เดิม", type="primary", key="btn_run_pdf_translation"):
                    # Create paths
                    temp_pdf_in = os.path.join(TEMP_DIR, f"original_{pdf_uploader.name}")
                    temp_pdf_out = os.path.join(OUTPUT_DIR, f"translated_{pdf_uploader.name}")
                    
                    with open(temp_pdf_in, "wb") as f:
                        f.write(pdf_uploader.getbuffer())
                    
                    status_placeholder = st.empty()
                    
                    def update_status(text):
                        status_placeholder.info(text)
                        
                    with st.spinner("AI กำลังแปลและจัดหน้า PDF..."):
                        try:
                            # Run translation
                            translate_pdf_layout(temp_pdf_in, temp_pdf_out, api_key, status_callback=update_status)
                            status_placeholder.success("🎉 การแปลเสร็จสมบูรณ์เรียบร้อยแล้ว!")
                            st.session_state.translated_pdf_path = temp_pdf_out
                        except Exception as e:
                            status_placeholder.error(f"❌ เกิดข้อผิดพลาดระหว่างแปลภาษา: {str(e)}")
                            
    with col_pdf2:
        if "translated_pdf_path" in st.session_state and os.path.exists(st.session_state.translated_pdf_path):
            st.markdown("#### ⬇️ ดาวน์โหลดและพรีวิวเอกสารที่แปลแล้ว")
            
            translated_path = st.session_state.translated_pdf_path
            filename = os.path.basename(translated_path)
            
            # Download Button
            with open(translated_path, "rb") as f:
                st.download_button(
                    label=f"⬇️ ดาวน์โหลด PDF แปลภาษา: {filename}",
                    data=f,
                    file_name=filename,
                    mime="application/pdf"
                )
            
            st.markdown("---")
            st.markdown("##### 👁️ พรีวิวหน้าเอกสารแปลล่าสุด")
            
            # Show preview using PyMuPDF to render pages as PNG
            try:
                import fitz
                doc = fitz.open(translated_path)
                page_count = len(doc)
                
                selected_page = st.number_input("เลือกหน้าที่ต้องการพรีวิว", min_value=1, max_value=page_count, value=1)
                
                # Render page
                page = doc[selected_page - 1]
                pix = page.get_pixmap(dpi=150)
                preview_png = os.path.join(TEMP_DIR, f"preview_page_{selected_page}.png")
                pix.save(preview_png)
                doc.close()
                
                st.image(preview_png, caption=f"หน้า {selected_page} จากทั้งหมด {page_count} หน้า", use_column_width=True)
            except Exception as e:
                st.warning(f"ไม่สามารถพรีวิวหน้าเอกสารได้: {str(e)}")
        else:
            st.info("อัปโหลดไฟล์ PDF และกดปุ่มแปลภาษาเพื่อแสดงพรีวิวและดาวน์โหลด")

