import html
import streamlit as st
import json
import os
import requests
import re
from bs4 import BeautifulSoup

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# File paths
COURSES_PATH = os.path.join(ASSETS_DIR, "all_courses.json")
TITLES_PATH = os.path.join(ASSETS_DIR, "translated_titles.json")
META_PATH = os.path.join(ASSETS_DIR, "translated_meta.json")
CACHE_PATH = os.path.join(ASSETS_DIR, "course_details_cache.json")

# Ensure assets dir exists
os.makedirs(ASSETS_DIR, exist_ok=True)

# ----------------------------------------------------
# 1. Base Data Loading (Cached)
# ----------------------------------------------------
@st.cache_data(ttl="1h")
@st.cache_data
def load_matched_courses():
    matched_path = os.path.join(ASSETS_DIR, "matched_courses.json")
    if os.path.exists(matched_path):
        with open(matched_path, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def load_base_data():
    courses = []
    if os.path.exists(COURSES_PATH):
        with open(COURSES_PATH, "r", encoding="utf-8") as f:
            courses = json.load(f)
            
    titles_map = {}
    if os.path.exists(TITLES_PATH):
        with open(TITLES_PATH, "r", encoding="utf-8") as f:
            titles_map = json.load(f)
            
    meta_map = {"cats": {}, "tags": {}}
    if os.path.exists(META_PATH):
        with open(META_PATH, "r", encoding="utf-8") as f:
            meta_map = json.load(f)
            
    # Apply deterministic diverse mix round-robin sorting across all categories
    from collections import defaultdict
    cat_groups = defaultdict(list)
    for c in courses:
        cat = c.get("cats", [""])[0] if c.get("cats") else ""
        parent = PARENT_CATS_MAP.get(cat, "ทั่วไปและอื่นๆ (General & Others)")
        cat_groups[parent].append(c)

    diverse_courses = []
    category_keys = list(cat_groups.keys())
    max_len = max(len(v) for v in cat_groups.values()) if cat_groups else 0

    for i in range(max_len):
        for parent_key in category_keys:
            if i < len(cat_groups[parent_key]):
                diverse_courses.append(cat_groups[parent_key][i])

    if len(diverse_courses) == len(courses):
        courses = diverse_courses

    return courses, titles_map, meta_map

# ----------------------------------------------------
# 1.6. Skill Tag to Parent Skill Tag Map (10 Parent Skill Groups)
# ----------------------------------------------------
PARENT_TAGS_MAP = {
    # 1. เทคโนโลยี ข้อมูล และซอฟต์แวร์ (Technology, Data & Software)
    "AI Basics": "เทคโนโลยี ข้อมูล และซอฟต์แวร์ (Technology, Data & Software)",
    "Coding Awareness": "เทคโนโลยี ข้อมูล และซอฟต์แวร์ (Technology, Data & Software)",
    "Cybersecurity Awareness": "เทคโนโลยี ข้อมูล และซอฟต์แวร์ (Technology, Data & Software)",
    "Data Analysis": "เทคโนโลยี ข้อมูล และซอฟต์แวร์ (Technology, Data & Software)",
    "Data Literacy": "เทคโนโลยี ข้อมูล และซอฟต์แวร์ (Technology, Data & Software)",
    "Data-Driven Decision-Making": "เทคโนโลยี ข้อมูล และซอฟต์แวร์ (Technology, Data & Software)",
    "Digital Literacy": "เทคโนโลยี ข้อมูล และซอฟต์แวร์ (Technology, Data & Software)",
    "Excel Basics": "เทคโนโลยี ข้อมูล และซอฟต์แวร์ (Technology, Data & Software)",
    "Google Docs Basics": "เทคโนโลยี ข้อมูล และซอฟต์แวร์ (Technology, Data & Software)",
    "Google Sheets Basics": "เทคโนโลยี ข้อมูล และซอฟต์แวร์ (Technology, Data & Software)",
    "Google Slides Basics": "เทคโนโลยี ข้อมูล และซอฟต์แวร์ (Technology, Data & Software)",
    "PowerPoint Basics": "เทคโนโลยี ข้อมูล และซอฟต์แวร์ (Technology, Data & Software)",
    "Word Basics": "เทคโนโลยี ข้อมูล และซอฟต์แวร์ (Technology, Data & Software)",
    "Prompt Engineering": "เทคโนโลยี ข้อมูล และซอฟต์แวร์ (Technology, Data & Software)",
    "Researching": "เทคโนโลยี ข้อมูล และซอฟต์แวร์ (Technology, Data & Software)",
    "Information Literacy": "เทคโนโลยี ข้อมูล และซอฟต์แวร์ (Technology, Data & Software)",
    
    # 2. การสื่อสารและการทำงานร่วมกัน (Communication & Collaboration)
    "Active Listening": "การสื่อสารและการทำงานร่วมกัน (Communication & Collaboration)",
    "Assertiveness": "การสื่อสารและการทำงานร่วมกัน (Communication & Collaboration)",
    "Collaboration": "การสื่อสารและการทำงานร่วมกัน (Communication & Collaboration)",
    "Effective Communication": "การสื่อสารและการทำงานร่วมกัน (Communication & Collaboration)",
    "Empathy": "การสื่อสารและการทำงานร่วมกัน (Communication & Collaboration)",
    "Giving Feedback": "การสื่อสารและการทำงานร่วมกัน (Communication & Collaboration)",
    "Networking": "การสื่อสารและการทำงานร่วมกัน (Communication & Collaboration)",
    "Non-Verbal Communication": "การสื่อสารและการทำงานร่วมกัน (Communication & Collaboration)",
    "Persuasion": "การสื่อสารและการทำงานร่วมกัน (Communication & Collaboration)",
    "Rapport Building": "การสื่อสารและการทำงานร่วมกัน (Communication & Collaboration)",
    "Relationship Management": "การสื่อสารและการทำงานร่วมกัน (Communication & Collaboration)",
    "Storytelling": "การสื่อสารและการทำงานร่วมกัน (Communication & Collaboration)",
    "Written Communication": "การสื่อสารและการทำงานร่วมกัน (Communication & Collaboration)",
    "Presentation Skills": "การสื่อสารและการทำงานร่วมกัน (Communication & Collaboration)",
    
    # 3. การเป็นผู้นำและการจัดการบุคคล (Leadership & People Management)
    "Accountability": "การเป็นผู้นำและการจัดการบุคคล (Leadership & People Management)",
    "Change Management": "การเป็นผู้นำและการจัดการบุคคล (Leadership & People Management)",
    "Coaching": "การเป็นผู้นำและการจัดการบุคคล (Leadership & People Management)",
    "Conflict Management": "การเป็นผู้นำและการจัดการบุคคล (Leadership & People Management)",
    "Inspiring Others": "การเป็นผู้นำและการจัดการบุคคล (Leadership & People Management)",
    "Leadership": "การเป็นผู้นำและการจัดการบุคคล (Leadership & People Management)",
    "Mentoring": "การเป็นผู้นำและการจัดการบุคคล (Leadership & People Management)",
    "Motivation": "การเป็นผู้นำและการจัดการบุคคล (Leadership & People Management)",
    "Performance Management": "การเป็นผู้นำและการจัดการบุคคล (Leadership & People Management)",
    "Team Building": "การเป็นผู้นำและการจัดการบุคคล (Leadership & People Management)",
    
    # 4. การคิดเชิงวิเคราะห์และการแก้ปัญหา (Analytical & Problem Solving)
    "Analytical Thinking": "การคิดเชิงวิเคราะห์และการแก้ปัญหา (Analytical & Problem Solving)",
    "Creative Thinking": "การคิดเชิงวิเคราะห์และการแก้ปัญหา (Analytical & Problem Solving)",
    "Critical Thinking": "การคิดเชิงวิเคราะห์และการแก้ปัญหา (Analytical & Problem Solving)",
    "Decision-Making": "การคิดเชิงวิเคราะห์และการแก้ปัญหา (Analytical & Problem Solving)",
    "Innovation": "การคิดเชิงวิเคราะห์และการแก้ปัญหา (Analytical & Problem Solving)",
    "Logical Thinking": "การคิดเชิงวิเคราะห์และการแก้ปัญหา (Analytical & Problem Solving)",
    "Problem-Solving": "การคิดเชิงวิเคราะห์และการแก้ปัญหา (Analytical & Problem Solving)",
    "Process Improvement": "การคิดเชิงวิเคราะห์และการแก้ปัญหา (Analytical & Problem Solving)",
    "Strategic Thinking": "การคิดเชิงวิเคราะห์และการแก้ปัญหา (Analytical & Problem Solving)",
    
    # 5. การพัฒนาและจัดการตนเอง (Personal Growth & Self-Management)
    "Adaptability": "การพัฒนาและจัดการตนเอง (Personal Growth & Self-Management)",
    "Attention to Detail": "การพัฒนาและจัดการตนเอง (Personal Growth & Self-Management)",
    "Flexible Thinking": "การพัฒนาและจัดการตนเอง (Personal Growth & Self-Management)",
    "Goal Orientation": "การพัฒนาและจัดการตนเอง (Personal Growth & Self-Management)",
    "Organizational Skills": "การพัฒนาและจัดการตนเอง (Personal Growth & Self-Management)",
    "Prioritization": "การพัฒนาและจัดการตนเอง (Personal Growth & Self-Management)",
    "Proactivity": "การพัฒนาและจัดการตนเอง (Personal Growth & Self-Management)",
    "Productivity": "การพัฒนาและจัดการตนเอง (Personal Growth & Self-Management)",
    "Resilience": "การพัฒนาและจัดการตนเอง (Personal Growth & Self-Management)",
    "Self-Awareness": "การพัฒนาและจัดการตนเอง (Personal Growth & Self-Management)",
    "Self-Confidence": "การพัฒนาและจัดการตนเอง (Personal Growth & Self-Management)",
    "Self-Management": "การพัฒนาและจัดการตนเอง (Personal Growth & Self-Management)",
    "Time Management": "การพัฒนาและจัดการตนเอง (Personal Growth & Self-Management)",
    "Well-being": "การพัฒนาและจัดการตนเอง (Personal Growth & Self-Management)",
    "Learning Design": "การพัฒนาและจัดการตนเอง (Personal Growth & Self-Management)",
    "Emotional Intelligence": "การพัฒนาและจัดการตนเอง (Personal Growth & Self-Management)",
    "Positive Attitude": "การพัฒนาและจัดการตนเอง (Personal Growth & Self-Management)",
    "Responsibility": "การพัฒนาและจัดการตนเอง (Personal Growth & Self-Management)",
    
    # 6. การบริหารธุรกิจและการปฏิบัติการ (Business & Operations)
    "Accounting": "การบริหารธุรกิจและการปฏิบัติการ (Business & Operations)",
    "Budgeting": "การบริหารธุรกิจและการปฏิบัติการ (Business & Operations)",
    "Business Ethics": "การบริหารธุรกิจและการปฏิบัติการ (Business & Operations)",
    "Commercial Awareness": "การบริหารธุรกิจและการปฏิบัติการ (Business & Operations)",
    "Entrepreneurship": "การบริหารธุรกิจและการปฏิบัติการ (Business & Operations)",
    "Financial Management": "การบริหารธุรกิจและการปฏิบัติการ (Business & Operations)",
    "Product Management": "การบริหารธุรกิจและการปฏิบัติการ (Business & Operations)",
    "Project Management": "การบริหารธุรกิจและการปฏิบัติการ (Business & Operations)",
    "Quality Management": "การบริหารธุรกิจและการปฏิบัติการ (Business & Operations)",
    "Risk Management": "การบริหารธุรกิจและการปฏิบัติการ (Business & Operations)",
    "Sustainability Management": "การบริหารธุรกิจและการปฏิบัติการ (Business & Operations)",
    "eCommerce": "การบริหารธุรกิจและการปฏิบัติการ (Business & Operations)",
    "Remote Working": "การบริหารธุรกิจและการปฏิบัติการ (Business & Operations)",
    
    # 7. การขาย การตลาด และบริการ (Sales, Marketing & Customer Service)
    "Branding": "การขาย การตลาด และบริการ (Sales, Marketing & Customer Service)",
    "Campaign Planning": "การขาย การตลาด และบริการ (Sales, Marketing & Customer Service)",
    "Content Management": "การขาย การตลาด และบริการ (Sales, Marketing & Customer Service)",
    "Copywriting": "การขาย การตลาด และบริการ (Sales, Marketing & Customer Service)",
    "Customer Service": "การขาย การตลาด และบริการ (Sales, Marketing & Customer Service)",
    "Digital Marketing": "การขาย การตลาด และบริการ (Sales, Marketing & Customer Service)",
    "Market Research": "การขาย การตลาด และบริการ (Sales, Marketing & Customer Service)",
    "Negotiation": "การขาย การตลาด และบริการ (Sales, Marketing & Customer Service)",
    "PPC (Pay-Per-Click)": "การขาย การตลาด และบริการ (Sales, Marketing & Customer Service)",
    "Prospecting": "การขาย การตลาด และบริการ (Sales, Marketing & Customer Service)",
    "SEO": "การขาย การตลาด และบริการ (Sales, Marketing & Customer Service)",
    "Sales": "การขาย การตลาด และบริการ (Sales, Marketing & Customer Service)",
    
    # 8. การปฏิบัติตามกฎระเบียบและความปลอดภัย (Compliance & Safety)
    "Accident Prevention": "การปฏิบัติตามกฎระเบียบและความปลอดภัย (Compliance & Safety)",
    "Compliance Awareness": "การปฏิบัติตามกฎระเบียบและความปลอดภัย (Compliance & Safety)",
    "Data Protection": "การปฏิบัติตามกฎระเบียบและความปลอดภัย (Compliance & Safety)",
    "Safeguarding Awareness": "การปฏิบัติตามกฎระเบียบและความปลอดภัย (Compliance & Safety)",
    "Safety": "การปฏิบัติตามกฎระเบียบและความปลอดภัย (Compliance & Safety)",
    
    # 9. การออกแบบและประสบการณ์ผู้ใช้ (Design & UX)
    "UI/UX Design": "การออกแบบและประสบการณ์ผู้ใช้ (Design & UX)",
    "User Experience": "การออกแบบและประสบการณ์ผู้ใช้ (Design & UX)",
    
    # 10. ความเข้าใจความหลากหลายและวัฒนธรรม (Culture & Diversity)
    "Cultural Awareness": "ความเข้าใจความหลากหลายและวัฒนธรรม (Culture & Diversity)",
    
}
# Load static base data
PARENT_CATS_MAP = {
    # 1. การพัฒนาตนเองและสุขภาวะ (Personal Development & Well-being)
    "Personal Development": "การพัฒนาตนเองและสุขภาวะ (Personal Development & Well-being)",
    "Life Skills 101": "การพัฒนาตนเองและสุขภาวะ (Personal Development & Well-being)",
    "Well-Being Training Essentials": "การพัฒนาตนเองและสุขภาวะ (Personal Development & Well-being)",
    "Mental Health Awareness": "การพัฒนาตนเองและสุขภาวะ (Personal Development & Well-being)",
    "Mindfulness": "การพัฒนาตนเองและสุขภาวะ (Personal Development & Well-being)",
    "Mastering Happiness": "การพัฒนาตนเองและสุขภาวะ (Personal Development & Well-being)",
    "Emotional Intelligence": "การพัฒนาตนเองและสุขภาวะ (Personal Development & Well-being)",
    "Career Management": "การพัฒนาตนเองและสุขภาวะ (Personal Development & Well-being)",
    "Learning Applied": "การพัฒนาตนเองและสุขภาวะ (Personal Development & Well-being)",
    "Learning Essentials": "การพัฒนาตนเองและสุขภาวะ (Personal Development & Well-being)",
    
    # 2. การเป็นผู้นำและการจัดการ (Leadership & Management)
    "Adaptive Leadership": "การเป็นผู้นำและการจัดการ (Leadership & Management)",
    "Leadership": "การเป็นผู้นำและการจัดการ (Leadership & Management)",
    "Leadership Tool Kit": "การเป็นผู้นำและการจัดการ (Leadership & Management)",
    "Leadership Training Essentials": "การเป็นผู้นำและการจัดการ (Leadership & Management)",
    "Practicing Leadership": "การเป็นผู้นำและการจัดการ (Leadership & Management)",
    "The Leadership Role Model": "การเป็นผู้นำและการจัดการ (Leadership & Management)",
    "Remote Leadership": "การเป็นผู้นำและการจัดการ (Leadership & Management)",
    "New Manager": "การเป็นผู้นำและการจัดการ (Leadership & Management)",
    "Coaching Applied": "การเป็นผู้นำและการจัดการ (Leadership & Management)",
    "Coaching Essentials": "การเป็นผู้นำและการจัดการ (Leadership & Management)",
    "Change Management": "การเป็นผู้นำและการจัดการ (Leadership & Management)",
    "Change Management Essentials": "การเป็นผู้นำและการจัดการ (Leadership & Management)",
    "Performance Management": "การเป็นผู้นำและการจัดการ (Leadership & Management)",
    
    # 3. ทักษะทางธุรกิจและกลยุทธ์ (Business Skills & Strategy)
    "Business Skills": "ทักษะทางธุรกิจและกลยุทธ์ (Business Skills & Strategy)",
    "Business Continuity Applied": "ทักษะทางธุรกิจและกลยุทธ์ (Business Skills & Strategy)",
    "Business Continuity Essentials": "ทักษะทางธุรกิจและกลยุทธ์ (Business Skills & Strategy)",
    "Business Innovation Essentials": "ทักษะทางธุรกิจและกลยุทธ์ (Business Skills & Strategy)",
    "Strategy Development": "ทักษะทางธุรกิจและกลยุทธ์ (Business Skills & Strategy)",
    "Entrepreneurship": "ทักษะทางธุรกิจและกลยุทธ์ (Business Skills & Strategy)",
    "KPIs &#038; OKRs": "ทักษะทางธุรกิจและกลยุทธ์ (Business Skills & Strategy)",
    "KPIs & OKRs": "ทักษะทางธุรกิจและกลยุทธ์ (Business Skills & Strategy)",
    "Contract Management Essentials": "ทักษะทางธุรกิจและกลยุทธ์ (Business Skills & Strategy)",
    "Project Management Applied": "ทักษะทางธุรกิจและกลยุทธ์ (Business Skills & Strategy)",
    "Project Management Mastery": "ทักษะทางธุรกิจและกลยุทธ์ (Business Skills & Strategy)",
    "Project Management Training Essentials": "ทักษะทางธุรกิจและกลยุทธ์ (Business Skills & Strategy)",
    "Quality Management Essentials": "ทักษะทางธุรกิจและกลยุทธ์ (Business Skills & Strategy)",
    "Supply Chain Management": "ทักษะทางธุรกิจและกลยุทธ์ (Business Skills & Strategy)",
    
    # 4. การเงินและความเสี่ยง (Finance & Risk)
    "Corporate Finance": "การเงินและความเสี่ยง (Finance & Risk)",
    "Corporate Risk": "การเงินและความเสี่ยง (Finance & Risk)",
    "Finance Applied": "การเงินและความเสี่ยง (Finance & Risk)",
    "Finance Training Essentials": "การเงินและความเสี่ยง (Finance & Risk)",
    "Financial Compliance": "การเงินและความเสี่ยง (Finance & Risk)",
    "Financial Conduct Authority (UK)": "การเงินและความเสี่ยง (Finance & Risk)",
    "Personal Finances": "การเงินและความเสี่ยง (Finance & Risk)",
    "Risk and Uncertainty": "การเงินและความเสี่ยง (Finance & Risk)",
    
    # 5. การขายและการบริการลูกค้า (Sales & Customer Service)
    "Sales & Service": "การขาย การตลาด และบริการ (Sales, Marketing & Customer Service)",
    "Sales Mastery": "การขาย การตลาด และบริการ (Sales, Marketing & Customer Service)",
    "Sales Methodologies": "การขาย การตลาด และบริการ (Sales, Marketing & Customer Service)",
    "Sales to Customer Success": "การขาย การตลาด และบริการ (Sales, Marketing & Customer Service)",
    "Customer Service Applied": "การขาย การตลาด และบริการ (Sales, Marketing & Customer Service)",
    "Customer Service Mastery": "การขาย การตลาด และบริการ (Sales, Marketing & Customer Service)",
    "Customer Service Training Essentials": "การขาย การตลาด และบริการ (Sales, Marketing & Customer Service)",
    "Customer Success": "การขาย การตลาด และบริการ (Sales, Marketing & Customer Service)",
    "Retail Applied": "ทักษะเฉพาะอุตสาหกรรม (Industry Specific)",
    "Retail Essentials": "ทักษะเฉพาะอุตสาหกรรม (Industry Specific)",
    "Retail Mastery": "ทักษะเฉพาะอุตสาหกรรม (Industry Specific)",
    
    # 6. การตลาดและความคิดสร้างสรรค์ (Marketing & Creative)
    "Marketing Skills Applied": "การตลาดและความคิดสร้างสรรค์ (Marketing & Creative)",
    "Marketing Skills Mastery": "การตลาดและความคิดสร้างสรรค์ (Marketing & Creative)",
    "Marketing Training Essentials": "การตลาดและความคิดสร้างสรรค์ (Marketing & Creative)",
    "The Creative Process": "การตลาดและความคิดสร้างสรรค์ (Marketing & Creative)",
    "UI/UX Design": "การตลาดและความคิดสร้างสรรค์ (Marketing & Creative)",
    "Presentation Skills": "การสื่อสารและการทำงานร่วมกัน (Communication & Collaboration)",
    
    # 7. ทรัพยากรบุคคลและวัฒนธรรมองค์กร (HR & Workplace Culture)
    "Human Resources": "ทรัพยากรบุคคลและวัฒนธรรมองค์กร (HR & Workplace Culture)",
    "HR Training Essentials": "ทรัพยากรบุคคลและวัฒนธรรมองค์กร (HR & Workplace Culture)",
    "HR Strategy": "ทรัพยากรบุคคลและวัฒนธรรมองค์กร (HR & Workplace Culture)",
    "Company Culture": "ทรัพยากรบุคคลและวัฒนธรรมองค์กร (HR & Workplace Culture)",
    "Diversity and Inclusion": "ทรัพยากรบุคคลและวัฒนธรรมองค์กร (HR & Workplace Culture)",
    "Neurodiversity": "ทรัพยากรบุคคลและวัฒนธรรมองค์กร (HR & Workplace Culture)",
    "Employee Experience": "ทรัพยากรบุคคลและวัฒนธรรมองค์กร (HR & Workplace Culture)",
    "Employee Life Cycle": "ทรัพยากรบุคคลและวัฒนธรรมองค์กร (HR & Workplace Culture)",
    "Employee Teamwork Training Essentials": "การสื่อสารและการทำงานร่วมกัน (Communication & Collaboration)",
    "Teamwork Applied": "การสื่อสารและการทำงานร่วมกัน (Communication & Collaboration)",
    "Workplace Housekeeping": "การปฏิบัติตามกฎระเบียบและความปลอดภัย (Compliance & Safety)",
    "Work Ethic": "ทรัพยากรบุคคลและวัฒนธรรมองค์กร (HR & Workplace Culture)",
    "Hybrid Working": "ทรัพยากรบุคคลและวัฒนธรรมองค์กร (HR & Workplace Culture)",
    "Remote Working": "ทรัพยากรบุคคลและวัฒนธรรมองค์กร (HR & Workplace Culture)",
    
    # 8. เทคโนโลยีและซอฟต์แวร์ (Technology & Software)
    "Technology": "เทคโนโลยีและซอฟต์แวร์ (Technology & Software)",
    "Artificial Intelligence (AI)": "เทคโนโลยีและซอฟต์แวร์ (Technology & Software)",
    "Coding for Everyone": "เทคโนโลยีและซอฟต์แวร์ (Technology & Software)",
    "Data Analysis": "เทคโนโลยีและซอฟต์แวร์ (Technology & Software)",
    "Digital Transformation Essentials": "เทคโนโลยีและซอฟต์แวร์ (Technology & Software)",
    "Cybersecurity Training Essentials": "เทคโนโลยีและซอฟต์แวร์ (Technology & Software)",
    "Google Workspace": "เทคโนโลยีและซอฟต์แวร์ (Technology & Software)",
    "Introduction to Microsoft Software": "เทคโนโลยีและซอฟต์แวร์ (Technology & Software)",
    "Networking": "การสื่อสารและการทำงานร่วมกัน (Communication & Collaboration)",
    
    # 9. การปฏิบัติตามกฎระเบียบและความปลอดภัย (Compliance & Safety)
    "Compliance Essentials": "การปฏิบัติตามกฎระเบียบและความปลอดภัย (Compliance & Safety)",
    "Safety &amp; Compliance": "การปฏิบัติตามกฎระเบียบและความปลอดภัย (Compliance & Safety)",
    "Safety Leadership": "การปฏิบัติตามกฎระเบียบและความปลอดภัย (Compliance & Safety)",
    "Safeguarding": "การปฏิบัติตามกฎระเบียบและความปลอดภัย (Compliance & Safety)",
    "HIPAA Compliance Essentials": "การปฏิบัติตามกฎระเบียบและความปลอดภัย (Compliance & Safety)",
    "OSHA: Workplace Safety": "การปฏิบัติตามกฎระเบียบและความปลอดภัย (Compliance & Safety)",
    "Workplace Safety Training Essentials": "การปฏิบัติตามกฎระเบียบและความปลอดภัย (Compliance & Safety)",
    "Food Safety Applied": "การปฏิบัติตามกฎระเบียบและความปลอดภัย (Compliance & Safety)",
    "Food Safety Essentials": "การปฏิบัติตามกฎระเบียบและความปลอดภัย (Compliance & Safety)",
    
    # 10. สิ่งแวดล้อมและความยั่งยืน (Environment & Sustainability)
    "Environment &#038; Sustainability": "สิ่งแวดล้อมและความยั่งยืน (Environment & Sustainability)",
    "Environment &amp; Sustainability": "สิ่งแวดล้อมและความยั่งยืน (Environment & Sustainability)",
    
    # 11. ทักษะเฉพาะอุตสาหกรรม (Industry Specific)
    "Sector Specific": "ทักษะเฉพาะอุตสาหกรรม (Industry Specific)",
    "Healthcare Essentials": "ทักษะเฉพาะอุตสาหกรรม (Industry Specific)",
    
    # 12. ทั่วไปและอื่นๆ (General & Others)
    "One-Minute Learning": "ทั่วไปและอื่นๆ (General & Others)",
    "Online Social Presence": "ทั่วไปและอื่นๆ (General & Others)",
    "Temporary": "ทั่วไปและอื่นๆ (General & Others)",
    "Product Teams": "ทั่วไปและอื่นๆ (General & Others)",
    
    # 13. หมวดหมู่เพิ่มเติมและถอดรหัส HTML Entity (Mapped Missing & Unescaped Categories)
    "Communication Skills Applied": "การสื่อสารและการทำงานร่วมกัน (Communication & Collaboration)",
    "Nurturing Talent": "การเป็นผู้นำและการจัดการ (Leadership & Management)",
    "Sales & Service": "การขาย การตลาด และบริการ (Sales, Marketing & Customer Service)",
    "Sales &amp; Service": "การขาย การตลาด และบริการ (Sales, Marketing & Customer Service)",
    "Safety & Compliance": "การปฏิบัติตามกฎระเบียบและความปลอดภัย (Compliance & Safety)",
    "Safety &amp; Compliance": "การปฏิบัติตามกฎระเบียบและความปลอดภัย (Compliance & Safety)",
    "Environment & Sustainability": "สิ่งแวดล้อมและความยั่งยืน (Environment & Sustainability)",
    "Environment &amp; Sustainability": "สิ่งแวดล้อมและความยั่งยืน (Environment & Sustainability)",
    "Online Social Presence": "การขาย การตลาด และบริการ (Sales, Marketing & Customer Service)",
    "Product Teams": "เทคโนโลยีและซอฟต์แวร์ (Technology & Software)"
}

all_courses_list, titles_map, meta_map = load_base_data()
matched_courses_set = load_matched_courses()

# ----------------------------------------------------
# 1.5. Subcategory to Parent Category Map (Max 12 Parent Categories)
# ----------------------------------------------------

# ----------------------------------------------------
# 2. Details Cache Management (Dynamic)
# ----------------------------------------------------
def load_details_cache():
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_details_cache(cache):
    try:
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving details cache: {e}")

# ----------------------------------------------------
# 3. Text Cleanup Helper
# ----------------------------------------------------
def clean_text(text):
    if not text:
        return ""
    # Replace unicode punctuation with standard ASCII equivalents
    text = text.replace("\u2019", "'")  # Curly apostrophe
    text = text.replace("\u201c", '"')  # Left double quote
    text = text.replace("\u201d", '"')  # Right double quote
    text = text.replace("\u2013", "-")  # En dash
    text = text.replace("\u2014", "-")  # Em dash
    text = text.replace("\u2026", "...") # Ellipsis
    text = text.replace("\u00a0", " ")  # Non-breaking space
    text = text.replace("\xa0", " ")
    text = text.replace("\ufffd", "'")  # Unicode replacement character
    text = text.replace("\r\n", "\n")
    return text.strip()

# ----------------------------------------------------
# 4. Scraper for YouTube Video ID & Duration
# ----------------------------------------------------
def scrape_course_details(course_url):
    full_url = f"https://www.talentlms.com{course_url}"
    try:
        r = requests.get(full_url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })
        if r.status_code != 200:
            return "", ""
        
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Extract duration
        duration_div = soup.find(class_="course-hero__duration")
        duration = ""
        if duration_div:
            duration = duration_div.text.replace("Duration:", "").strip()
            
        # Extract youtube video ID
        lite_yt = soup.find("lite-youtube")
        videoid = ""
        if lite_yt and lite_yt.has_attr("videoid"):
            videoid = lite_yt["videoid"]
        else:
            # Fallback 1: search embed iframe
            for iframe in soup.find_all("iframe"):
                src = iframe.get("src", "")
                if "youtube.com" in src or "youtu.be" in src:
                    m = re.search(r"embed/([^/?&#]+)", src)
                    if m:
                        videoid = m.group(1)
                        break
            # Fallback 2: search standard watch links
            if not videoid:
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if "youtube.com/watch" in href:
                        m = re.search(r"v=([^&]+)", href)
                        if m:
                            videoid = m.group(1)
                            break
                    elif "youtu.be/" in href:
                        videoid = href.split("youtu.be/")[-1].split("?")[0]
                        break
                        
        video_url = f"https://www.youtube.com/embed/{videoid}" if videoid else ""
        return duration, video_url
    except Exception as e:
        print(f"Error scraping details from {course_url}: {e}")
        return "", ""

