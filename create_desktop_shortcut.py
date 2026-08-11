import os
import sys

def create_desktop_shortcut():
    desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
    project_dir = os.path.dirname(os.path.abspath(__file__))
    target_bat = os.path.join(project_dir, 'Start_Studio.bat')
    shortcut_path = os.path.join(desktop, 'eBook to e-Learning Studio.lnk')
    
    vbs_script = f"""
    Set WshShell = CreateObject("WScript.Shell")
    Set shortcut = WshShell.CreateShortcut("{shortcut_path.replace('\\', '\\\\')}")
    shortcut.TargetPath = "{target_bat.replace('\\', '\\\\')}"
    shortcut.WorkingDirectory = "{project_dir.replace('\\', '\\\\')}"
    shortcut.Description = "Launch eBook to e-Learning Studio"
    shortcut.Save
    """
    
    temp_vbs = os.path.join(project_dir, 'make_shortcut.vbs')
    with open(temp_vbs, 'w', encoding='utf-8') as f:
        f.write(vbs_script)
        
    os.system(f'cscript //nologo "{temp_vbs}"')
    if os.path.exists(temp_vbs):
        os.remove(temp_vbs)
        
    print(f"Created Desktop Shortcut: {shortcut_path}")

if __name__ == "__main__":
    create_desktop_shortcut()
