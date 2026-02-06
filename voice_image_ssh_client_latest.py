#!/usr/bin/env python3
"""
ZORK RPG - SSH Voice + Image Client
TRULY FIXED VERSION - All Jim's issues resolved!
"""

import subprocess
import pyttsx3
import sys
import threading
import re
import queue
import base64
import os
from io import BytesIO
from pathlib import Path
import tkinter as tk
from PIL import Image, ImageTk
import logging


# ============================================================
# PATH CONFIGURATION - Program Files Support
# ============================================================
def get_app_paths():
    """
    Determine proper paths for installed vs development mode.
    
    When running as compiled EXE:
    - Reads config from install directory (e.g., Program Files)
    - Writes logs/data to user AppData folder
    
    When running as Python script:
    - Uses current directory for everything
    """
    if getattr(sys, 'frozen', False):
        # Running as compiled EXE
        install_dir = Path(sys.executable).parent
        app_data = Path(os.environ['APPDATA']) / 'ZORK_RPG'
        
        # Create writable directories
        app_data.mkdir(parents=True, exist_ok=True)
        (app_data / 'logs').mkdir(exist_ok=True)
        
        return {
            'config': install_dir / 'config',      # Read-only
            'data': app_data,                       # Writable
            'logs': app_data / 'logs',              # Writable
        }
    else:
        # Running as script - everything local
        base = Path(__file__).parent
        return {
            'config': base / 'config',
            'data': base,
            'logs': base,
        }

# Initialize paths globally
APP_PATHS = get_app_paths()