def parse_json_from_response(text):
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
        
    start = text.find("{")
    if start != -1:
        end = text.rfind("}")
        while end > start:
            try:
                return json.loads(text[start:end+1])
            except json.JSONDecodeError:
                end = text.rfind("}", start, end)
                
    raise json.JSONDecodeError("Failed to parse JSON even after trimming", text, 0)

# ----------------------------------------------------
# 5. Gemini Details Translator
# ----------------------------------------------------
def translate_course_details(api_key, course_desc, what_is_covered, why_take_this):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={api_key}"
    
    prompt = f"""
    You are a professional translator. Translate the following e-learning course details from English to professional, natural, and clear Thai.
    Keep any bullet points or lists intact.
    
    CRITICAL RULES FOR JSON OUTPUT:
    1. Return ONLY a JSON object with keys: "course_desc_th", "what_is_covered_desc_th", "why_take_this_course_desc_th".
    2. Do NOT include any markdown formatting like ```json or ``` wrappers. Output raw JSON text.
    3. Any double quotes inside the string values of the JSON object MUST be escaped as \\" (backslash followed by double quote) so that the JSON is valid.
    4. Do not use raw unescaped newlines inside string values. Use \\n instead.
    
    Course Overview:
    {course_desc}
    
    What's Covered:
    {what_is_covered}
    
    Why your teams need this course:
    {why_take_this}
    """
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.1,
            "max_output_tokens": 8192,
            "thinkingConfig": {
                "thinkingBudget": 0
            }
        }
    }
    
    try:
        r = requests.post(url, json=payload, timeout=25)
        if r.status_code == 200:
            res_data = r.json()
            text_response = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
            translated_obj = parse_json_from_response(text_response)
            return (
                translated_obj.get("course_desc_th", ""),
                translated_obj.get("what_is_covered_desc_th", ""),
                translated_obj.get("why_take_this_course_desc_th", "")
            )
        else:
            with open("error_log.txt", "a", encoding="utf-8") as f_err:
                f_err.write(f"Gemini API Error: status={r.status_code}, response={r.text[:500]}\n")
            print(f"Gemini Translation Error: {r.status_code} - {r.text}")
    except Exception as e:
        with open("error_log.txt", "a", encoding="utf-8") as f_err:
            f_err.write(f"Exception during translation: {str(e)}\n")
        print(f"Exception during details translation: {e}")
    return "", "", ""

