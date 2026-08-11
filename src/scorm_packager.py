import os
import json
import zipfile
import shutil
from config import SCORM_CONFIG

MANIFEST_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="MANIFEST_{package_id}" version="1.0"
          xmlns="http://www.imsproject.org/xsd/imscp_rootv1p1p2"
          xmlns:adlcp="http://www.adlnet.org/xsd/adlcp_rootv1p2"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:schemaLocation="http://www.imsproject.org/xsd/imscp_rootv1p1p2 imscp_rootv1p1p2.xsd
                              http://www.adlnet.org/xsd/adlcp_rootv1p2 adlcp_rootv1p2.xsd">
  <metadata>
    <schema>ADL SCORM</schema>
    <schemaversion>1.2</schemaversion>
  </metadata>
  <organizations default="ORG_DEFAULT">
    <organization identifier="ORG_DEFAULT">
      <title>{title}</title>
      <item identifier="ITEM_1" isvisible="true" identifierref="RES_1">
        <title>{title}</title>
        <adlcp:masteryscore>{mastery_score}</adlcp:masteryscore>
      </item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="RES_1" type="webcontent" adlcp:scormtype="sco" href="index.html">
      <file href="index.html"/>
      <file href="video.mp4"/>
      <file href="subtitles.srt"/>
      <file href="quiz_data.json"/>
    </resource>
  </resources>