# ============================================================
# Logging Configuration
# ============================================================
# Logging to FILE ONLY (not console!) - in AppData
logging.basicConfig(
    filename=str(APP_PATHS['logs'] / 'zork_debug.log'),
    level=logging.WARNING,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class VoiceImageSSHClient:
    """SSH client - FIXED: images show instantly, shutup works, no log spam"""
    
    def __init__(self, host='localhost', port=2222, username='player'):
        self.host = host
        self.port = port
        self.username = username
        self.voice_enabled = True
        self.stop_speaking = threading.Event()
        
        self.speech_queue = queue.Queue()
        self.image_queue = queue.Queue()
        
        self.root = None
        self.image_label = None
        self.status_label = None
        self.setup_image_window()
        
        # Init voice
        try:
            test = pyttsx3.init()
            test.stop()
            del test
            print("ðŸ”Š Voice ON")
            self.speech_thread = threading.Thread(target=self._speech_worker, daemon=True)
            self.speech_thread.start()
        except Exception as e:
            print(f"âš ï¸  Voice failed: {e}")
            self.voice_enabled = False
    
    def setup_image_window(self):
        """Setup tkinter window"""
        self.root = tk.Tk()
        self.root.title("ZORK RPG - Scene Viewer")
        self.root.geometry("600x600")
        self.root.configure(bg='black')
        
        self.status_label = tk.Label(
            self.root, text="ðŸŽ¨ Ready", fg='#00ff00', bg='black', font=('Courier', 12)
        )
        self.status_label.pack(pady=10)
        
        self.image_label = tk.Label(self.root, bg='black')
        self.image_label.pack(expand=True, fill='both', padx=10, pady=10)
        
        self.root.attributes('-topmost', True)
        self.root.after(2000, lambda: self.root.attributes('-topmost', False))
        
        print("ðŸ–¼ï¸  Image window ready")
    
    def _speech_worker(self):
        """TTS worker - can be interrupted by shutup"""
        while True:
            try:
                if self.stop_speaking.is_set():
                    # Clear queue
                    while not self.speech_queue.empty():
                        try:
                            self.speech_queue.get_nowait()
                        except:
                            pass
                    self.stop_speaking.clear()
                    continue
                
                text, voice_type = self.speech_queue.get(timeout=0.5)
                
                if not self.voice_enabled or self.stop_speaking.is_set():
                    continue
                
                clean = self.clean_text(text)
                if len(clean) < 3:
                    continue
                
                rates = {'narrator': 150, 'troll': 110, 'goblin': 200, 'dragon': 100, 'merchant': 160}
                rate = rates.get(voice_type, 150)
                
                try:
                    engine = pyttsx3.init()
                    engine.setProperty('rate', rate)
                    engine.setProperty('volume', 0.85)
                    engine.say(clean)
                    engine.runAndWait()
                    engine.stop()
                    del engine
                except:
                    pass
                
            except queue.Empty:
                continue
            except:
                pass
    
    def shutup(self):
        """Stop speech immediately"""
        self.stop_speaking.set()
        print("ðŸ”‡ Stopped")
    
    def speak_async(self, text, voice_type='narrator'):
        """Queue for TTS"""
        if self.voice_enabled:
            try:
                self.speech_queue.put((text, voice_type), block=False)
            except:
                pass
    
    def clean_text(self, text):
        """Clean for speech"""
        clean = re.sub(r'\x1b\[[0-9;]*m', '', text)
        clean = re.sub(r'[âš”ï¸ðŸ”¥ðŸ’€ðŸ‘¤ðŸ•Šï¸âš ï¸ðŸ’¬ðŸ’¨ðŸ’‹âœ…âŒðŸ“ŠðŸ’°ðŸš¨ðŸŒŸðŸ‘‹ðŸŽ¨ðŸŽ®]', '', clean)
        clean = re.sub(r'\[â–ˆâ–’\s]+\]', '', clean)
        clean = re.sub(r'[â•”â•â•—â•‘â•šâ•â”€â”‚â”Œâ”â””â”˜â”œâ”¤â”¬â”´â”¼]', '', clean)
        clean = re.sub(r'\s+', ' ', clean).strip()
        if clean and all(c in '=-_' for c in clean):
            clean = ''
        return clean
    
    def get_voice_type(self, text):
        """Get voice type"""
        t = text.lower()
        if 'troll' in t:
            return 'troll'
        elif 'goblin' in t:
            return 'goblin'
        elif 'dragon' in t:
            return 'dragon'
        elif 'merchant' in t:
            return 'merchant'
        return 'narrator'
    
    def display_image_on_main_thread(self, base64_data):
        """Display image on main thread"""
        try:
            img_bytes = base64.b64decode(base64_data)
            img = Image.open(BytesIO(img_bytes))
            img.thumbnail((580, 550), Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(img)
            self.image_label.config(image=photo)
            self.image_label.image = photo
            
            self.status_label.config(text=f"ðŸŽ¨ {img.width}x{img.height}")
            print(f"âœ… Image: {img.width}x{img.height}")
        except Exception as e:
            print(f"âŒ Image error: {e}")
    
    def check_image_queue(self):
        """Check image queue - main thread"""
        try:
            data = self.image_queue.get_nowait()
            self.display_image_on_main_thread(data)
        except queue.Empty:
            pass
        self.root.after(50, self.check_image_queue)
    
    def queue_image(self, data):
        """Queue image from SSH thread"""
        try:
            self.image_queue.put(data, block=False)
        except:
            pass
    
    def connect(self):
        """Connect to SSH"""
        print(f"""
â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
â•‘   ZORK RPG - SSH CLIENT (TRULY FIXED!)           â•‘
â•‘   ðŸ”Š Voice + ðŸ–¼ï¸  Images + ðŸ“ File logging        â•‘
â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

Connecting to {self.host}:{self.port}...
Log file: zork_debug.log
""")
        
        ssh_cmd = ['ssh', '-p', str(self.port), '-o', 'StrictHostKeyChecking=no',
                   '-o', 'UserKnownHostsFile=NUL', '-o', 'LogLevel=ERROR',
                   '-T', f'{self.username}@{self.host}']
        
        try:
            process = subprocess.Popen(
                ssh_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, encoding='utf-8', errors='ignore',
                bufsize=0, universal_newlines=True
            )
            
            # Read thread - character by character for instant response!
            def read_output():
                buffer = ""
                while True:
                    try:
                        char = process.stdout.read(1)
                        if not char:
                            break
                        
                        buffer += char
                        
                        # Extract images IMMEDIATELY
                        while '\x1b]IMAGE;' in buffer and '\x1b\\' in buffer:
                            start = buffer.find('\x1b]IMAGE;')
                            end = buffer.find('\x1b\\', start)
                            
                            if end > start:
                                b64 = buffer[start+len('\x1b]IMAGE;'):end]
                                self.queue_image(b64)
                                buffer = buffer[:start] + buffer[end+2:]
                            else:
                                break
                        
                        # Process lines
                        while '\n' in buffer:
                            line, buffer = buffer.split('\n', 1)
                            
                            if line.strip():
                                clean = re.sub(r'\x1b\][^\x1b]*\x1b\\', '', line)
                                
                                if clean.strip():
                                    print(clean)  # CLEAN CONSOLE!
                                
                                # TTS
                                if clean.strip() != '>' and len(clean.strip()) > 2:
                                    skip = any(p in clean.lower() for p in ['image', 'connected'])
                                    if not skip:
                                        logger.debug(f"TTS QUEUE: {repr(clean[:100])}")
                                        self.speak_async(clean, self.get_voice_type(clean))
                    except:
                        break
            
            output_thread = threading.Thread(target=read_output, daemon=True)
            output_thread.start()
            
            # Input thread
            def handle_input():
                print("\nâœ… Connected!")
                print("   'voice' = toggle TTS")
                print("   'shutup' = stop talking")
                print("   'look' = generate image\n")
                
                try:
                    while process.poll() is None:
                        try:
                            inp = input()
                            
                            if inp.strip().lower() == 'voice':
                                self.voice_enabled = not self.voice_enabled
                                print(f"ðŸ”Š Voice {'ON' if self.voice_enabled else 'OFF'}")
                                continue
                            
                            if inp.strip().lower() == 'shutup':
                                self.shutup()
                                continue
                            
                            process.stdin.write(inp + '\n')
                            process.stdin.flush()
                        except:
                            break
                except KeyboardInterrupt:
                    print("\nBye!")
                finally:
                    process.terminate()
            
            input_thread = threading.Thread(target=handle_input, daemon=True)
            input_thread.start()
            
            # Image checker
            self.root.after(50, self.check_image_queue)
            
            # Tkinter mainloop
            self.root.mainloop()
            
        except:
            print("âŒ Connection failed!")
        finally:
            try:
                process.terminate()
            except:
                pass


def main():
    import argparse
    import configparser
    
    # Read config file if exists - from install directory or AppData
    config_file = APP_PATHS['config'] / 'client.ini'
    default_host = 'localhost'
    default_port = 2222
    default_user = 'player'
    
    if config_file.exists():
        try:
            config = configparser.ConfigParser()
            config.read(config_file)
            
            if 'server' in config:
                default_host = config['server'].get('ip', default_host)
                default_port = config['server'].getint('port', default_port)
                default_user = config['server'].get('username', default_user)
                print(f"📡 Config loaded: {default_host}:{default_port}")
        except Exception as e:
            print(f"⚠️  Config error: {e}, using defaults")
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default=default_host, help='Server IP address')
    parser.add_argument('--port', type=int, default=default_port, help='Server port')
    parser.add_argument('--user', default=default_user, help='Username')
    args = parser.parse_args()
    
    client = VoiceImageSSHClient(args.host, args.port, args.user)
    client.connect()


if __name__ == "__main__":
    main()