# ----------------------------------------------------
# 6. Combined Scrape & Translate Flow (with Caching)
# ----------------------------------------------------
def get_course_details(course, api_key):
    cache = load_details_cache()
    obj_id = course["objectID"]
    
    # Return from cache if exists
    if obj_id in cache:
        cached_data = cache[obj_id]
        if "course_desc_th" in cached_data and "video_url" in cached_data:
            return cached_data
            
    # Log API key for diagnostics
    with open("key_log.txt", "a", encoding="utf-8") as f_log:
        f_log.write(f"api_key type: {type(api_key)}, length: {len(api_key) if api_key else 0}, value start: {api_key[:10] if api_key else 'None'}\n")

    # Scrape first
    duration, video_url = scrape_course_details(course["url"])
    
    # Prep source text
    course_desc = clean_text(course.get("course_desc", ""))
    what_is_covered = clean_text(course.get("what_is_covered_desc", ""))
    why_take_this = clean_text(course.get("why_take_this_course_desc", ""))
    
    # Translate
    course_desc_th, what_is_covered_th, why_take_this_th = "", "", ""
    if api_key:
        course_desc_th, what_is_covered_th, why_take_this_th = translate_course_details(
            api_key, course_desc, what_is_covered, why_take_this
        )
        
    # Fallback to English if translation fails/no API Key
    if not course_desc_th:
        course_desc_th = f"(ยังไม่ได้แปล) {course_desc}"
    if not what_is_covered_th:
        what_is_covered_th = f"(ยังไม่ได้แปล) {what_is_covered}"
    if not why_take_this_th:
        why_take_this_th = f"(ยังไม่ได้แปล) {why_take_this}"
        
    details = {
        "title": course["title"],
        "url": course["url"],
        "duration": duration or "10 mins",
        "video_url": video_url,
        "course_desc_th": course_desc_th,
        "what_is_covered_desc_th": what_is_covered_th,
        "why_take_this_course_desc_th": why_take_this_th,
        "course_desc_en": course_desc,
        "what_is_covered_desc_en": what_is_covered,
        "why_take_this_course_desc_en": why_take_this
    }
    
    # Save to cache
    cache[obj_id] = details
    save_details_cache(cache)
    return details

