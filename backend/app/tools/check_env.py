import sys
import shutil
import subprocess
import socket
import urllib.request
import os

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class DummyColor:
        def __getattr__(self, name): return ""
    Fore = Style = DummyColor()

def print_status(name, status, is_ok, details=""):
    color = Fore.GREEN if is_ok else Fore.RED
    print(f"{name:20}: {color}{status}{Style.RESET_ALL} {details}")

def main():
    print("Environment Check")
    print("-" * 50)
    
    # Python
    print_status("Python", sys.version.split()[0], sys.version_info >= (3, 11))
    
    # Torch & GPU
    torch_ok = False
    try:
        import torch
        torch_ok = torch.cuda.is_available()
        gpu_name = torch.cuda.get_device_name(0) if torch_ok else "None"
        print_status("Torch/CUDA", f"{torch.__version__}, GPU: {gpu_name}", torch_ok)
    except ImportError:
        print_status("Torch/CUDA", "Not installed", False)
        
    # Ultralytics
    try:
        import ultralytics
        print_status("Ultralytics", ultralytics.__version__, True)
    except ImportError:
        print_status("Ultralytics", "Not installed", False)
        
    # FFmpeg / FFprobe
    def check_cmd(cmd, version_flag="-version"):
        try:
            exe = shutil.which(cmd) or cmd
            res = subprocess.run([exe, version_flag], capture_output=True, text=True, check=True)
            return res.stdout.split('\n')[0], True
        except Exception:
            return "Not found", False
            
    ffmpeg_v, ffmpeg_ok = check_cmd("ffmpeg")
    ffprobe_v, ffprobe_ok = check_cmd("ffprobe")
    print_status("FFmpeg", ffmpeg_v[:30] + "...", ffmpeg_ok)
    print_status("FFprobe", ffprobe_v[:30] + "...", ffprobe_ok)
    
    # Node / NPM
    node_v, node_ok = check_cmd("node", "--version")
    npm_v, npm_ok = check_cmd("npm", "--version")
    print_status("Node", node_v, node_ok)
    print_status("NPM", npm_v, npm_ok)
    
    # MediaMTX Reachable (RTSP 8554)
    try:
        with socket.create_connection(("127.0.0.1", 8554), timeout=2):
            pass
        print_status("MediaMTX (8554)", "Reachable", True)
    except OSError:
        print_status("MediaMTX (8554)", "Unreachable", False)
        
    # Cameras
    for cam in ["cam01", "cam02", "cam03"]:
        url = f"rtsp://127.0.0.1:8554/{cam}"
        try:
            res = subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams", url],
                                 capture_output=True, timeout=5)
            if res.returncode == 0:
                print_status(f"Camera {cam}", "Readable", True)
            else:
                print_status(f"Camera {cam}", "Failed (not running?)", False, res.stderr.decode().strip()[:50].replace('\n', ' '))
        except subprocess.TimeoutExpired:
            print_status(f"Camera {cam}", "Timeout", False)
        except Exception as e:
            print_status(f"Camera {cam}", "Error", False, str(e)[:50])
            
    # Free disk
    total, used, free = shutil.disk_usage(".")
    free_gb = free // (2**30)
    print_status("Free Disk", f"{free_gb} GB", free_gb > 10)
    
    # Download models
    models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/models"))
    os.makedirs(models_dir, exist_ok=True)
    models = ["yolo11s.pt", "yolo11n.pt"]
    base_url = "https://github.com/ultralytics/assets/releases/download/v8.3.0/"
    for m in models:
        path = os.path.join(models_dir, m)
        if not os.path.exists(path):
            print(f"Downloading {m} to {models_dir}...")
            try:
                urllib.request.urlretrieve(base_url + m, path)
                print_status(m, "Downloaded", True)
            except Exception as e:
                print_status(m, "Failed to download", False, str(e))
        else:
            print_status(m, "Already exists", True)
            
    # Overall status
    sys.exit(0 if (torch_ok and ffmpeg_ok) else 1)

if __name__ == "__main__":
    main()
