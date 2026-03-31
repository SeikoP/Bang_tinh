"""
Tunnel Service — manage ngrok / Cloudflare Tunnel from within the app.

Supports two providers:
  • cloudflare  — zero-signup, fast (recommended)
  • ngrok       — needs free authtoken, wider compatibility

Both start a subprocess / library in a background thread and emit
Qt signals when the public URL is ready (or on error).
"""

from __future__ import annotations

import logging
import os
import platform
import re
import shutil
import subprocess
import sys
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QObject, QThread, pyqtSignal

logger = logging.getLogger(__name__)

# ─── helpers ────────────────────────────────────────────
CLOUDFLARED_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "cloudflared"
CLOUDFLARED_EXE = CLOUDFLARED_DIR / "cloudflared.exe"


def _find_cloudflared() -> Optional[str]:
    """Return path to cloudflared binary, or None."""
    # 1. Check our managed copy
    if CLOUDFLARED_EXE.is_file():
        return str(CLOUDFLARED_EXE)
    # 2. Check PATH
    which = shutil.which("cloudflared")
    if which:
        return which
    return None


def _download_cloudflared(progress_cb=None) -> str:
    """Download cloudflared for Windows and return path to exe."""
    import urllib.request

    CLOUDFLARED_DIR.mkdir(parents=True, exist_ok=True)

    arch = platform.machine().lower()
    if arch in ("amd64", "x86_64"):
        url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    elif arch in ("arm64", "aarch64"):
        url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-arm64.exe"
    else:
        url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-386.exe"

    logger.info("Downloading cloudflared from %s", url)
    if progress_cb:
        progress_cb("Đang tải cloudflared...")

    req = urllib.request.Request(url, headers={"User-Agent": "WMS/2.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = resp.read()

    CLOUDFLARED_EXE.write_bytes(data)
    logger.info("cloudflared saved to %s (%d KB)", CLOUDFLARED_EXE, len(data) // 1024)
    return str(CLOUDFLARED_EXE)


# ═══════════════════════════════════════════════════════
#  Cloudflare Tunnel Worker
# ═══════════════════════════════════════════════════════
class _CloudflareWorker(QThread):
    tunnel_ready = pyqtSignal(str)
    tunnel_error = pyqtSignal(str)
    tunnel_stopped = pyqtSignal()
    progress = pyqtSignal(str)

    # Regex to capture the .trycloudflare.com URL from cloudflared output
    _URL_RE = re.compile(r"(https://[a-z0-9\-]+\.trycloudflare\.com)")

    def __init__(self, port: int, parent=None):
        super().__init__(parent)
        self.port = port
        self._process: Optional[subprocess.Popen] = None
        self._should_stop = False

    def run(self):
        try:
            exe = _find_cloudflared()
            if not exe:
                self.progress.emit("Đang tải cloudflared lần đầu (~25 MB)...")
                exe = _download_cloudflared(progress_cb=lambda m: self.progress.emit(m))

            self.progress.emit("Đang khởi động Cloudflare Tunnel...")

            # Start cloudflared quick tunnel
            cmd = [exe, "tunnel", "--url", f"http://localhost:{self.port}"]
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )

            # cloudflared prints the URL to stderr
            url_found = False
            for line in iter(self._process.stderr.readline, b""):
                if self._should_stop:
                    break
                text = line.decode("utf-8", errors="replace").strip()
                if text:
                    logger.debug("cloudflared: %s", text)

                match = self._URL_RE.search(text)
                if match and not url_found:
                    url_found = True
                    public_url = match.group(1)
                    logger.info("Cloudflare tunnel: %s → localhost:%s", public_url, self.port)
                    self.tunnel_ready.emit(public_url)

                # Check for fatal errors
                if "ERR" in text and "tunnel" in text.lower() and not url_found:
                    self.tunnel_error.emit(f"Cloudflare: {text}")
                    return

            # If process ended without finding URL
            if not url_found and not self._should_stop:
                rc = self._process.wait()
                self.tunnel_error.emit(
                    f"cloudflared thoát với mã {rc}. Kiểm tra kết nối mạng."
                )

        except FileNotFoundError:
            self.tunnel_error.emit("Không tìm thấy cloudflared và không tải được.")
        except Exception as exc:
            self.tunnel_error.emit(f"Lỗi Cloudflare Tunnel: {exc}")
            logger.error("Cloudflare tunnel error: %s", exc, exc_info=True)
        finally:
            self._cleanup()
            self.tunnel_stopped.emit()

    def stop(self):
        self._should_stop = True
        self._cleanup()

    def _cleanup(self):
        proc = self._process
        if proc is None:
            return
        self._process = None
        # Close pipes first to unblock readline() in the run() thread
        try:
            if proc.stderr:
                proc.stderr.close()
        except Exception:
            pass
        try:
            if proc.stdout:
                proc.stdout.close()
        except Exception:
            pass
        # On Windows, terminate() may not be enough for cloudflared — use kill()
        if proc.poll() is None:
            try:
                proc.kill()
                proc.wait(timeout=5)
            except Exception:
                pass


# ═══════════════════════════════════════════════════════
#  Ngrok Tunnel Worker
# ═══════════════════════════════════════════════════════
class _NgrokWorker(QThread):
    tunnel_ready = pyqtSignal(str)
    tunnel_error = pyqtSignal(str)
    tunnel_stopped = pyqtSignal()
    progress = pyqtSignal(str)

    def __init__(self, port: int, authtoken: str = "", region: str = "", parent=None):
        super().__init__(parent)
        self.port = port
        self.authtoken = authtoken
        self.region = region
        self._tunnel = None
        self._should_stop = False

    def run(self):
        try:
            from pyngrok import conf, ngrok

            self.progress.emit("Đang khởi động ngrok...")

            if self.authtoken:
                conf.get_default().auth_token = self.authtoken
            if self.region:
                conf.get_default().region = self.region

            self._tunnel = ngrok.connect(self.port, "http")
            public_url: str = self._tunnel.public_url
            if public_url.startswith("http://"):
                public_url = public_url.replace("http://", "https://", 1)

            logger.info("ngrok tunnel: %s → localhost:%s", public_url, self.port)
            self.tunnel_ready.emit(public_url)

            while not self._should_stop:
                self.msleep(500)

        except ImportError:
            self.tunnel_error.emit("Chưa cài pyngrok. Chạy: pip install pyngrok")
        except Exception as exc:
            msg = str(exc)
            if "ERR_NGROK" in msg and "authtoken" in msg.lower():
                self.tunnel_error.emit(
                    "Thiếu authtoken ngrok.\n"
                    "Đăng ký tại https://dashboard.ngrok.com → dán token."
                )
            else:
                self.tunnel_error.emit(f"Lỗi ngrok: {msg}")
            logger.error("ngrok error: %s", exc, exc_info=True)

    def stop(self):
        self._should_stop = True
        try:
            from pyngrok import ngrok
            if self._tunnel:
                ngrok.disconnect(self._tunnel.public_url)
            ngrok.kill()
        except Exception as exc:
            logger.debug("ngrok cleanup: %s", exc)
        finally:
            self.tunnel_stopped.emit()


# ═══════════════════════════════════════════════════════
#  Unified TunnelService
# ═══════════════════════════════════════════════════════
PROVIDERS = ("cloudflare", "ngrok")


class TunnelService(QObject):
    """
    Unified tunnel manager.

    Signals
    -------
    tunnel_started(str)  — public HTTPS URL
    tunnel_stopped()
    tunnel_error(str)
    progress(str)        — status messages (downloading, connecting…)
    """

    tunnel_started = pyqtSignal(str)
    tunnel_stopped = pyqtSignal()
    tunnel_error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker: Optional[QThread] = None
        self._public_url: str = ""
        self._provider: str = ""

    @property
    def public_url(self) -> str:
        return self._public_url

    @property
    def is_running(self) -> bool:
        return self._worker is not None and self._worker.isRunning()

    @property
    def provider(self) -> str:
        return self._provider

    def start(self, port: int, provider: str = "cloudflare",
              authtoken: str = "", region: str = ""):
        if self.is_running:
            # Stop previous worker first
            self.stop()

        self._provider = provider

        if provider == "cloudflare":
            self._worker = _CloudflareWorker(port)
        elif provider == "ngrok":
            self._worker = _NgrokWorker(port, authtoken, region)
        else:
            self.tunnel_error.emit(f"Provider không hợp lệ: {provider}")
            return

        self._worker.tunnel_ready.connect(self._on_ready)
        self._worker.tunnel_error.connect(self._on_error)
        self._worker.tunnel_stopped.connect(self._on_stopped)
        self._worker.progress.connect(self.progress.emit)
        self._worker.start()

    def stop(self):
        if self._worker:
            self._worker.stop()
            if not self._worker.wait(5000):
                # Force terminate the thread if it didn't stop in time
                self._worker.terminate()
                self._worker.wait(2000)
            self._worker = None
        self._public_url = ""

    def _on_ready(self, url: str):
        self._public_url = url
        self.tunnel_started.emit(url)

    def _on_error(self, msg: str):
        self._public_url = ""
        self.tunnel_error.emit(msg)

    def _on_stopped(self):
        self._public_url = ""
        self.tunnel_stopped.emit()