# ----------------------------------------------------
# 7. Sidebar Statistics Info
# ----------------------------------------------------
def render_stats_sidebar(courses_list):
    with st.sidebar.expander("📊 สถิติคลังหลักสูตร (Statistics)", expanded=False):
        total = len(courses_list)
        cache = load_details_cache()
        cached_count = len([k for k, v in cache.items() if "course_desc_th" in v and "video_url" in v])
        
        st.metric("หลักสูตรทั้งหมด", f"{total:,} วิชา", help="จำนวนหลักสูตรทั้งหมดใน TalentLibrary")
        st.metric("ดาวน์โหลด & แปลละเอียดแล้ว", f"{cached_count:,} วิชา", help="จำนวนหลักสูตรที่แปลละเอียดและเก็บข้อมูลวิดีโอแล้ว")
        
        pct = (cached_count / total) * 100 if total > 0 else 0
        st.markdown(f"**ความคืบหน้าของคลังข้อมูล:** `{pct:.1f}%`")
        st.progress(int(pct))

# ----------------------------------------------------
# 8. Course Detail Dialog Modal
# ----------------------------------------------------
@st.dialog(" ", width="large")
def show_course_details(course, api_key):
    # Fetch details
    with st.spinner("กำลังโหลดวิดีโอแนะนำและแปลเนื้อหาเป็นภาษาไทย..."):
        details = get_course_details(course, api_key)
        
    # Title Display & Video Availability Check
    matched_set = load_matched_courses()
    has_video = course["objectID"] in matched_set
    title_th = titles_map.get(course["title"], course["title"])
    if has_video:
        title_th = title_th + " *"
        title_color = "#047857" # Dark Green
        st.success("🇹🇭 มีเสียงบรรยายภาษาไทยของหลักสูตรนี้ในคลัง H:\\4 TalentLibrary เรียบร้อยแล้ว *")
    else:
        title_color = "#0F172A"
        
    st.markdown(f"<h1 style='font-size: 2.2rem; font-weight: 700; margin-top: -35px; margin-right: 60px; margin-bottom: 2px; color: {title_color}; line-height: 1.25; font-family: \"Prompt\", sans-serif;'>{title_th}</h1>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size: 1.1rem; color: #64748B; margin-bottom: 20px; font-weight: 500; font-family: \"Prompt\", sans-serif; margin-right: 60px;'>{course['title']}</div>", unsafe_allow_html=True)
    
    # Content Columns (Moved directly under the titles)
    col_media, col_desc = st.columns([1.2, 1.5])
    
    with col_media:
        if details["video_url"]:
            st.markdown("### 🎬 วิดีโอตัวอย่างหลักสูตร")
            video_url = details["video_url"]
            if "youtube.com" in video_url or "youtu.be" in video_url:
                video_id = None
                if "embed/" in video_url:
                    video_id = video_url.split("embed/")[-1].split("?")[0]
                elif "v=" in video_url:
                    video_id = video_url.split("v=")[-1].split("&")[0]
                elif "youtu.be/" in video_url:
                    video_id = video_url.split("youtu.be/")[-1].split("?")[0]
                
                if video_id:
                    embed_url = f"https://www.youtube.com/embed/{video_id}?cc_load_policy=1&cc_lang_pref=th&hl=th"
                    iframe_html = f"""
                    <iframe width="100%" height="240" src="{embed_url}" 
                            frameborder="0" 
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                            allowfullscreen>
                    </iframe>
                    """
                    st.components.v1.html(iframe_html, height=250)
                    
                    # Add translation guide as collapsible expander to save vertical space
                    with st.expander("💡 วิธีเปิดคำบรรยายภาษาไทย", expanded=False):
                        st.markdown("""
                        <ol style="font-size: 13px; color: #1E3A8A; margin: 0 0 0 16px; padding: 0; line-height: 1.5; font-family: 'Prompt', sans-serif;">
                            <li>คลิกที่ปุ่ม <b>ฟันเฟือง (Settings) ⚙️</b> ด้านขวาบนของตัวเล่นวิดีโอ</li>
                            <li>เลือก <b>คำบรรยาย (Subtitles/CC)</b></li>
                            <li>เลือก <b>แปลอัตโนมัติ (Auto-translate)</b> และเลือกภาษา <b>ไทย (Thai)</b></li>
                        </ol>
                        """, unsafe_allow_html=True)
                else:
                    st.video(video_url)
            else:
                st.video(video_url)
        else:
            st.info("ไม่มีวิดีโอแนะนำสำหรับวิชานี้")
            
        # Metadata section (รายละเอียดหลักสูตร) moved under the video - pushed up close to guide box
        raw_dur = details.get('duration', '10 mins')
        dur_th = raw_dur.replace("'", " นาที").replace(" mins", " นาที").replace(" min", " นาที")
        st.markdown(f"<div style='margin-top: 8px; font-size: 14px; font-family: \"Prompt\", sans-serif;'>⏱️ <b>ระยะเวลาการเรียนรู้:</b> 15 นาที</div>", unsafe_allow_html=True)
        
        cat_th = [meta_map["cats"].get(c, c) for c in course.get("cats", [])]
        st.markdown(f"<div style='margin-top: 4px; font-size: 14px; font-family: \"Prompt\", sans-serif;'>📁 <b>หมวดหมู่:</b> {', '.join(cat_th)}</div>", unsafe_allow_html=True)
        
        tag_th = [meta_map["tags"].get(t, t) for t in course.get("tags", [])]
        st.markdown(f"<div style='margin-top: 4px; font-size: 14px; font-family: \"Prompt\", sans-serif;'>💡 <b>ทักษะที่เกี่ยวข้อง:</b> {', '.join(tag_th)}</div>", unsafe_allow_html=True)
            
    with col_desc:
        # Bilingual tabs
        th_tab, en_tab = st.tabs(["ภาษาไทย (Thai)", "English (อังกฤษ)"])
        
        with th_tab:
            st.markdown("### 🧠 ภาพรวมหลักสูตร (Course Overview)")
            st.write(details["course_desc_th"])
            
            st.markdown("### 📝 เนื้อหาการเรียนรู้")
            st.write(details["what_is_covered_desc_th"])
            
            st.markdown("### 🚀 ประโยชน์ที่ทีมจะได้รับ")
            st.write(details["why_take_this_course_desc_th"])
            
        with en_tab:
            st.markdown("### 🧠 Course Overview")
            st.write(details["course_desc_en"])
            
            st.markdown("### 📝 What's Covered")
            st.write(details["what_is_covered_desc_en"])
            
            st.markdown("### 🚀 Why your teams need this course")
            st.write(details["why_take_this_course_desc_en"])