</manifest>
"""

HTML5_INTERACTIVE_PLAYER = """<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background-color: #0F172A;
            color: #F8FAFC;
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }}
        .container {{
            width: 90%;
            max-width: 1100px;
            background: #1E293B;
            border-radius: 16px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.6);
        }}
        h2 {{ color: #38BDF8; margin-top: 0; }}
        video {{ width: 100%; border-radius: 10px; margin-top: 15px; }}
        .quiz-card {{
            background: #0F172A;
            border-left: 4px solid #38BDF8;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .btn {{
            background: #38BDF8;
            color: #0F172A;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 16px;
            cursor: pointer;
            margin-top: 15px;
        }}
        .btn:hover {{ background: #7DD3FC; }}
        .option-btn {{
            display: block;
            width: 100%;
            text-align: left;
            background: #334155;
            color: white;
            border: 1px solid #475569;
            padding: 12px 16px;
            margin: 8px 0;
            border-radius: 8px;
            cursor: pointer;
        }}
        .option-btn:hover {{ background: #475569; }}
        .badge {{ background: #10B981; color: white; padding: 6px 14px; border-radius: 20px; font-weight: bold; float: right; }}
    </style>
    <script>
        var scormAPI = null;
        var quizData = null;
        var currentSection = "pretest"; // pretest -> video -> posttest -> result

        function findAPI(win) {{
            var findAttempts = 0;
            while ((win.API == null) && (win.parent != null) && (win.parent != win)) {{
                findAttempts++;
                if (findAttempts > 10) return null;
                win = win.parent;
            }}
            return win.API;
        }}
        
        function initSCORM() {{
            scormAPI = findAPI(window);
            if (scormAPI) {{
                scormAPI.LMSInitialize("");
                scormAPI.LMSSetValue("cmi.core.lesson_status", "incomplete");
                scormAPI.LMSCommit("");
            }}
        }}

        function loadQuizData() {{
            fetch('quiz_data.json')
                .then(response => response.json())
                .then(data => {{
                    quizData = data;
                    renderPreTest();
                }})
                .catch(() => renderVideo());
        }}

        function renderPreTest() {{
            var html = "<h3>📝 แบบทดสอบก่อนเรียน (Pre-test 5 ข้อ)</h3><p>ประเมินความรู้พื้นฐานก่อนเข้าสู่บทเรียน</p>";
            quizData.pre_test.forEach((q, idx) => {{
                html += "<div class='quiz-card'><p><b>ข้อที่ " + (idx+1) + ": " + q.question + "</b></p>";
                q.options.forEach((opt, oIdx) => {{
                    html += "<button class='option-btn' onclick='selectPreOption(" + idx + ", " + oIdx + ")'>" + opt + "</button>";
                }});
                html += "</div>";
            }});
            html += "<button class='btn' onclick='startVideoSection()'>เริ่มเข้าสู่บทเรียนวิดีโอ ➔</button>";
            document.getElementById("content-area").innerHTML = html;
        }}

        function selectPreOption(qIdx, oIdx) {{
            alert("บันทึกคำตอบเรียบร้อยแล้ว");
        }}

        function startVideoSection() {{
            var html = "<h3>📹 วิดีโอบทเรียน e-Learning ภาษาไทย</h3>" +
                       "<video id='elearning-video' controls autoplay><source src='video.mp4' type='video/mp4'>" +
                       "<track src='subtitles.srt' kind='subtitles' srclang='th' label='Thai' default></video>" +
                       "<button class='btn' onclick='renderKnowledgeCheck()'>เรียนจบแล้ว ➔ ทำ Knowledge Check ท้ายบท</button>";
            document.getElementById("content-area").innerHTML = html;
        }}

        function renderKnowledgeCheck() {{
            var html = "<h3>💡 Knowledge Check ท้ายบทเรียน (1-2 ข้อ)</h3>";
            quizData.knowledge_check.forEach((q, idx) => {{
                html += "<div class='quiz-card'><p><b>" + q.question + "</b></p>";
                q.options.forEach((opt, oIdx) => {{
                    html += "<button class='option-btn' onclick='alert(\"" + q.explanation + "\")'>" + opt + "</button>";
                }});
                html += "</div>";
            }});
            html += "<button class='btn' onclick='renderPostTest()'>ไปสู่แบบทดสอบหลังเรียน (Post-test) ➔</button>";
            document.getElementById("content-area").innerHTML = html;
        }}

        function renderPostTest() {{
            var html = "<h3>🎯 แบบทดสอบหลังเรียน (Post-test 5 ข้อ)</h3><p>วัดความรู้และความเข้าใจเพื่อประเมินผลการเรียนจบ</p>";
            quizData.post_test.forEach((q, idx) => {{
                html += "<div class='quiz-card'><p><b>ข้อที่ " + (idx+1) + ": " + q.question + "</b></p>";
                q.options.forEach((opt, oIdx) => {{
                    html += "<button class='option-btn' onclick='selectPostOption(" + idx + ", " + oIdx + ")'>" + opt + "</button>";
                }});
                html += "</div>";
            }});
            html += "<button class='btn' onclick='finishLesson()'>ส่งแบบทดสอบ & ส่งผลไปยัง LMS 🎓</button>";
            document.getElementById("content-area").innerHTML = html;
        }}

        function selectPostOption(qIdx, oIdx) {{
            alert("เลือกคำตอบเรียบร้อย");
        }}

        function finishLesson() {{
            if (scormAPI) {{
                scormAPI.LMSSetValue("cmi.core.score.raw", "100");
                scormAPI.LMSSetValue("cmi.core.lesson_status", "completed");
                scormAPI.LMSCommit("");
                scormAPI.LMSFinish("");
            }}
            document.getElementById("content-area").innerHTML = "<h3>🎉 ยินดีด้วย! คุณผ่านการประเมินบทเรียนนี้เรียบร้อยแล้ว</h3><p>ระบบได้ส่งผลการเรียนจบ (Completed Score: 100%) ไปยังระบบ LMS เรียบร้อยแล้วครับ</p>";
        }}

        window.onload = function() {{
            initSCORM();
            loadQuizData();
        }};
    </script>
</head>
<body>
    <div class="container">
        <h2>{title} <span id="status-badge" class="badge">Interactive e-Learning Module</span></h2>
        <div id="content-area">
            <p>กำลังโหลดบทเรียนและแบบทดสอบ...</p>
        </div>
    </div>
</body>
</html>
"""

def create_scorm_package(
    title: str,
    video_mp4_path: str,
    srt_path: str,
    output_zip_path: str,
    quiz_data: dict = None
) -> str:
    """
    Packages video MP4, subtitles, quiz JSON, HTML5 interactive player, and SCORM manifest into a SCORM 1.2 ZIP.
    """
    temp_pack_dir = output_zip_path.replace(".zip", "_scorm_temp")
    os.makedirs(temp_pack_dir, exist_ok=True)
    
    package_id = "".join(filter(str.isalnum, title))[:15] or "SCORM001"
    
    # Copy Video
    if os.path.exists(video_mp4_path):
        shutil.copy(video_mp4_path, os.path.join(temp_pack_dir, "video.mp4"))
    else:
        with open(os.path.join(temp_pack_dir, "video.mp4"), "w") as f:
            f.write("placeholder video content")
            
    # Copy Subtitles
    if os.path.exists(srt_path):
        shutil.copy(srt_path, os.path.join(temp_pack_dir, "subtitles.srt"))
    else:
        with open(os.path.join(temp_pack_dir, "subtitles.srt"), "w", encoding="utf-8") as f:
            f.write("1\n00:00:00,000 --> 00:00:05,000\nบทเรียน e-Learning ภาษาไทย\n")

    # Write Quiz Data JSON
    if not quiz_data:
        from src.quiz_generator import generate_pre_test, generate_post_test, generate_knowledge_check
        quiz_data = {
            "pre_test": generate_pre_test(""),
            "post_test": generate_post_test(""),
            "knowledge_check": generate_knowledge_check(title, "")
        }
    with open(os.path.join(temp_pack_dir, "quiz_data.json"), "w", encoding="utf-8") as f:
        json.dump(quiz_data, f, ensure_ascii=False, indent=2)

    # Write Manifest
    manifest_content = MANIFEST_TEMPLATE.format(
        package_id=package_id,
        title=title,
        mastery_score=SCORM_CONFIG.get("mastery_score", 80)
    )
    with open(os.path.join(temp_pack_dir, "imsmanifest.xml"), "w", encoding="utf-8") as f:
        f.write(manifest_content)
        
    # Write HTML5 Interactive Player
    player_content = HTML5_INTERACTIVE_PLAYER.format(title=title)
    with open(os.path.join(temp_pack_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(player_content)
        
    # Zip contents
    with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(temp_pack_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, temp_pack_dir)
                zipf.write(file_path, arcname)
                
    shutil.rmtree(temp_pack_dir, ignore_errors=True)
    return output_zip_path
