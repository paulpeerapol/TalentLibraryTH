import os
import re

def extract_text_from_file(file_path: str) -> str:
    """
    Extracts text from PDF, TXT, or Markdown files.
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n\n"
            return text.strip()
        except ImportError:
            raise ImportError("Please install pypdf (`pip install pypdf`) to extract PDF files.")
    elif ext in [".txt", ".md"]:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    else:
        # Fallback reading as plain text
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read().strip()

def chunk_content_into_modules(text: str, target_word_count: int = 500) -> list[dict]:
    """
    Splits long text into digestible Micro-learning modules (3-5 minutes each).
    Returns a list of dicts with module id, title, and content.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    
    modules = []
    current_module = []
    current_word_count = 0
    module_counter = 1
    
    for p in paragraphs:
        words = p.split()
        current_module.append(p)
        current_word_count += len(words)
        
        if current_word_count >= target_word_count:
            module_text = "\n\n".join(current_module)
            # Infer title from first line or generate generic
            first_line = current_module[0].split("\n")[0][:60]
            title = re.sub(r'[^a-zA-Z0-9\s]', '', first_line).strip() or f"Module {module_counter}"
            
            modules.append({
                "module_id": f"module_{module_counter:02d}",
                "title": title,
                "text": module_text,
                "estimated_duration_min": round(current_word_count / 130, 1) # ~130 words/min
            })
            
            module_counter += 1
            current_module = []
            current_word_count = 0
            
    # Catch remaining text
    if current_module:
        module_text = "\n\n".join(current_module)
        first_line = current_module[0].split("\n")[0][:60]
        title = re.sub(r'[^a-zA-Z0-9\s]', '', first_line).strip() or f"Module {module_counter}"
        modules.append({
            "module_id": f"module_{module_counter:02d}",
            "title": title,
            "text": module_text,
            "estimated_duration_min": round(current_word_count / 130, 1)
        })
        
    return modules
