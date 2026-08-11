' ========================================================
' eBook to e-Learning Studio - Silent VBScript Launcher
' Launches Web App directly in Web Browser with zero terminal window
' ========================================================
Set WshShell = CreateObject("WScript.Shell")
strPath = WshShell.CurrentDirectory
WshShell.Run "cmd /c python -m streamlit run """ & strPath & "\app.py"" --server.headless=false", 0, False
