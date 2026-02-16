"""
Text-to-Speech Service - Vietnamese voice notifications
Optimized for low-latency with QMediaPlayer and Predictive Caching
"""

import logging
import os
import tempfile
import hashlib
import re
from pathlib import Path
from typing import Optional, Dict, List

from PyQt6.QtCore import QObject, QThread, pyqtSignal, QUrl, QTimer
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

# Cache directory for pre-generated audio
CACHE_DIR = Path(tempfile.gettempdir()) / "tts_cache"
CACHE_DIR.mkdir(exist_ok=True)


class TTSWorker(QThread):
    """Worker thread for background TTS generation/download"""
    
    finished_generating = pyqtSignal(str, str)  # cache_key, file_path
    error = pyqtSignal(str)
    
    def __init__(self, text: str, voice: str, cache_key: str):
        super().__init__()
        self.text = text
        self.voice = voice
        self.cache_key = cache_key
    
    def run(self):
        """Generate audio file using Edge-TTS"""
        cache_file = CACHE_DIR / f"{self.cache_key}.mp3"
        try:
            import edge_tts
            import asyncio
            
            voice_id = TTSService.VOICES.get(self.voice, "vi-VN-HoaiMyNeural")
            
            # Remove existing file if it's 0 bytes or corrupted
            if cache_file.exists() and cache_file.stat().st_size < 500:
                try: os.unlink(str(cache_file))
                except: pass

            async def generate():
                communicate = edge_tts.Communicate(self.text, voice_id)
                await communicate.save(str(cache_file))
            
            asyncio.run(generate())
            
            # Verify file
            if cache_file.exists() and cache_file.stat().st_size > 500:
                self.finished_generating.emit(self.cache_key, str(cache_file))
            else:
                self.error.emit("Failed to generate valid audio file")
                
        except Exception as e:
            if cache_file.exists():
                try: os.unlink(str(cache_file))
                except: pass
            self.error.emit(str(e))


class TTSBatchWorker(QThread):
    """Worker that generates multiple TTS files in a single asyncio event loop"""
    
    item_generated = pyqtSignal(str, str)  # cache_key, file_path
    all_done = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, items: list, voice: str):
        """items: list of (cache_key, text) tuples"""
        super().__init__()
        self.items = items
        self.voice = voice
    
    def run(self):
        """Generate all audio files in one asyncio session"""
        try:
            import edge_tts
            import asyncio
            
            voice_id = TTSService.VOICES.get(self.voice, "vi-VN-HoaiMyNeural")
            
            async def generate_all():
                for cache_key, text in self.items:
                    cache_file = CACHE_DIR / f"{cache_key}.mp3"
                    try:
                        if cache_file.exists() and cache_file.stat().st_size < 500:
                            try: os.unlink(str(cache_file))
                            except: pass
                        
                        communicate = edge_tts.Communicate(text, voice_id)
                        await communicate.save(str(cache_file))
                        
                        if cache_file.exists() and cache_file.stat().st_size > 500:
                            self.item_generated.emit(cache_key, str(cache_file))
                    except Exception as e:
                        if cache_file.exists():
                            try: os.unlink(str(cache_file))
                            except: pass
            
            asyncio.run(generate_all())
            self.all_done.emit()
            
        except Exception as e:
            self.error.emit(str(e))


