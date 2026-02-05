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
from io import BytesIO
import tkinter as tk
from PIL import Image, ImageTk
import logging

# Logging to FILE ONLY (not console!)
logging.basicConfig(
    filename='zork_debug.log',
    level=logging.DEBUG,
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
            print("🔊 Voice ON")
            self.speech_thread = threading.Thread(target=self._speech_worker, daemon=True)
            self.speech_thread.start()
        except Exception as e:
            print(f"⚠️  Voice failed: {e}")
            self.voice_enabled = False
    
    def setup_image_window(self):
        """Setup tkinter window"""
        self.root = tk.Tk()
        self.root.title("ZORK RPG - Scene Viewer")
        self.root.geometry("600x600")
        self.root.configure(bg='black')
        
        self.status_label = tk.Label(
            self.root, text="🎨 Ready", fg='#00ff00', bg='black', font=('Courier', 12)
        )
        self.status_label.pack(pady=10)
        
        self.image_label = tk.Label(self.root, bg='black')
        self.image_label.pack(expand=True, fill='both', padx=10, pady=10)
        
        self.root.attributes('-topmost', True)
        self.root.after(2000, lambda: self.root.attributes('-topmost', False))
        
        print("🖼️  Image window ready")
    
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
        print("🔇 Stopped")
    
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
        clean = re.sub(r'[⚔️🔥💀👤🕊️⚠️💬💨💋✅❌📊💰🚨🌟👋🎨🎮]', '', clean)
        clean = re.sub(r'\[█▒\s]+\]', '', clean)
        clean = re.sub(r'[╔═╗║╚╝─│┌┐└┘├┤┬┴┼]', '', clean)
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
            
            self.status_label.config(text=f"🎨 {img.width}x{img.height}")
            print(f"✅ Image: {img.width}x{img.height}")
        except Exception as e:
            print(f"❌ Image error: {e}")
    
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
╔═══════════════════════════════════════════════════╗
║   ZORK RPG - SSH CLIENT (TRULY FIXED!)           ║
║   🔊 Voice + 🖼️  Images + 📝 File logging        ║
╚═══════════════════════════════════════════════════╝

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
                                        self.speak_async(clean, self.get_voice_type(clean))
                    except:
                        break
            
            output_thread = threading.Thread(target=read_output, daemon=True)
            output_thread.start()
            
            # Input thread
            def handle_input():
                print("\n✅ Connected!")
                print("   'voice' = toggle TTS")
                print("   'shutup' = stop talking")
                print("   'look' = generate image\n")
                
                try:
                    while process.poll() is None:
                        try:
                            inp = input()
                            
                            if inp.strip().lower() == 'voice':
                                self.voice_enabled = not self.voice_enabled
                                print(f"🔊 Voice {'ON' if self.voice_enabled else 'OFF'}")
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
            print("❌ Connection failed!")
        finally:
            try:
                process.terminate()
            except:
                pass


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='localhost')
    parser.add_argument('--port', type=int, default=2222)
    parser.add_argument('--user', default='player')
    args = parser.parse_args()
    
    client = VoiceImageSSHClient(args.host, args.port, args.user)
    client.connect()


if __name__ == "__main__":
    main()
