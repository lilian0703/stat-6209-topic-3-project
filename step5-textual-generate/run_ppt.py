import subprocess, sys
result = subprocess.run(
    [sys.executable, r"c:\Users\93480\Desktop\开学\学习\下学期\6209\大作业\stat-6209-topic-3-project\step5-textual-generate\create_ppt.py"],
    capture_output=True, text=True, encoding="utf-8"
)
log = r"c:\Users\93480\Desktop\开学\学习\下学期\6209\大作业\stat-6209-topic-3-project\step5-textual-generate\ppt_log.txt"
with open(log, "w", encoding="utf-8") as f:
    f.write(f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}\n\nRETURN CODE: {result.returncode}\n")
