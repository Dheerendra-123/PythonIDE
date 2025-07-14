import tempfile
import subprocess

def run_code(code):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w") as f:
        f.write(code)
        f.flush()
        try:
            result = subprocess.run(["python", f.name], capture_output=True, text=True, timeout=5)
            return result.stdout or result.stderr
        except Exception as e:
            return str(e)
