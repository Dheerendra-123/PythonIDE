import tempfile
import subprocess
import os
import sys
from threading import Thread
import queue

def run_code(code, file_path=None, input_queue=None, output_callback=None):

    with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w") as f:
        f.write(code)
        f.flush()
        temp_file = f.name
    
    try:

        if file_path:
            work_dir = os.path.dirname(os.path.abspath(file_path))
            display_path = os.path.abspath(file_path)
        else:
            work_dir = os.getcwd()
            display_path = temp_file
        
        process = subprocess.Popen(
            [sys.executable, temp_file],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=work_dir,
            bufsize=0
        )
        
        def handle_input():
            if input_queue:
                try:
                    while process.poll() is None:
                        try:
                            user_input = input_queue.get(timeout=0.1)
                            if user_input is not None:
                                process.stdin.write(user_input + '\n')
                                process.stdin.flush()
                        except queue.Empty:
                            continue
                except:
                    pass
        
        if input_queue:
            input_thread = Thread(target=handle_input, daemon=True)
            input_thread.start()
        
        stdout, stderr = process.communicate(timeout=30)
        
        try:
            os.unlink(temp_file)
        except:
            pass
        
        result = ""
        if stdout:
            result += stdout
        if stderr:
            result += stderr
        
        return result, process.returncode, display_path
        
    except subprocess.TimeoutExpired:
        process.kill()
        try:
            os.unlink(temp_file)
        except:
            pass
        return "Process timed out after 30 seconds", 1, display_path
    except Exception as e:
        try:
            os.unlink(temp_file)
        except:
            pass
        return str(e), 1, display_path if 'display_path' in locals() else temp_file

def run_command(command, work_dir=None):
    """
    Run a system command in the terminal
    """
    if not work_dir:
        work_dir = os.getcwd()
    
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=work_dir
        )
        
        stdout, stderr = process.communicate(timeout=30)
        
        result = ""
        if stdout:
            result += stdout
        if stderr:
            result += stderr
        
        return result, process.returncode
        
    except subprocess.TimeoutExpired:
        process.kill()
        return "Command timed out after 30 seconds", 1
    except Exception as e:
        return str(e), 1
