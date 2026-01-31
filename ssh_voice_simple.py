#!/usr/bin/env python3
"""
ZORK RPG - SSH Voice Client (Simple Version)
Uses subprocess + pyttsx3 for voice
Works with passwordless SSH server!
"""

import subprocess
import pyttsx3
import sys
import threading
import re
import time
import queue


class SimpleVoiceSSHClient:
    """Simple SSH client with local voice using subprocess"""
    
    def __init__(self, host='localhost', port=2222, username='player'):
        self.host = host
        self.port = port
        self.username = username
        self.voice_enabled = True
        
        # Speech queue for single-threaded processing
        self.speech_queue = queue.Queue()
        
        # Test voice engine at startup
        try:
            test_engine = pyttsx3.init()
            test_engine.stop()
            del test_engine
            print("🔊 Voice synthesis initialized!")
            
            # Start speech worker thread
            self.speech_thread = threading.Thread(target=self._speech_worker, daemon=True)
            self.speech_thread.start()
            
        except Exception as e:
            print(f"⚠️  Voice synthesis failed: {e}")
            self.voice_enabled = False
    
    def _speech_worker(self):
        """Worker thread that processes speech queue"""
        while True:
            try:
                # Get next speech item from queue
                text, voice_type = self.speech_queue.get(timeout=1)
                
                if not self.voice_enabled:
                    continue
                
                # Clean text
                clean = self.clean_text(text)
                
                if len(clean) < 3:
                    continue
                
                # Set voice rate
                rates = {
                    'narrator': 150,
                    'troll': 110,
                    'goblin': 200,
                    'dragon': 100,
                    'merchant': 160
                }
                rate = rates.get(voice_type, 150)
                
                # Create FRESH engine for each speech to avoid hanging
                try:
                    engine = pyttsx3.init()
                    engine.setProperty('rate', rate)
                    engine.setProperty('volume', 85)
                    engine.say(clean)
                    engine.runAndWait()
                    engine.stop()
                    del engine
                except:
                    pass  # Silently ignore speech errors
                
            except queue.Empty:
                continue
            except Exception as e:
                pass  # Silently ignore errors
    
    def speak_async(self, text, voice_type='narrator'):
        """Queue text for speaking"""
        if not self.voice_enabled:
            return
        
        # Add to queue
        try:
            self.speech_queue.put((text, voice_type), block=False)
        except queue.Full:
            pass  # Skip if queue is full
    
    def clean_text(self, text):
        """Clean text for speech"""
        # Remove emoji
        clean = re.sub(r'[⚔️🔥💀👤🕊️⚠️💬💨👋✅❌📊💰🚨]', '', text)
        # Remove health bars
        clean = re.sub(r'\[█░]+\]', '', clean)
        # Remove ANSI codes
        clean = re.sub(r'\x1b\[[0-9;]*m', '', clean)
        # Remove box drawing characters
        clean = re.sub(r'[╔╗╚╝═║]', '', clean)
        # Remove prompts at start of line
        clean = re.sub(r'^>\s*', '', clean)
        # Remove multiple spaces
        clean = re.sub(r'\s+', ' ', clean)
        # Remove separator lines (but not from within text)
        if clean.strip() and all(c in '=-_' for c in clean.strip()):
            return ''
        return clean.strip()
    
    def get_voice_type(self, text):
        """Determine voice type from text"""
        text_lower = text.lower()
        if 'troll' in text_lower and any(w in text_lower for w in ['says', 'roars', 'attacks']):
            return 'troll'
        elif 'goblin' in text_lower:
            return 'goblin'
        elif 'dragon' in text_lower:
            return 'dragon'
        elif 'merchant' in text_lower:
            return 'merchant'
        return 'narrator'
    
    def connect(self):
        """Connect to SSH server with voice"""
        print(f"""
╔════════════════════════════════════════════════╗
║   ZORK RPG - SSH CLIENT WITH LOCAL VOICE      ║
║        🔊 Voice plays on YOUR speakers!       ║
╚════════════════════════════════════════════════╝

Connecting to {self.host}:{self.port} as {self.username}...
""")
        
        # Build SSH command
        # -o StrictHostKeyChecking=no - don't ask about host keys
        # -o UserKnownHostsFile=NUL - don't save host keys  
        # -o LogLevel=ERROR - suppress warnings
        # -T - disable pseudo-terminal allocation
        ssh_cmd = [
            'ssh',
            '-p', str(self.port),
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=NUL',
            '-o', 'LogLevel=ERROR',
            '-T',
            f'{self.username}@{self.host}'
        ]
        
        print("Starting SSH connection...")
        print("(Press Ctrl+C to disconnect)")
        print("-" * 50)
        
        try:
            # Start SSH process with proper encoding
            process = subprocess.Popen(
                ssh_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                encoding='utf-8',
                errors='ignore',  # Ignore bad characters
                bufsize=1,
                universal_newlines=True
            )
            
            # Thread to read output
            def read_output():
                for line in iter(process.stdout.readline, ''):
                    if line:
                        # Print to screen
                        print(line, end='', flush=True)
                        
                        # Only skip SSH system messages - speak everything else!
                        skip_patterns = [
                            'pseudo-terminal',
                            'warning:',
                            'permanently added',
                            'known hosts'
                        ]
                        
                        line_lower = line.lower().strip()
                        should_skip = any(pattern in line_lower for pattern in skip_patterns)
                        
                        # Also skip empty lines
                        if not line.strip():
                            should_skip = True
                        
                        # Speak everything else!
                        if not should_skip:
                            voice_type = self.get_voice_type(line)
                            self.speak_async(line, voice_type)
            
            output_thread = threading.Thread(target=read_output, daemon=True)
            output_thread.start()
            
            # Read user input
            print("\n✅ Connected! Voice is ENABLED!")
            print("   Type 'voice' to toggle voice on/off\n")
            
            try:
                while process.poll() is None:
                    try:
                        user_input = input()
                        
                        # Handle voice toggle locally
                        if user_input.strip().lower() == 'voice':
                            self.voice_enabled = not self.voice_enabled
                            status = "ENABLED" if self.voice_enabled else "DISABLED"
                            print(f"🔊 Voice {status}")
                            continue
                        
                        # Send to server
                        process.stdin.write(user_input + '\n')
                        process.stdin.flush()
                        
                    except EOFError:
                        break
            except KeyboardInterrupt:
                print("\n\nDisconnecting...")
            
            process.terminate()
            process.wait(timeout=2)
            
        except FileNotFoundError:
            print("\n❌ ERROR: 'ssh' command not found!")
            print("\nInstall OpenSSH:")
            print("  Windows 10/11: Settings → Apps → Optional Features → OpenSSH Client")
            print("  Or download from: https://www.openssh.com/")
        except Exception as e:
            print(f"\n❌ Connection error: {e}")
            print("\nMake sure:")
            print("1. Server is running: python ssh_server_multiplayer_rpg.py")
            print(f"2. OpenSSH client is installed")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ZORK RPG SSH Voice Client')
    parser.add_argument('--host', default='localhost', help='Server host')
    parser.add_argument('--port', type=int, default=2222, help='Server port')
    parser.add_argument('--user', default='player', help='Username')
    
    args = parser.parse_args()
    
    client = SimpleVoiceSSHClient(
        host=args.host,
        port=args.port,
        username=args.user
    )
    
    client.connect()


if __name__ == "__main__":
    main()