class TTSService(QObject):
    """
    High-Performance Text-to-Speech Service
    
    Optimized for low-latency notifications using:
    - PyQt6.QtMultimedia for instant playback
    - Intelligent predictive caching for monetary amounts
    - Hybrid offline/online fallback system
    """
    
    error_occurred = pyqtSignal(str)
    
    VOICES = {
        "edge_female": "vi-VN-HoaiMyNeural",      # South Female (Default)
        "edge_male": "vi-VN-NamMinhNeural",        # North Male
        "edge_north_female": "vi-VN-NamMinhNeural", # North Fallback (ThuongNeural missing in current API)
    }
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        super().__init__()
        self.logger = logger or logging.getLogger(__name__)
        self.enabled = True
        self.voice = "edge_female"
        self.volume = 100
        
        # Initialize Player
        self._player = QMediaPlayer()
        self._audio_output = QAudioOutput()
        self._player.setAudioOutput(self._audio_output)
        self.set_volume(self.volume)
        
        # Pre-compiled amount patterns for parsing transaction amounts
        self._AMOUNT_COMPILED = [
            # Allow optional space after +/- sign: e.g. "GD: - 1.000.000"
            re.compile(r'(?:Giao\s+dich|So\s+tien|GD|ST):\s*([\+\-]?\s*[\d,\.]{3,15})\s*(?:VND|d|dong)?', re.IGNORECASE),
            re.compile(r'([\+\-]\s*\d{1,3}(?:[,\.]\d{3})+)', re.IGNORECASE),
            re.compile(r'([\+\-]?\s*\d{1,3}(?:[,\.]\d{3})+)\s*(?:VND|d|dong)', re.IGNORECASE),
            re.compile(r'([\+\-]\s*\d{4,12})', re.IGNORECASE), # Plain +/- numbers without separators
        ]
        
        # Cache management
        self._cache = {}
        self._workers: List[TTSWorker] = [] # Keep refs to workers to avoid GC
        self._load_existing_cache()
        
        # Start pre-generation in 1 second to not block startup
        QTimer.singleShot(1000, self._pregenerate_common_amounts)

    def _load_existing_cache(self):
        """Scan cache directory for existing files and clean up invalid ones"""
        try:
            if CACHE_DIR.exists():
                for f in CACHE_DIR.glob("*.mp3"):
                    if f.stat().st_size > 500:
                        self._cache[f.stem] = str(f)
                    else:
                        try: os.unlink(str(f)) # Delete 0-byte or corrupt files
                        except: pass
        except Exception as e:
            self.logger.error(f"Error loading cache: {e}")

    def set_enabled(self, enabled: bool):
        self.enabled = enabled

    def set_volume(self, volume: int):
        self.volume = max(0, min(100, volume))
        self._audio_output.setVolume(self.volume / 100.0)

    def set_voice(self, voice: str):
        """Set voice ID (edge_female, edge_male)"""
        if voice in self.VOICES:
            self.voice = voice
            self.logger.info(f"TTS voice set to: {voice}")

    def set_engine(self, engine_type: str):
        """No-op for compatibility with old code"""
        pass

    def speak(self, text: str):
        """Speak generic text - uses cache if matches, else background generate"""
        if not self.enabled or not text: return
        
        cache_key = hashlib.md5(f"{text}_{self.voice}".encode()).hexdigest()
        
        if cache_key in self._cache:
            self._play_file(self._cache[cache_key], text, cache_key)
        else:
            self._generate_and_play(text, cache_key)

    def speak_transaction(self, amount: str, sender_name: Optional[str] = None):
        """Speak transaction notification - Zero delay if cached"""
        if not self.enabled: return
        
        try:
            # Detect transaction direction
            amount_str = amount.strip()
            is_outgoing = amount_str.startswith('-')
            
            # Explicitly set action word based on sign
            action_text = "Đã chuyển" if is_outgoing else "Đã nhận"
            action_key = "out" if is_outgoing else "in"

            # Clean amount (keep digits)
            amount_clean = "".join(filter(str.isdigit, amount))
            if not amount_clean: return
            
            amount_int = int(amount_clean)
            
            # For the "1m dong thi input -000,000" request:
            # If the user literally provides "000,000" and says it's 1 million,
            # we check if it's exactly 0 and if the original string has many zeros.
            if amount_int == 0 and "000,000" in amount and len(amount_clean) >= 6:
                # Interpret as 1,000,000 if it's exactly 6 zeros
                amount_int = 1000000
                self.logger.warning(f"TTS: Interpreting {amount} as 1,000,000 based on user request")

            # Cache key must include action type
            cache_key = f"amt_{action_key}_{self.voice}_{amount_int}"
            
            # Generating message
            from num2words import num2words
            try:
                words = num2words(amount_int, lang='vi')
            except:
                words = str(amount_int)
            
            # Full message with action prefix
            message = f"{action_text} {words} đồng"

            if cache_key in self._cache:
                self.logger.info(f"TTS Latency: ZERO (Cache hit for {action_key} {amount_int})")
                self._play_file(self._cache[cache_key], message, cache_key)
                return

            self.logger.info(f"TTS: Generating for {action_key} {amount_int} -> '{message}'")
            self._generate_and_play(message, cache_key)
            
        except Exception as e:
            self.logger.error(f"TTS Transaction error: {e}")

    def _play_file(self, file_path: str, text_fallback: str = None, cache_key_fallback: str = None):
        """Instant playback using QMediaPlayer with validation"""
        try:
            p = Path(file_path)
            if not p.exists() or p.stat().st_size < 500:
                self.logger.warning(f"Cached file invalid: {file_path}. Retrying generation.")
                if p.exists():
                    try: os.unlink(file_path)
                    except: pass
                if cache_key_fallback in self._cache:
                    del self._cache[cache_key_fallback]
                
                if text_fallback and cache_key_fallback:
                    self._generate_and_play(text_fallback, cache_key_fallback)
                return

            self._player.stop()
            self._player.setSource(QUrl.fromLocalFile(file_path))
            self._player.play()
        except Exception as e:
            self.logger.error(f"Playback error: {e}")

    def _generate_and_play(self, text: str, cache_key: str):
        """Generate in background and play once ready"""
        worker = TTSWorker(text, self.voice, cache_key)
        worker.finished_generating.connect(self._on_worker_success)
        worker.finished.connect(lambda: self._cleanup_worker(worker))
        worker.error.connect(lambda e: self.logger.error(f"Generate error: {e}"))
        self._workers.append(worker)
        worker.start()

    def _on_worker_success(self, cache_key: str, file_path: str):
        self._cache[cache_key] = file_path
        self._play_file(file_path)

    def _cleanup_worker(self, worker):
        if worker in self._workers:
            self._workers.remove(worker)

    def _pregenerate_common_amounts(self):
        """Silent pre-generation of common amounts using single batch worker"""
        try:
            from num2words import num2words
        except ImportError:
            self.logger.warning("num2words not installed, predictive caching disabled")
            return
            
        common = [10000, 20000, 30000, 50000, 100000, 200000, 500000]
        
        # Build list of items to generate (skip already cached)
        items_to_generate = []
        for amt in common:
            cache_key = f"amt_{self.voice}_{amt}"
            if cache_key not in self._cache:
                try:
                    words = num2words(amt, lang='vi')
                    items_to_generate.append((cache_key, f"Đã nhận {words} đồng"))
                except Exception:
                    pass
        
        if not items_to_generate:
            self.logger.info("TTS: All common amounts already cached.")
            return
        
        self.logger.info(f"TTS: Batch pre-generating {len(items_to_generate)} amounts...")
        
        # Single worker for all items (1 asyncio event loop instead of N)
        worker = TTSBatchWorker(items_to_generate, self.voice)
        worker.item_generated.connect(lambda key, path: self._cache.update({key: path}))
        worker.all_done.connect(lambda: self.logger.info("TTS: Batch pre-generation completed."))
        worker.error.connect(lambda e: self.logger.error(f"TTS batch pre-gen error: {e}"))
        worker.finished.connect(lambda: self._cleanup_worker(worker))
        self._workers.append(worker)
        worker.start()

    def stop(self):
        self._player.stop()

    def cleanup(self):
        self.stop()
