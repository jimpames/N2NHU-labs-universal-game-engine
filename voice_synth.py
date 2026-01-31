#!/usr/bin/env python3
"""
Text-to-Speech Module for ZORK RPG
Uses Windows built-in speech synthesis - NO API costs!
"""

import subprocess
import platform
import re


class VoiceSynthesizer:
    """Text-to-speech using system voices"""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.system = platform.system()
        
        # Voice profiles for different entity types
        self.voice_profiles = {
            'narrator': {'rate': 0, 'volume': 80},
            'player': {'rate': 1, 'volume': 90},
            'troll': {'rate': -2, 'volume': 100},
            'goblin': {'rate': 3, 'volume': 80},
            'dragon': {'rate': -4, 'volume': 100},
            'merchant': {'rate': 1, 'volume': 85},
            'default': {'rate': 0, 'volume': 85}
        }
    
    def speak(self, text: str, voice_type: str = 'narrator'):
        """Speak text using system TTS"""
        if not self.enabled:
            return
        
        # Clean text for speech
        clean_text = self._clean_text(text)
        
        if not clean_text:
            return
        
        # Get voice settings
        profile = self.voice_profiles.get(voice_type, self.voice_profiles['default'])
        
        if self.system == 'Windows':
            self._speak_windows(clean_text, profile)
        elif self.system == 'Darwin':  # macOS
            self._speak_macos(clean_text, profile)
        elif self.system == 'Linux':
            self._speak_linux(clean_text, profile)
    
    def _clean_text(self, text: str) -> str:
        """Clean text for better speech output"""
        # Remove color codes, special characters
        clean = re.sub(r'\x1b\[[0-9;]*m', '', text)
        
        # Remove emoji and unicode symbols
        clean = re.sub(r'[⚔️🔥💀👤🕊️⚠️💬💨👋✅❌📊💰🚨]', '', clean)
        
        # Remove health bars
        clean = re.sub(r'\[█░]+\]', '', clean)
        
        # Remove multiple spaces
        clean = re.sub(r'\s+', ' ', clean)
        
        # Remove command prompts
        clean = re.sub(r'^>\s*', '', clean)
        
        return clean.strip()
    
    def _speak_windows(self, text: str, profile: dict):
        """Speak using Windows SAPI"""
        rate = profile['rate']
        volume = profile['volume']
        
        # Build PowerShell command
        ps_command = f"""
        Add-Type -AssemblyName System.Speech;
        $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer;
        $synth.Rate = {rate};
        $synth.Volume = {volume};
        $synth.Speak('{text.replace("'", "''")}');
        """
        
        try:
            subprocess.Popen(
                ['powershell', '-Command', ps_command],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception as e:
            print(f"Voice synthesis error: {e}")
    
    def _speak_macos(self, text: str, profile: dict):
        """Speak using macOS 'say' command"""
        rate = 200 + (profile['rate'] * 20)  # Convert to words per minute
        
        try:
            subprocess.Popen(
                ['say', '-r', str(rate), text],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception as e:
            print(f"Voice synthesis error: {e}")
    
    def _speak_linux(self, text: str, profile: dict):
        """Speak using Linux espeak/festival"""
        try:
            # Try espeak first
            subprocess.Popen(
                ['espeak', text],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except FileNotFoundError:
            try:
                # Fall back to festival
                subprocess.Popen(
                    ['festival', '--tts'],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                ).communicate(text.encode())
            except Exception as e:
                print(f"Voice synthesis error: {e}")
    
    def toggle(self):
        """Toggle voice on/off"""
        self.enabled = not self.enabled
        return self.enabled


# Convenience function
def speak(text: str, voice_type: str = 'narrator'):
    """Quick speak function"""
    synth = VoiceSynthesizer()
    synth.speak(text, voice_type)


if __name__ == "__main__":
    # Test voices
    synth = VoiceSynthesizer()
    
    print("Testing narrator voice...")
    synth.speak("Welcome to the dungeon. What will you do?", 'narrator')
    
    print("Testing troll voice...")
    synth.speak("Me smash! Give gold!", 'troll')
    
    print("Testing goblin voice...")
    synth.speak("Hehe! Shiny things! Mine!", 'goblin')
    
    print("Testing dragon voice...")
    synth.speak("You dare disturb my slumber, mortal?", 'dragon')