# ----------------------------------------------------
# 9. Main Application Entrypoint
# ----------------------------------------------------
def main():
    st.set_page_config(
        page_title="คลังหลักสูตร TalentLibrary ไทย",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    # Load API Key from config or env
    matched_courses_set = load_matched_courses()
    api_key = ""
    try:
        from config import GEMINI_API_KEY
        api_key = GEMINI_API_KEY
    except Exception:
        pass
        
    if not api_key:
        env_path = os.path.join(BASE_DIR, ".env")
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("GEMINI_API_KEY="):
                        api_key = line.strip().split("=", 1)[1]
                        
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY", "")

    # Startup key diagnostics
    with open("key_log.txt", "a", encoding="utf-8") as f_log:
        f_log.write(f"Startup - api_key length: {len(api_key) if api_key else 0}, value start: {api_key[:10] if api_key else 'None'}\n")

    # Layout and Sidebar
    
    # Catalog Description (Moved from Main Page Hero)
    st.sidebar.markdown("""
    <div style='margin-bottom: 15px; font-family: "Prompt", sans-serif;'>
        <h2 style='font-size: 1.8rem; font-weight: 700; color: #0284C7; margin: 0 0 6px 0; line-height: 1.2;'>TalentLibrary™ ไทย</h2>
        <p style='font-size: 0.95rem; color: #475569; margin: 0; line-height: 1.45;'>ค้นหารายละเอียด หลักสูตรออนไลน์ภาษาไทย พร้อมวิดีโอตัวอย่างและเนื้อหาการเรียนรู้ที่ครบถ้วน</p>
    </div>
    """, unsafe_allow_html=True)

    # Style primary buttons (used for course titles) to look like clean clickable hyperlinks and apply global Prompt font
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600;700&display=swap');
        
        /* Apply Prompt font globally to the entire app */
        html, body, .stApp, p, h1, h2, h3, h4, h5, h6, button, select, input, label, li, ol, ul, small {
            font-family: 'Prompt', sans-serif !important;
        }
        
        /* Remove top whitespace padding from main content area and sidebar */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 2rem !important;
        }
        header[data-testid="stHeader"] {
            background: transparent !important;
            height: 1rem !important;
            min-height: 0 !important;
        }
        section[data-testid="stSidebar"] > div:first-child {
            padding-top: 1rem !important;
        }
        div[data-testid="stMainBlockContainer"] {
            padding-top: 1rem !important;
        }
        
        /* Protect Streamlit's native icon fonts from being overridden */
        [class*="Icon"], [class*="icon"], [data-testid="stIcon"], svg {
            font-family: inherit !important;
        }
        
        /* Target all title buttons via Streamlit's container key class (div[class*="st-key-title_"] button) */
        div[class*="st-key-title_"] button,
        div[class*="st-key-title_"] button:hover,
        div[class*="st-key-title_"] button:focus,
        div[class*="st-key-title_"] button:active,
        [data-testid="stVerticalBlockBorderWrapper"] div.stButton:first-of-type > button,
        [data-testid="stVerticalBlockBorderWrapper"] div.stButton:first-of-type > button:hover,
        [data-testid="stVerticalBlockBorderWrapper"] div.stButton:first-of-type > button:focus,
        [data-testid="stVerticalBlockBorderWrapper"] div.stButton:first-of-type > button:active {
            background: transparent !important;
            background-color: transparent !important;
            border: none !important;
            border-width: 0 !important;
            border-style: none !important;
            border-color: transparent !important;
            border-radius: 0 !important;
            box-shadow: none !important;
            outline: none !important;
            padding: 4px 0 !important;
            margin: 0 !important;
            text-align: left !important;
            justify-content: flex-start !important;
            align-items: flex-start !important;
            cursor: pointer !important;
            width: 100% !important;
            height: auto !important;
            min-height: 0 !important;
        }

        /* Large Font size & hover underline for title buttons */
        div[class*="st-key-title_"] button *,
        [data-testid="stVerticalBlockBorderWrapper"] div.stButton:first-of-type > button * {
            font-size: 1.35rem !important;
            font-weight: 700 !important;
            line-height: 1.3 !important;
            text-align: left !important;
        }
        
        div[class*="st-key-title_"] button:hover *,
        [data-testid="stVerticalBlockBorderWrapper"] div.stButton:first-of-type > button:hover * {
            text-decoration: underline !important;
        }

        /* Card Category Pill Buttons */
        div[data-testid="stButton"] button[key^="btn_cat_"] {
            background: #F1F5F9 !important;
            background-color: #F1F5F9 !important;
            border: 1px solid #CBD5E1 !important;
            border-radius: 6px !important;
            padding: 2px 8px !important;
            margin: 2px 0 4px 0 !important;
            font-size: 0.78rem !important;
            font-weight: 500 !important;
            color: #334155 !important;
            text-align: left !important;
            justify-content: flex-start !important;
            align-items: center !important;
            display: inline-flex !important;
            box-shadow: none !important;
            height: auto !important;
            min-height: 0 !important;
            width: 100% !important;
        }
        div[data-testid="stButton"] button[key^="btn_cat_"]:hover {
            background: #E2E8F0 !important;
            background-color: #E2E8F0 !important;
            border-color: #0284C7 !important;
            color: #0284C7 !important;
        }
        div[data-testid="stButton"] button[key^="btn_cat_"] * {
            font-size: 0.78rem !important;
            font-weight: 500 !important;
            color: inherit !important;
        }

        /* Card Skill Tag Pill Buttons */
        div[data-testid="stButton"] button[key^="btn_tag_"] {
            background: #F0F9FF !important;
            background-color: #F0F9FF !important;
            border: 1px solid #BAE6FD !important;
            border-radius: 6px !important;
            padding: 2px 6px !important;
            margin: 2px 0 !important;
            font-size: 0.75rem !important;
            font-weight: 500 !important;
            color: #0284C7 !important;
            text-align: center !important;
            justify-content: center !important;
            align-items: center !important;
            display: inline-flex !important;
            box-shadow: none !important;
            height: auto !important;
            min-height: 0 !important;
            width: 100% !important;
        }
        div[data-testid="stButton"] button[key^="btn_tag_"]:hover {
            background: #E0F2FE !important;
            background-color: #E0F2FE !important;
            border-color: #0369A1 !important;
            color: #0369A1 !important;
        }
        div[data-testid="stButton"] button[key^="btn_tag_"] * {
            font-size: 0.75rem !important;
            font-weight: 500 !important;
            color: inherit !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # 9.2 Sidebar Search & Title
    st.sidebar.markdown("## 🔍 คลังหลักสูตร TalentLibrary")
    
    # Key-Version Bump for 100% instant frontend widget reset
    if "filter_version" not in st.session_state:
        st.session_state.filter_version = 0
    fv = st.session_state.filter_version
    
    # Search Input Bar
    search_query = st.sidebar.text_input(
        "ค้นหาหลักสูตร",
        value=st.session_state.get("search_query", ""),
        placeholder="พิมพ์ชื่อหลักสูตร (ไทย / อังกฤษ) หรือทักษะที่ต้องการ...",
        label_visibility="collapsed",
        key=f"search_query_{fv}"
    )
    selected_video_only = st.sidebar.checkbox("🇹🇭 แสดงเฉพาะหลักสูตรที่มีเสียงภาษาไทย (250 หลักสูตร)", value=True, key=f"video_only_{fv}")
    
    # Reset page index on search changes
    if "prev_search" not in st.session_state or st.session_state.prev_search != search_query:
        st.session_state.prev_search = search_query
        st.session_state.current_page = 1
        
    from collections import Counter
    
    # 1. Count courses per parent category
    parent_cat_counts = Counter()
    for c in all_courses_list:
        parents_for_course = set()
        for cat in c.get("cats", []):
            parent = PARENT_CATS_MAP.get(cat, "ทั่วไปและอื่นๆ (General & Others)")
            parents_for_course.add(parent)
        for parent in parents_for_course:
            parent_cat_counts[parent] += 1
            
    # Prepare parent category options (Short Thai name to prevent layout truncation)
    parent_options = ["ทั้งหมด (All)"]
    option_to_parent_map = {"ทั้งหมด (All)": "All"}
    for p, count in parent_cat_counts.most_common():
        thai_part = p.split(" (")[0]
        opt_text = f"{thai_part} ({count} หลักสูตร)"
        parent_options.append(opt_text)
        option_to_parent_map[opt_text] = p
        
    # Check session state for requested parent category filter from card button click
    parent_def_idx = 0
    req_parent = st.session_state.get("filter_parent_cat")
    if req_parent:
        for idx, opt in enumerate(parent_options):
            if option_to_parent_map[opt] == req_parent:
                parent_def_idx = idx
                break
                
    selected_parent_opt = st.sidebar.selectbox("หมวดหมู่หลัก", parent_options, index=parent_def_idx, key=f"sel_parent_cat_{fv}")
    selected_parent = option_to_parent_map[selected_parent_opt]
    
    # 2. Count courses per subcategory (pre-filtered by selected parent category)
    subcat_counts = Counter()
    for c in all_courses_list:
        for cat in c.get("cats", []):
            parent_of_cat = PARENT_CATS_MAP.get(cat, PARENT_CATS_MAP.get(html.unescape(cat), "ทั่วไปและอื่นๆ (General & Others)"))
            if selected_parent == "All" or parent_of_cat == selected_parent:
                subcat_counts[cat] += 1
                
    # Prepare subcategory options (short format to ensure visibility of counts)
    subcat_options = ["ทั้งหมด (All)"]
    option_to_subcat_map = {"ทั้งหมด (All)": "All"}
    for subcat, count in subcat_counts.most_common():
        subcat_thai = meta_map["cats"].get(subcat, subcat)
        opt_text = f"{subcat_thai} ({count} หลักสูตร)"
        subcat_options.append(opt_text)
        option_to_subcat_map[opt_text] = subcat
        
    child_def_idx = 0
    req_child = st.session_state.get("filter_child_cat")
    if req_child:
        for idx, opt in enumerate(subcat_options):
            if option_to_subcat_map[opt] == req_child:
                child_def_idx = idx
                break
                
    selected_child_opt = st.sidebar.selectbox("หมวดหมู่ย่อย", subcat_options, index=child_def_idx, key=f"sel_child_cat_{fv}")
    selected_child = option_to_subcat_map[selected_child_opt]
    
    # 3. Count courses per parent tag/skill group (Independent of category selection)
    parent_tag_counts = Counter()
    for c in all_courses_list:
        parents_for_course = set()
        for tag in c.get("tags", []):
            parent = PARENT_TAGS_MAP.get(tag, "ทั่วไปและอื่นๆ (General & Others)")
            parents_for_course.add(parent)
        for parent in parents_for_course:
            parent_tag_counts[parent] += 1
            
    # Prepare parent tag options (Short Thai name to prevent layout truncation)
    parent_tag_options = ["ทั้งหมด (All)"]
    option_to_parent_tag_map = {"ทั้งหมด (All)": "All"}
    for p, count in parent_tag_counts.most_common():
        thai_part = p.split(" (")[0]
        opt_text = f"{thai_part} ({count} หลักสูตร)"
        parent_tag_options.append(opt_text)
        option_to_parent_tag_map[opt_text] = p
        
    parent_tag_def_idx = 0
    req_parent_tag = st.session_state.get("filter_parent_tag")
    if req_parent_tag:
        for idx, opt in enumerate(parent_tag_options):
            if option_to_parent_tag_map[opt] == req_parent_tag:
                parent_tag_def_idx = idx
                break
                
    selected_parent_tag_opt = st.sidebar.selectbox("กลุ่มทักษะหลัก", parent_tag_options, index=parent_tag_def_idx, key=f"sel_parent_tag_{fv}")
    selected_parent_tag = option_to_parent_tag_map[selected_parent_tag_opt]
    
    # 4. Count courses per child tag/skill (pre-filtered by selected parent skill group)
    child_tag_counts = Counter()
    for c in all_courses_list:
        for tag in c.get("tags", []):
            parent_of_tag = PARENT_TAGS_MAP.get(tag, "ทั่วไปและอื่นๆ (General & Others)")
            if selected_parent_tag == "All" or parent_of_tag == selected_parent_tag:
                child_tag_counts[tag] += 1
                
    # Prepare child tag options (short format to ensure visibility of counts)
    child_tag_options = ["ทั้งหมด (All)"]
    option_to_child_tag_map = {"ทั้งหมด (All)": "All"}
    for tag, count in child_tag_counts.most_common():
        tag_thai = meta_map["tags"].get(tag, tag)
        opt_text = f"{tag_thai} ({count} หลักสูตร)"
        child_tag_options.append(opt_text)
        option_to_child_tag_map[opt_text] = tag
        
    child_tag_def_idx = 0
    req_child_tag = st.session_state.get("filter_child_tag")
    if req_child_tag:
        for idx, opt in enumerate(child_tag_options):
            if option_to_child_tag_map[opt] == req_child_tag:
                child_tag_def_idx = idx
                break
                
    selected_child_tag_opt = st.sidebar.selectbox("ทักษะย่อย", child_tag_options, index=child_tag_def_idx, key=f"sel_child_tag_{fv}")
    selected_child_tag = option_to_child_tag_map[selected_child_tag_opt]
        
    # Filter logic execution
    filtered_courses = []
    
    # Search query regex matching
    q = search_query.strip().lower()
    
    for c in all_courses_list:
        if selected_video_only and c.get('objectID') not in matched_courses_set:
            continue
        # Parent Category filter
        if selected_parent != "All":
            has_parent = False
            for cat in c.get("cats", []):
                parent_of_cat = PARENT_CATS_MAP.get(cat, PARENT_CATS_MAP.get(html.unescape(cat), "ทั่วไปและอื่นๆ (General & Others)"))
                if parent_of_cat == selected_parent:
                    has_parent = True
                    break
            if not has_parent:
                continue
                
        # Subcategory filter
        if selected_child != "All" and selected_child not in c.get("cats", []):
            continue
            
        # Parent Tag filter
        if selected_parent_tag != "All":
            has_parent_tag = False
            for tag in c.get("tags", []):
                parent_of_tag = PARENT_TAGS_MAP.get(tag, "ทั่วไปและอื่นๆ (General & Others)")
                if parent_of_tag == selected_parent_tag:
                    has_parent_tag = True
                    break
            if not has_parent_tag:
                continue
                
        # Child Tag filter
        if selected_child_tag != "All" and selected_child_tag not in c.get("tags", []):
            continue
            
        # Text query filter
        if q:
            title_en = c["title"].lower()
            title_th = titles_map.get(c["title"], "").lower()
            excerpt = c.get("course_excerpt", "").lower()
            desc = c.get("course_desc", "").lower()
            cats_str = " ".join(c.get("cats", [])).lower()
            tags_str = " ".join(c.get("tags", [])).lower()
            
            # Match titles, excerpts, descriptions, categories or tags
            if (q not in title_en and 
                q not in title_th and 
                q not in excerpt and 
                q not in desc and 
                q not in cats_str and 
                q not in tags_str):
                continue
                
        filtered_courses.append(c)
        
    total_courses = len(filtered_courses)
    
    # Reset filter button in sidebar
    is_filtered = (search_query or 
                   selected_parent_opt != "ทั้งหมด (All)" or 
                   selected_child_opt != "ทั้งหมด (All)" or 
                   selected_parent_tag_opt != "ทั้งหมด (All)" or 
                   selected_child_tag_opt != "ทั้งหมด (All)")
    if is_filtered:
        if st.sidebar.button("🔄 ล้างตัวกรองทั้งหมด", use_container_width=True):
            st.session_state.filter_version += 1
            st.session_state.current_page = 1
            for k in ["filter_parent_cat", "filter_child_cat", "filter_parent_tag", "filter_child_tag"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()

    # Display Filter Summary in Sidebar
    st.sidebar.divider()
    st.sidebar.markdown(f"พบหลักสูตรที่ตรงตามเงื่อนไข **{total_courses:,}** หลักสูตร จากทั้งหมด 1,089 หลักสูตร")
    
    # 9.4 Pagination Calculation
    items_per_page = 12
    total_pages = (total_courses - 1) // items_per_page + 1 if total_courses > 0 else 1
    
    if "current_page" not in st.session_state:
        st.session_state.current_page = 1
        
    if st.session_state.current_page > total_pages:
        st.session_state.current_page = total_pages
    if st.session_state.current_page < 1:
        st.session_state.current_page = 1

    start_idx = (st.session_state.current_page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    page_courses = filtered_courses[start_idx:end_idx]

    # Load details cache for cover images
    details_cache = load_details_cache()
    st.divider()

    # 9.5 Cards Grid layout & Top Pagination Bar
    if total_courses == 0:
        st.warning("ไม่พบหลักสูตรที่ต้องการ กรุณาลองใช้คำค้นหาอื่นหรือปรับตัวกรอง")
    else:
        # Top Pagination Bar
        if total_pages > 1:
            col_p_prev, col_p_info, col_p_next = st.columns([1.5, 3, 1.5])
            with col_p_prev:
                if st.button("⬅️ ก่อนหน้า", key="top_prev", disabled=(st.session_state.current_page == 1)):
                    st.session_state.current_page -= 1
                    st.rerun()
            with col_p_info:
                st.markdown(
                    f"<div style='text-align: center; font-weight: bold; margin-top: 6px; color: #334155;'>"
                    f"หน้า {st.session_state.current_page} / {total_pages} (แสดงหลักสูตรลำดับที่ {start_idx + 1} - {min(end_idx, total_courses)} จาก {total_courses:,} หลักสูตร)"
                    f"</div>",
                    unsafe_allow_html=True
                )
            with col_p_next:
                if st.button("ถัดไป ➡️", key="top_next", disabled=(st.session_state.current_page == total_pages)):
                    st.session_state.current_page += 1
                    st.rerun()
            st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)
        else:
            st.markdown(
                f"<div style='text-align: center; font-weight: bold; margin-bottom: 12px; color: #334155;'>"
                f"หน้า 1 / 1 (แสดงหลักสูตรลำดับที่ 1 - {total_courses} จาก {total_courses:,} หลักสูตร)"
                f"</div>",
                unsafe_allow_html=True
            )
            
        # 4 Columns for grids
        cols = st.columns(4)
        for idx, course in enumerate(page_courses):
            col_idx = idx % 4
            with cols[col_idx]:
                with st.container(border=True):
                    # Get course cover image from cache or construct fallback
                    obj_id = course["objectID"]
                    details = details_cache.get(obj_id, {})
                    image_url = details.get("image_url", "")
                    if not image_url:
                        slug = course["url"].strip("/").split("/")[-1]
                        image_url = f"https://images.www.talentlms.com/library/wp-content/uploads/{slug}-online-training-course-web.jpg"
                    
                    st.image(image_url, width='stretch')
                    
                    # Check if course has matched Thai audio in H:\4 TalentLibrary
                    obj_id = course["objectID"]
                    has_video = obj_id in matched_courses_set
                    t_th = titles_map.get(course["title"], course["title"])
                    
                    if has_video:
                        t_th_display = f":green[**{t_th} * 🇹🇭**]"
                    else:
                        t_th_display = f":blue[**{t_th}**]"
                        
                    if st.button(t_th_display, key=f"title_{course['objectID']}", use_container_width=True):
                        show_course_details(course, api_key)
                        
                    # English Title
                    st.markdown(f"""<div style='color: #64748B; font-size: 0.82rem; margin-top: -6px; margin-bottom: 4px; font-family: "Prompt", sans-serif;'>{course['title']}</div>""", unsafe_allow_html=True)
                    
                    # Interactive Category Pill Button: 📁 หมวดหมู่หลัก • หมวดหมู่ย่อย
                    raw_cat = course.get("cats", [""])[0] if course.get("cats") else ""
                    cat_parent = PARENT_CATS_MAP.get(raw_cat, PARENT_CATS_MAP.get(html.unescape(raw_cat), "ทั่วไปและอื่นๆ (General & Others)"))
                    parent_cat_short = cat_parent.split(" (")[0]
                    subcat_th = meta_map["cats"].get(raw_cat, "ทั่วไป")
                    
                    cat_btn_text = f"📁 {parent_cat_short} • {subcat_th}"
                    if st.button(cat_btn_text, key=f"btn_cat_{course['objectID']}", use_container_width=True):
                        st.session_state["filter_parent_cat"] = cat_parent
                        st.session_state["filter_child_cat"] = raw_cat
                        st.session_state["filter_parent_tag"] = "All"
                        st.session_state["filter_child_tag"] = "All"
                        st.session_state.filter_version += 1
                        st.session_state.current_page = 1
                        st.rerun()
                        
                    # Interactive Skill Tag Pill Buttons: 💡 ทักษะย่อย
                    tags_list = course.get("tags", [])[:2]
                    if tags_list:
                        t_cols = st.columns(len(tags_list))
                        for t_idx, tag_code in enumerate(tags_list):
                            tag_th = meta_map["tags"].get(tag_code, tag_code)
                            parent_tag = PARENT_TAGS_MAP.get(tag_code, "ทั่วไปและอื่นๆ (General & Others)")
                            with t_cols[t_idx]:
                                if st.button(f"💡 {tag_th}", key=f"btn_tag_{course['objectID']}_{t_idx}", use_container_width=True):
                                    st.session_state["filter_parent_cat"] = "All"
                                    st.session_state["filter_child_cat"] = "All"
                                    st.session_state["filter_parent_tag"] = parent_tag
                                    st.session_state["filter_child_tag"] = tag_code
                                    st.session_state.filter_version += 1
                                    st.session_state.current_page = 1
                                    st.rerun()
                    
                    st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)
                    
                    # View details button (Restored to original label)
                    if st.button("🔍 ดูรายละเอียดวิชา", key=f"det_{course['objectID']}", use_container_width=True):
                        show_course_details(course, api_key)
                        
        # 9.6 Bottom Pagination Buttons Render
        if total_pages > 1:
            st.divider()
            col_p_prev, col_p_info, col_p_next = st.columns([1.5, 3, 1.5])
            with col_p_prev:
                if st.button("⬅️ ก่อนหน้า", key="bottom_prev", disabled=(st.session_state.current_page == 1)):
                    st.session_state.current_page -= 1
                    st.rerun()
            with col_p_info:
                st.markdown(
                    f"<div style='text-align: center; font-weight: bold; margin-top: 6px; color: #334155;'>"
                    f"หน้า {st.session_state.current_page} / {total_pages} (แสดงหลักสูตรลำดับที่ {start_idx + 1} - {min(end_idx, total_courses)} จาก {total_courses:,} หลักสูตร)"
                    f"</div>",
                    unsafe_allow_html=True
                )
            with col_p_next:
                if st.button("ถัดไป ➡️", key="bottom_next", disabled=(st.session_state.current_page == total_pages)):
                    st.session_state.current_page += 1
                    st.rerun()

if __name__ == "__main__":
    main()

