#!/usr/bin/env python3
# -*- coding: utf-8 -*-




































import argparse
import array
import base64
import hashlib
import json
import math
import operator
import os
import re
import shutil
import signal
import socket
import ssl
import struct
import subprocess
import sys
import tempfile
import threading
import time

try:
    from urllib.parse import quote, urlsplit
    import urllib.request
    import urllib.error
except ImportError:
    raise

VERSION = "1.0.0"
LABEL = "Gemini 3.5 Transcribe Live"
MODEL_ID = "gemini-live"

CLOUD_BASE = os.environ.get("FLEX_AI_BASE", "https://www.captureflex.in").rstrip("/")
LIVE_PATH = os.environ.get("FLEX_AI_LIVE_PATH", "/api/transcribe-live")

GOOGLE_WS = ("wss://generativelanguage.googleapis.com/ws/"
             "google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent")
GOOGLE_MODEL = "models/gemini-3.5-transcribe-live"

RATE = 16000
CHUNK_MS = 100
SESSION_SECONDS = 540.0





WANT_SESSION_SECONDS = 60.0
BURST_SECONDS = 15.0
MAX_PARALLEL = 4
MAX_REFRESHES = 3


def _env_float(name, default):
    raw = str(os.environ.get(name, "") or "").strip().lower()
    if raw in ("", "default"):
        return default
    if raw in ("max", "fast", "unlimited", "inf"):
        return 0.0
    try:
        value = float(raw)
        return value if value == value and value >= 0 else default
    except ValueError:
        return default







_PRINT_LOCK = threading.Lock()
_SECRET_LOCK = threading.Lock()
_SECRETS = set()


def _secret(value):
    value = str(value or "").strip()
    if len(value) >= 6:
        with _SECRET_LOCK:
            _SECRETS.add(value)
            _SECRETS.add(quote(value, safe=""))
    return value


def _redact(text):
    text = str(text)
    with _SECRET_LOCK:
        known = sorted(_SECRETS, key=len, reverse=True)
    for value in known:
        if value and value in text:
            text = text.replace(value, "***")

    text = re.sub(r"(?i)\b(access_token|key|token)=([^&\s\"']+)", r"\1=***", text)
    text = re.sub(r"auth_tokens/[A-Za-z0-9_\-\.]+", "auth_tokens/***", text)
    return text


def say(message=""):
    text = _redact(message)
    with _PRINT_LOCK:
        try:
            sys.stdout.write(text + "\n")
        except UnicodeEncodeError:
            enc = getattr(sys.stdout, "encoding", None) or "ascii"
            sys.stdout.write(text.encode(enc, "replace").decode(enc, "replace") + "\n")
        try:
            sys.stdout.flush()
        except Exception:
            pass


def stage(name, pct=None, detail=""):

    detail = re.sub(r"[^\x20-\x7e]", "", str(detail or "")).replace("|", "/")
    say("FLEX_STAGE:%s|%s|%s|%s" % (name, "" if pct is None else int(pct), LABEL, detail))









def _load_autocaptions():
    here = os.path.dirname(os.path.abspath(__file__))
    target = os.path.join(here, "autocaptions.py")
    if not os.path.isfile(target) or os.environ.get("FLEX_LIVE_NO_AC_IMPORT") == "1":
        return None
    old_bytecode = sys.dont_write_bytecode
    old_stdout = sys.stdout
    try:
        import importlib.util
        import io
        import warnings
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location("flex_autocaptions_helpers", target)
        module = importlib.util.module_from_spec(spec)
        sys.stdout = io.StringIO()
        with warnings.catch_warnings():
            spec.loader.exec_module(module)
        for name in ("generate_srt", "has_devanagari", "to_roman"):
            if not callable(getattr(module, name, None)):
                return None
        return module
    except BaseException:
        return None
    finally:
        sys.stdout = old_stdout
        sys.dont_write_bytecode = old_bytecode







def _ac_format_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _ac_segment_bounds(segment):
    start = segment.get('start')
    end = segment.get('end')
    first_word_start = None
    last_word_end = None
    for word in segment.get('words') or []:
        value = word.get('start')
        if first_word_start is None and isinstance(value, (int, float)):
            first_word_start = float(value)
        value = word.get('end')
        if isinstance(value, (int, float)):
            last_word_end = float(value)
    if first_word_start is not None:
        start = first_word_start
    if last_word_end is not None:
        end = last_word_end
    if start is None or end is None or end <= start:
        return segment.get('start'), segment.get('end')
    return start, end


def _ac_clamp_to_range(start, end, real_preroll):
    if start >= 0.0:
        return (start, end)
    if end > 0.0:
        return (0.0, end)
    if real_preroll > 0.001:
        return None
    return (0.0, max(0.05, end - start))


def _ac_generate_srt(result, max_words=0, fill_gaps=False, start_time=None, end_time=None, pad_start=0.0, real_preroll=0.0):
    blocks = []
    sel_duration = (end_time - start_time) if (start_time is not None and end_time is not None) else None
    for segment in result.get('segments', []):
        words = segment.get('words', [])
        if max_words > 0:
            if words:
                for i in range(0, len(words), max_words):
                    chunk = words[i:i + max_words]
                    raw_start = chunk[0].get('start', segment['start'])
                    raw_end = chunk[-1].get('end', segment['end'])
                    start = raw_start - pad_start
                    end = raw_end - pad_start
                    _placed = _ac_clamp_to_range(start, end, real_preroll)
                    if _placed is None:
                        continue
                    start, end = _placed
                    if sel_duration is not None:
                        if start >= sel_duration:
                            continue
                        if end > sel_duration:
                            end = sel_duration
                    text = "".join([w.get('word', '') for w in chunk]).strip()
                    if text:
                        blocks.append({'start': start, 'end': end, 'text': text})
            else:
                seg_words = segment['text'].strip().split()
                if not seg_words:
                    continue
                duration = segment['end'] - segment['start']
                num_words = len(seg_words)
                for i in range(0, num_words, max_words):
                    chunk_words = seg_words[i:i + max_words]
                    word_start_idx = i
                    word_end_idx = min(i + max_words, num_words)
                    raw_start = segment['start'] + (word_start_idx / num_words) * duration
                    raw_end = segment['start'] + (word_end_idx / num_words) * duration
                    start = raw_start - pad_start
                    end = raw_end - pad_start
                    _placed = _ac_clamp_to_range(start, end, real_preroll)
                    if _placed is None:
                        continue
                    start, end = _placed
                    if sel_duration is not None:
                        if start >= sel_duration:
                            continue
                        if end > sel_duration:
                            end = sel_duration
                    text = " ".join(chunk_words).strip()
                    if text:
                        blocks.append({'start': start, 'end': end, 'text': text})
        else:
            raw_start, raw_end = _ac_segment_bounds(segment)
            start = raw_start - pad_start
            end = raw_end - pad_start
            _placed = _ac_clamp_to_range(start, end, real_preroll)
            if _placed is None:
                continue
            start, end = _placed
            if sel_duration is not None:
                if start >= sel_duration:
                    continue
                if end > sel_duration:
                    end = sel_duration
            text = segment['text'].strip()
            if text:
                blocks.append({'start': start, 'end': end, 'text': text})
    if fill_gaps and len(blocks) > 1:
        for i in range(len(blocks) - 1):
            curr_end = blocks[i]['end']
            next_start = blocks[i + 1]['start']
            if next_start > curr_end and (next_start - curr_end) < 2.0:
                blocks[i]['end'] = next_start
    srt_content = ""
    idx = 1
    for b in blocks:
        srt_content += f"{idx}\n{_ac_format_timestamp(b['start'])} --> {_ac_format_timestamp(b['end'])}\n{b['text']}\n\n"
        idx += 1
    return srt_content


def _ac_has_devanagari(text):
    return any(u'ऀ' <= ch <= u'ॿ' for ch in (text or ""))


class _Helpers(object):


    def __init__(self):
        self.module = _load_autocaptions()
        self.source = "autocaptions.py" if self.module else "built-in copy"



        self.writes_sidecar = True
        try:
            here = os.path.dirname(os.path.abspath(__file__))
            with open(os.path.join(here, "autocaptions.py"), encoding="utf-8", errors="replace") as fh:
                self.writes_sidecar = '".words.json"' in fh.read()
        except OSError:
            pass

    def generate_srt(self, *a, **k):
        if self.module:
            return self.module.generate_srt(*a, **k)
        return _ac_generate_srt(*a, **k)

    def has_devanagari(self, text):
        if self.module:
            return self.module.has_devanagari(text)
        return _ac_has_devanagari(text)

    def to_roman(self, text):
        if self.module:
            return self.module.to_roman(text)
        return None





class LiveError(Exception):


    def __init__(self, message, kind="failed", code="", status=0, retryable=False):
        Exception.__init__(self, message)
        self.kind = kind
        self.code = code
        self.status = status
        self.retryable = retryable


class Cancelled(Exception):
    pass


NOT_ON = "Gemini Live is not switched on yet on the Flex server."
RELINK = ("Flex AI could not confirm your licence on this machine - it needs re-linking. "
          "Open AI Settings and activate your licence again, then press TRANSCRIBE.")





class FlexLive(object):
    def __init__(self):
        key = _secret(os.environ.get("FLEX_LICENSE_KEY", ""))
        install = _secret(os.environ.get("FLEX_INSTALL_ID", ""))
        if not key:
            raise LiveError(RELINK + " (No licence key reached the engine.)", kind="relink",
                            code="INVALID_LICENSE")
        self.headers = {"Accept": "application/json", "X-Flex-License-Key": key}
        if install:
            self.headers["X-Install-ID"] = install
        self.url = CLOUD_BASE + LIVE_PATH

    def call(self, action, body, timeout=45.0):


        payload = dict(body or {})
        payload["action"] = action
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self.url + "?action=" + quote(action), data=data, method="POST")
        for name, value in self.headers.items():
            req.add_header(name, value)
        req.add_header("Content-Type", "application/json")
        try:
            response = urllib.request.urlopen(req, timeout=timeout)
            status, text = response.getcode(), response.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as http_error:
            status = http_error.code
            try:
                text = http_error.read().decode("utf-8", "replace")
            except Exception:
                text = ""
        except Cancelled:
            raise
        except Exception as transport_error:
            raise LiveError("Could not reach the Flex server: %s" % transport_error,
                            kind="network", code="NETWORK", retryable=True)
        try:
            parsed = json.loads(text) if text.strip() else {}
        except ValueError:
            parsed = None
        return _classify(action, status, parsed, text)


def _classify(action, status, parsed, text):
    if not isinstance(parsed, dict):
        if status == 404:
            raise LiveError(NOT_ON, kind="not_on", code="404", status=404)
        if status == 503:
            raise LiveError(NOT_ON, kind="not_on", code="503", status=503)
        if status == 401:
            raise LiveError(RELINK, kind="relink", code="401", status=401)
        snippet = " ".join(str(text or "").split())[:160]
        raise LiveError("The Flex server answered HTTP %s with something that is not JSON. %s"
                        % (status, snippet), kind="failed", code="BAD_BODY", status=status, retryable=True)
    err = parsed.get("error")
    err = err if isinstance(err, dict) else ({"message": err} if isinstance(err, str) and err else {})
    failed = parsed.get("success") is False or (bool(err) and parsed.get("success") is not True)
    if status >= 400 and parsed.get("success") is not True:
        failed = True
    if not failed:
        return parsed
    code = str(err.get("code") or "").upper()
    message = str(err.get("message") or parsed.get("message") or "").strip()
    if status == 401 or code in ("INVALID_LICENSE", "AUTHENTICATION_REQUIRED", "401"):
        raise LiveError(RELINK, kind="relink", code=code or "401", status=status)
    if status == 404 or code in ("404", "NOT_FOUND"):
        raise LiveError(NOT_ON, kind="not_on", code=code or "404", status=status)
    if status == 503 or code == "PROVIDER_NOT_CONFIGURED":
        raise LiveError(NOT_ON, kind="not_on", code=code or "503", status=status)
    if code == "INSUFFICIENT_CREDITS" or status == 402:
        need, have = parsed.get("required_credits"), parsed.get("available_credits")
        extra = (" (needs %s, you have %s)" % (need, have)) if need is not None and have is not None else ""
        raise LiveError("Not enough Flex AI credits for this audio%s. Nothing was charged." % extra,
                        kind="credits", code=code or "402", status=status)
    if code == "PROVIDER_BILLING":
        raise LiveError("Gemini Live is switched on, but its Google account needs billing set up. "
                        "Nothing was charged.", kind="not_on", code=code, status=status)
    if code == "PROVIDER_BUSY" or status == 429:
        busy = LiveError("Gemini Live is busy right now. Try again in a minute. Nothing was charged.",
                         kind="busy", code=code or "429", status=status, retryable=True)
        try:
            busy.retry_after = float(parsed.get("retry_after_seconds") or err.get("retry_after_seconds") or 0) or None
        except (TypeError, ValueError):
            busy.retry_after = None
        raise busy
    raise LiveError("The Flex server refused the Gemini Live %s request: %s%s"
                    % (action, message or "no reason given", (" (%s)" % code) if code else ""),
                    kind="failed", code=code or str(status), status=status,
                    retryable=bool(err.get("retryable")))


def _parse_time(value):

    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        v = float(value)
        return v / 1000.0 if v > 1e11 else v
    m = re.match(r"^(\d{4})-(\d\d)-(\d\d)[T ](\d\d):(\d\d):(\d\d)(\.\d+)?(Z|[+-]\d\d:?\d\d)?$", str(value).strip())
    if not m:
        try:
            return _parse_time(float(value))
        except ValueError:
            return None
    import calendar
    y, mo, d, h, mi, s, frac, tz = m.groups()
    t = calendar.timegm((int(y), int(mo), int(d), int(h), int(mi), int(s), 0, 0, 0))
    if frac:
        t += float(frac)
    if tz and tz != "Z":
        sign = 1 if tz[0] == "+" else -1
        digits = tz[1:].replace(":", "")
        t -= sign * (int(digits[:2]) * 3600 + int(digits[2:4]) * 60)
    return float(t)


def _duration(value):

    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value) if value == value else None
    if isinstance(value, dict):
        try:
            return float(value.get("seconds") or 0) + float(value.get("nanos") or 0) / 1e9
        except (TypeError, ValueError):
            return None
    text = str(value).strip().lower()
    m = re.match(r"^(-?\d+(?:\.\d+)?)\s*(s|ms)?$", text)
    if not m:
        return None
    number = float(m.group(1))
    return number / 1000.0 if m.group(2) == "ms" else number








_WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


class WsClosed(Exception):
    def __init__(self, code=1006, reason=""):
        Exception.__init__(self, "closed (%s) %s" % (code, reason))
        self.code = code
        self.reason = reason


class WsHandshakeError(Exception):
    def __init__(self, status, body=""):
        Exception.__init__(self, "HTTP %s" % status)
        self.status = status
        self.body = body


class WebSocket(object):
    MAX_MESSAGE = 16 * 1024 * 1024

    def __init__(self, url, timeout=30.0):
        parts = urlsplit(url)
        scheme = parts.scheme.lower()
        if scheme not in ("wss", "ws"):
            raise ValueError("not a WebSocket URL")
        if scheme == "ws" and os.environ.get("FLEX_LIVE_ALLOW_WS") != "1":
            raise ValueError("unencrypted ws:// is only allowed in tests (FLEX_LIVE_ALLOW_WS=1)")
        self.host = parts.hostname or ""
        self.port = parts.port or (443 if scheme == "wss" else 80)
        self.where = "%s%s" % (self.host, parts.path)
        path = (parts.path or "/") + (("?" + parts.query) if parts.query else "")
        self.buf = bytearray()
        self.lock = threading.Lock()
        self.closed = False
        self.close_sent = False
        self.close_code = None
        self.close_reason = ""
        self._frag = None
        raw = socket.create_connection((self.host, self.port), timeout=timeout)
        try:
            raw.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except Exception:
            pass
        if scheme == "wss":
            raw = _ssl_context().wrap_socket(raw, server_hostname=self.host)
        self.sock = raw
        self.sock.settimeout(timeout)
        self._handshake(path)


    def _handshake(self, path):
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        host = self.host if self.port in (80, 443) else "%s:%d" % (self.host, self.port)
        request = ("GET %s HTTP/1.1\r\nHost: %s\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                   "Sec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n"
                   "User-Agent: FlexLive/%s\r\n\r\n" % (path, host, key, VERSION))
        self.sock.sendall(request.encode("ascii"))
        head = bytearray()
        while b"\r\n\r\n" not in head:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise WsHandshakeError(0, "connection closed during the handshake")
            head += chunk
            if len(head) > 65536:
                raise WsHandshakeError(0, "handshake reply too large")
        header_bytes, rest = bytes(head).split(b"\r\n\r\n", 1)
        lines = header_bytes.decode("latin-1").split("\r\n")
        m = re.match(r"HTTP/1\.[01] (\d{3})", lines[0])
        status = int(m.group(1)) if m else 0
        headers = {}
        for line in lines[1:]:
            if ":" in line:
                k, v = line.split(":", 1)
                headers[k.strip().lower()] = v.strip()
        if status != 101:
            body = rest
            try:
                want = int(headers.get("content-length", "0") or 0)
                self.sock.settimeout(3.0)
                while len(body) < min(want, 8192):
                    chunk = self.sock.recv(4096)
                    if not chunk:
                        break
                    body += chunk
            except Exception:
                pass
            self._drop()
            raise WsHandshakeError(status, body[:600].decode("utf-8", "replace"))
        expect = base64.b64encode(hashlib.sha1((key + _WS_GUID).encode("ascii")).digest()).decode("ascii")
        if headers.get("sec-websocket-accept", "") != expect:
            self._drop()
            raise WsHandshakeError(101, "bad Sec-WebSocket-Accept")
        self.buf += rest


    def _send_frame(self, opcode, payload):
        n = len(payload)
        head = bytearray([0x80 | opcode])
        if n < 126:
            head.append(0x80 | n)
        elif n < 65536:
            head.append(0x80 | 126)
            head += struct.pack("!H", n)
        else:
            head.append(0x80 | 127)
            head += struct.pack("!Q", n)
        mask = os.urandom(4)
        head += mask
        if n:

            repeated = (mask * (n // 4 + 1))[:n]
            masked = (int.from_bytes(payload, "big") ^ int.from_bytes(repeated, "big")).to_bytes(n, "big")
        else:
            masked = b""
        with self.lock:
            if self.closed and opcode != 0x8:
                raise WsClosed(self.close_code or 1006, self.close_reason)
            self.sock.sendall(bytes(head) + masked)

    def send_text(self, text):
        self._send_frame(0x1, text.encode("utf-8"))

    def send_json(self, obj):
        self.send_text(json.dumps(obj, separators=(",", ":"), ensure_ascii=False))


    def _parse(self):

        buf = self.buf
        if len(buf) < 2:
            return None
        b0, b1 = buf[0], buf[1]
        n = b1 & 0x7F
        pos = 2
        if n == 126:
            if len(buf) < 4:
                return None
            n = struct.unpack("!H", bytes(buf[2:4]))[0]
            pos = 4
        elif n == 127:
            if len(buf) < 10:
                return None
            n = struct.unpack("!Q", bytes(buf[2:10]))[0]
            pos = 10
        if n > self.MAX_MESSAGE:
            raise WsClosed(1009, "message too big")
        mask = None
        if b1 & 0x80:
            if len(buf) < pos + 4:
                return None
            mask = bytes(buf[pos:pos + 4])
            pos += 4
        if len(buf) < pos + n:
            return None
        payload = bytes(buf[pos:pos + n])
        del buf[:pos + n]
        if mask and n:
            repeated = (mask * (n // 4 + 1))[:n]
            payload = (int.from_bytes(payload, "big") ^ int.from_bytes(repeated, "big")).to_bytes(n, "big")
        return (b0 & 0x80) != 0, b0 & 0x0F, payload

    def _fill(self, timeout):

        pending = 0
        try:
            pending = self.sock.pending() if hasattr(self.sock, "pending") else 0
        except Exception:
            pending = 0
        if not pending:
            import select
            try:
                ready, _, _ = select.select([self.sock], [], [], max(0.0, timeout))
            except (OSError, ValueError):
                raise WsClosed(1006, "socket closed")
            if not ready:
                return False
        try:
            chunk = self.sock.recv(65536)
        except ssl.SSLWantReadError:
            return False
        except socket.timeout:
            return False
        except OSError:
            raise WsClosed(self.close_code or 1006, self.close_reason or "connection lost")
        if not chunk:
            self.closed = True
            raise WsClosed(self.close_code or 1006, self.close_reason or "connection closed without a close frame")
        self.buf += chunk
        return True

    def poll(self, timeout=0.0):


        deadline = time.time() + max(0.0, timeout)
        while True:
            frame = self._parse()
            if frame is None:
                left = deadline - time.time()
                if not self._fill(left if left > 0 else 0.0):
                    return None
                continue
            fin, opcode, payload = frame
            if opcode == 0x9:
                try:
                    self._send_frame(0xA, payload)
                except Exception:
                    pass
                continue
            if opcode == 0xA:
                continue
            if opcode == 0x8:
                code, reason = 1005, ""
                if len(payload) >= 2:
                    code = struct.unpack("!H", payload[:2])[0]
                    reason = payload[2:].decode("utf-8", "replace")
                self.close_code, self.close_reason = code, reason
                if not self.close_sent:
                    try:
                        self.close_sent = True
                        self._send_frame(0x8, struct.pack("!H", code if code not in (1005, 1006) else 1000))
                    except Exception:
                        pass
                self.closed = True
                self._drop()
                raise WsClosed(code, reason)
            if opcode in (0x1, 0x2):
                if fin:
                    return payload
                self._frag = bytearray(payload)
                continue
            if opcode == 0x0 and self._frag is not None:
                self._frag += payload
                if len(self._frag) > self.MAX_MESSAGE:
                    raise WsClosed(1009, "message too big")
                if fin:
                    out, self._frag = bytes(self._frag), None
                    return out
                continue
            raise WsClosed(1002, "unexpected frame opcode %d" % opcode)

    def close(self, code=1000, reason="", wait=1.0):
        if self.closed:
            self._drop()
            return
        try:
            self.close_sent = True
            self._send_frame(0x8, struct.pack("!H", code) + reason.encode("utf-8")[:120])
        except Exception:
            self.closed = True
            self._drop()
            return
        end = time.time() + wait
        try:
            while time.time() < end:
                self.poll(max(0.0, end - time.time()))
        except WsClosed:
            pass
        except Exception:
            pass
        self.closed = True
        self._drop()

    def pending_close(self, wait=1.0):



        end = time.time() + wait
        while time.time() < end:
            try:
                if self.poll(max(0.0, end - time.time())) is None and self.closed:
                    return None
            except WsClosed as closed:
                return closed
            except Exception:
                return None
        return None

    def abort(self):

        self.closed = True
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass

    def _drop(self):
        try:
            self.sock.close()
        except Exception:
            pass


def _ssl_context():
    ctx = ssl.create_default_context()
    try:
        if not ctx.get_ca_certs():
            import certifi
            ctx.load_verify_locations(certifi.where())
    except Exception:
        pass
    return ctx





def find_ffmpeg():


    found = shutil.which("ffmpeg")
    if found:
        return found
    home = os.path.expanduser("~")
    exe = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    for folder in (os.path.join(home, ".flex_gui_bin"), "/opt/homebrew/bin", "/usr/local/bin", "/usr/bin"):
        candidate = os.path.join(folder, exe)
        if os.path.isfile(candidate):
            return candidate
    return None


def decode_audio(input_path, out_path, start_time=None, end_time=None):

    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        raise LiveError("Gemini Live needs ffmpeg to read your media and none was found. "
                        "Press Install / Fix Dependencies in Auto Captions.", kind="local", code="NO_FFMPEG")
    cmd = [ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-i", input_path]
    if start_time is not None and end_time is not None:
        cmd += ["-ss", "%.3f" % start_time, "-to", "%.3f" % end_time]
    cmd += ["-vn", "-ac", "1", "-ar", str(RATE), "-f", "s16le", "-acodec", "pcm_s16le", out_path]
    flags = 0x08000000 if os.name == "nt" else 0
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=flags)
    if proc.returncode != 0 or not os.path.exists(out_path):
        tail = (proc.stderr or b"").decode("utf-8", "replace").strip().splitlines()[-3:]
        raise LiveError("ffmpeg could not read that media: %s" % (" ".join(tail) or "exit %d" % proc.returncode),
                        kind="local", code="FFMPEG")
    size = os.path.getsize(out_path)
    if size < RATE * 2 // 10:
        raise LiveError("That media has no audio track (or less than 0.1 s of it).", kind="local", code="NO_AUDIO")
    return size / float(RATE * 2)


def read_pcm(path, start_s, end_s):
    with open(path, "rb") as handle:
        handle.seek(int(round(start_s * RATE)) * 2)
        return handle.read(int(round((end_s - start_s) * RATE)) * 2)


def envelope(pcm, hop=0.01):


    samples = array.array("h")
    samples.frombytes(pcm[:len(pcm) - (len(pcm) % 2)])
    if sys.byteorder == "big":
        samples.byteswap()
    n = max(1, int(RATE * hop))
    mul = operator.mul
    out = []
    for k in range(0, len(samples), n):
        seg = samples[k:k + n]
        out.append(math.sqrt(sum(map(mul, seg, seg)) / float(len(seg))))
    return out





SNAP_MAX = 0.30
MIN_WORD = 0.04
EDGE_TRIM = 0.30


def _percentile(values, q):
    if not values:
        return 0.0
    s = sorted(values)
    return s[min(len(s) - 1, max(0, int(q * (len(s) - 1))))]


def place_words(text, u_start, u_end, env, t0, hop=0.01):









    words = [w for w in str(text or "").split() if w]
    if not words:
        return []
    n = len(words)
    span = u_end - u_start
    if span <= 0:
        u_end = u_start + MIN_WORD * n
        span = u_end - u_start
    min_d = min(MIN_WORD, span / n)

    def frame(t):
        return int(math.floor((t - t0) / hop))

    def level(t):
        f = frame(t)
        return env[f] if 0 <= f < len(env) else 0.0

    inside = env[max(0, frame(u_start)):max(0, frame(u_end)) + 1] if env else []
    speech = _percentile(inside, 0.5) if inside else 0.0
    floor = _percentile(env, 0.1) if env else 0.0
    usable = bool(inside) and speech > floor * 1.5
    thr = floor + 0.15 * (speech - floor) if usable else 0.0


    if usable:
        room = span - n * min_d * 2
        cut = 0.0
        while cut + hop <= min(EDGE_TRIM, room) and level(u_start + cut + hop * 0.5) < thr:
            cut += hop
        u_start += cut
        room -= cut
        cut = 0.0
        while cut + hop <= min(EDGE_TRIM, room) and level(u_end - cut - hop * 0.5) < thr:
            cut += hop
        u_end -= cut
        span = u_end - u_start

    weights = [len(w) + 1 for w in words]
    total = float(sum(weights))
    bounds = [u_start]
    acc = 0
    for w in weights[:-1]:
        acc += w
        bounds.append(u_start + span * acc / total)
    bounds.append(u_end)

    snapped = [u_start]
    for k in range(1, n):
        b = bounds[k]
        width = min(SNAP_MAX, max(bounds[k] - bounds[k - 1], bounds[k + 1] - bounds[k]) * 0.6)
        lo = max(b - width, snapped[-1] + min_d)
        hi = min(b + width, bounds[k + 1] - min_d)
        best = b
        if usable and hi > lo and width > 0:
            f_lo = max(0, int(math.ceil((lo - t0) / hop - 0.5)))
            f_hi = min(len(env) - 1, int(math.floor((hi - t0) / hop - 0.5)))
            best_score = None
            for f in range(f_lo, f_hi + 1):
                t = t0 + (f + 0.5) * hop
                score = env[f] + speech * 0.25 * abs(t - b) / width
                if best_score is None or score < best_score:
                    best_score, best = score, t
        snapped.append(best)
    snapped.append(u_end)



    for k in range(1, n):
        snapped[k] = max(snapped[k], snapped[k - 1] + min_d)
    for k in range(n - 1, 0, -1):
        snapped[k] = min(snapped[k], snapped[k + 1] - min_d)

    starts = snapped[:-1]
    ends = snapped[1:]
    if usable:
        for k in range(1, n):
            b = snapped[k]
            if level(b) >= thr:
                continue
            left = b
            while left - hop > starts[k - 1] + min_d and b - (left - hop) <= SNAP_MAX and level(left - hop * 0.5) < thr:
                left -= hop
            right = b
            while right + hop < ends[k] - min_d and (right + hop) - b <= SNAP_MAX and level(right + hop * 0.5) < thr:
                right += hop
            ends[k - 1] = left
            starts[k] = right
    return [(words[k], starts[k], ends[k]) for k in range(n)]





_PACE_WORDS = re.compile(r"(too fast|faster than|real.?time|realtime|rate.?limit|too many|throttl|slow down|"
                         r"backpressure|resource.?exhausted|try again later)", re.I)
_MONEY_WORDS = re.compile(r"(quota|billing|spend|credit|payment)", re.I)
_AUTH_WORDS = re.compile(r"(token|expired|unauthori[sz]ed|unauthenticated|permission|auth)", re.I)


def pace_reason(code, reason):


    reason = str(reason or "")
    if _MONEY_WORDS.search(reason):
        return False
    return code == 1013 or bool(_PACE_WORDS.search(reason))


class SessionFailed(Exception):
    def __init__(self, kind, message, code=None, reason=""):
        Exception.__init__(self, message)
        self.kind = kind
        self.code = code
        self.reason = reason


class Session(object):
    def __init__(self, job, index, start_s, end_s):
        self.job = job
        self.index = index
        self.start_s = start_s
        self.end_s = end_s
        self.length = end_s - start_s
        self.sent_s = 0.0
        self.heard_s = 0.0
        self.done = False
        self.finals = []
        self.interim = None
        self.ws = None
        self.attempts = 0
        self.notes = []
        self.pcm = None
        self.env = None
        self.speech_thr = 0.0


    def handle(self, raw):
        try:
            msg = json.loads(raw.decode("utf-8", "replace"))
        except ValueError:
            return None
        if not isinstance(msg, dict):
            return None
        if "setupComplete" in msg:
            return "setup"
        if isinstance(msg.get("error"), (dict, str)):
            err = msg["error"]
            text = err.get("message") if isinstance(err, dict) else err
            raise SessionFailed("failed", "Google reported an error: %s" % text, reason=str(text))
        go = msg.get("goAway")
        if isinstance(go, dict):
            left = _duration(go.get("timeLeft"))
            self.notes.append("goAway (%.1fs left)" % (left or 0.0))
        sc = msg.get("serverContent")
        if not isinstance(sc, dict):
            return None
        interim = sc.get("interimInputTranscription")
        if isinstance(interim, dict) and str(interim.get("text") or "").strip():
            self.interim = self._utterance(interim, sc)
            if self.interim["end"] is not None:
                self.heard_s = max(self.heard_s, min(self.interim["end"], self.sent_s))
        final = sc.get("inputTranscription")
        if isinstance(final, dict) and str(final.get("text") or "").strip():
            u = self._utterance(final, sc)
            self.finals.append(u)
            self.interim = None
            if u["end"] is not None:
                self.heard_s = max(self.heard_s, min(u["end"], self.length))
        if sc.get("turnComplete") or sc.get("generationComplete"):
            return "turn"
        return "content"

    @staticmethod
    def _utterance(t, sc):
        start = _duration(t.get("startOffset"))
        end = _duration(t.get("endOffset"))
        nested = t.get("utterance") if isinstance(t.get("utterance"), dict) else None
        if start is None and nested:
            start = _duration(nested.get("startOffset"))
        if end is None and nested:
            end = _duration(nested.get("endOffset"))
        if start is None:
            start = _duration(sc.get("startOffset"))
        if end is None:
            end = _duration(sc.get("endOffset"))
        return {"text": str(t.get("text") or "").strip(), "start": start, "end": end,
                "lang": t.get("languageCode") or None}


    def run(self, url, setup, pace):
        job = self.job
        self.finals, self.interim, self.sent_s, self.heard_s = [], None, 0.0, 0.0
        if self.pcm is None:
            self.pcm = read_pcm(job.pcm_path, self.start_s, self.end_s)
            self.env = envelope(self.pcm)
            floor, loud = _percentile(self.env, 0.1), _percentile(self.env, 0.9)
            self.speech_thr = floor + 0.25 * max(0.0, loud - floor)
        pcm = self.pcm
        try:
            ws = WebSocket(url, timeout=job.io_timeout)
        except WsHandshakeError as hs:
            if hs.status in (401, 403) or _AUTH_WORDS.search(hs.body or ""):
                raise SessionFailed("auth", "Google refused the session token (HTTP %s)." % hs.status,
                                    code=hs.status, reason=hs.body)
            if hs.status == 429:
                raise SessionFailed("pace", "Google answered HTTP 429 (too many requests).", code=429,
                                    reason=hs.body)
            raise SessionFailed("failed", "Google refused the Live connection (HTTP %s): %s"
                                % (hs.status, " ".join(str(hs.body).split())[:160]), code=hs.status)
        except (OSError, ValueError) as conn_error:
            raise SessionFailed("failed", "Could not connect to Gemini Live: %s" % conn_error)
        self.ws = ws
        job.register(ws)
        try:
            ws.send_json({"setup": setup} if "setup" not in setup else setup)
            deadline = time.time() + job.setup_timeout
            while True:
                job.check()
                raw = ws.poll(0.25)
                if raw is not None and self.handle(raw) == "setup":
                    break
                if time.time() > deadline:
                    raise SessionFailed("failed", "Gemini Live did not confirm the session setup in %ds."
                                        % job.setup_timeout)
            chunk_bytes = int(RATE * 2 * job.chunk_ms / 1000)
            chunk_s = job.chunk_ms / 1000.0
            mime = job.mime
            total = len(pcm)
            t0 = time.time()
            k = 0
            for offset in range(0, total, chunk_bytes):
                job.check()
                if pace > 0:
                    due = t0 + max(0.0, k * chunk_s - job.burst) / pace
                    while True:
                        wait = due - time.time()
                        if wait <= 0:
                            break
                        raw = ws.poll(min(wait, 0.25))
                        if raw is not None:
                            self.handle(raw)
                        job.check()
                piece = pcm[offset:offset + chunk_bytes]
                ws.send_json({"realtimeInput": {"audio": {
                    "data": base64.b64encode(piece).decode("ascii"), "mimeType": mime}}})
                k += 1
                self.sent_s = min(self.length, (offset + len(piece)) / float(RATE * 2))
                while True:
                    raw = ws.poll(0.0)
                    if raw is None:
                        break
                    self.handle(raw)
            ws.send_json({"realtimeInput": {"audioStreamEnd": True}})
            self.sent_s = self.length
            self._finish(ws)
        except (socket.timeout, ssl.SSLError, OSError) as io_error:
            job.check()
            closed = ws.pending_close(1.0)
            if closed is None:
                if pace == 0 or pace > 1.5:
                    raise SessionFailed("maybe_pace", "the connection dropped while streaming faster than "
                                        "real time (%s)" % io_error, code=1006, reason=str(io_error))
                raise SessionFailed("failed", "The connection to Gemini Live failed: %s" % io_error, code=1006)
            self._closed(closed, pace)
        except WsClosed as closed:
            job.check()
            self._closed(closed, pace)
        finally:
            job.unregister(ws)
            try:
                ws.close(1000, "done", wait=0.5)
            except Exception:
                pass
            self.ws = None
        return pcm

    def _closed(self, closed, pace):

        reason = closed.reason or ""
        if pace_reason(closed.code, reason):
            raise SessionFailed("pace", "Google closed the session for sending audio too fast "
                                "(code %s: %s)" % (closed.code, reason or "no reason"),
                                code=closed.code, reason=reason)
        if closed.code == 1008 and _AUTH_WORDS.search(reason) and self.sent_s <= 0.2:
            raise SessionFailed("auth", "Google refused the session token (code 1008: %s)" % reason,
                                code=closed.code, reason=reason)
        if closed.code == 1006 and (pace == 0 or pace > 1.5):
            raise SessionFailed("maybe_pace", "the connection dropped (no close frame) while streaming "
                                "faster than real time", code=1006, reason=reason)
        if re.search(r"exhausted", reason, re.I) and (pace == 0 or pace > 1.05):
            raise SessionFailed("pace", "Gemini Live fell behind the audio (code %s: %s)"
                                % (closed.code, reason or "no reason"), code=closed.code, reason=reason)
        if _MONEY_WORDS.search(reason) or re.search(r"exhausted", reason, re.I):



            raise SessionFailed("quota", "Google's quota for Gemini Live is used up (code %s: %s)"
                                % (closed.code, reason or "no reason"), code=closed.code, reason=reason)
        raise SessionFailed("failed", "Google closed the session mid-stream (code %s: %s)"
                            % (closed.code, reason or "no reason"), code=closed.code, reason=reason)

    def rest_is_quiet(self):


        env = self.env or []
        first = int((self.heard_s + 0.5) / 0.01)
        loud = sum(1 for v in env[first:] if v > self.speech_thr)
        return loud * 0.01 < 0.3

    def _finish(self, ws):



        job = self.job
        started = time.time()
        last = time.time()
        turn = False
        while True:
            job.check()
            try:
                raw = ws.poll(0.25)
            except WsClosed as closed:
                job.check()
                normal = closed.code in (1000, 1001, 1005)
                if normal or self.heard_s >= self.length - job.tail_tolerance or self.rest_is_quiet():
                    if not normal:
                        self.notes.append("closed after the end of audio (code %s: %s)" % (closed.code, closed.reason))
                    break
                raise
            now = time.time()
            if raw is not None:
                last = now
                kind = self.handle(raw)
                if kind == "turn":
                    turn = True
            near_end = self.heard_s >= self.length - job.tail_tolerance
            quiet = now - last
            if turn and self.interim is None and (near_end or self.rest_is_quiet()) and quiet >= 0.3:
                break
            if self.interim is None and (near_end or self.rest_is_quiet()) and quiet >= job.tail_idle:
                break
            if quiet >= job.idle:
                self.notes.append("no reply for %ds after the end of audio" % int(job.idle))
                break
            if now - started >= job.final_wait:
                self.notes.append("stopped waiting %ds after the end of audio" % int(job.final_wait))
                break
        if self.interim is not None:
            self.finals.append(self.interim)
            self.notes.append("last partial line kept (no final came)")
            self.interim = None





class Job(object):
    def __init__(self, args, pcm_path, total_s):
        self.args = args
        self.pcm_path = pcm_path
        self.total_s = total_s
        self.cancel_event = threading.Event()
        self.abort_reason = None
        self.lock = threading.Lock()
        self.sockets = set()
        self.server = None
        self.job_id = None
        self.tokens = {}
        self.refreshes = 0
        self.ws_url = None
        self.token_param = "access_token"
        self.setup = None
        self.dev_key = None
        self.session_seconds = SESSION_SECONDS
        self.chunk_ms = CHUNK_MS
        self.mime = "audio/pcm;rate=%d" % RATE
        self.pace = args.pace if args.pace is not None else _env_float("FLEX_LIVE_PACE", 1.0)
        self.burst = _env_float("FLEX_LIVE_BURST_S", BURST_SECONDS)
        self.fallback_pace = _env_float("FLEX_LIVE_FALLBACK_PACE", 1.0) or 1.0
        self.parallel = int(max(1, min(MAX_PARALLEL, _env_float("FLEX_LIVE_PARALLEL", MAX_PARALLEL) or MAX_PARALLEL)))
        self.idle = _env_float("FLEX_LIVE_IDLE_S", 45.0) or 45.0
        self.tail_idle = _env_float("FLEX_LIVE_TAIL_IDLE_S", 2.0) or 2.0
        self.tail_tolerance = 2.0
        self.setup_timeout = int(_env_float("FLEX_LIVE_SETUP_TIMEOUT", 25.0) or 25)
        self.io_timeout = _env_float("FLEX_LIVE_IO_TIMEOUT", 60.0) or 60.0
        self.final_wait = 0.0
        self.closed_state = None


    def register(self, ws):
        with self.lock:
            self.sockets.add(ws)
        if self.cancel_event.is_set():
            ws.abort()

    def unregister(self, ws):
        with self.lock:
            self.sockets.discard(ws)

    def stop_all(self, reason):
        if not self.abort_reason:
            self.abort_reason = reason
        self.cancel_event.set()
        with self.lock:
            live = list(self.sockets)
        for ws in live:
            ws.abort()

    def check(self):
        if self.cancel_event.is_set():
            raise Cancelled(self.abort_reason or "cancelled")


    def open(self, language):
        dev = os.environ.get("FLEX_GEMINI_API_KEY", "").strip()
        if dev:
            self.dev_key = _secret(dev)
            base = os.environ.get("FLEX_LIVE_DEV_WS_URL", "").strip() or GOOGLE_WS
            self.ws_url = base
            self.token_param = "key"
            codes = _bcp47(language)
            self.setup = {"model": os.environ.get("FLEX_GEMINI_LIVE_MODEL", GOOGLE_MODEL),
                          "generationConfig": {"responseModalities": ["TEXT"]},
                          "inputAudioTranscription": {"languageCodes": codes}}
            say("Developer key in use (FLEX_GEMINI_API_KEY): the Flex server is not contacted and no credits are used.")
            self.session_seconds = WANT_SESSION_SECONDS
            n = int(math.ceil(self.total_s / self.session_seconds - 1e-9))
            return max(1, n)

        say("Checking your Flex AI balance...")
        self.server = FlexLive()
        reply = self.server.call("token", {"duration_seconds": math.ceil(self.total_s * 1000) / 1000.0,
                                           "language": language or "auto",
                                           "session_seconds": WANT_SESSION_SECONDS})
        self.job_id = str(reply.get("job_id") or "")
        if not self.job_id:
            raise LiveError("The Flex server did not open a Live job.", kind="failed", code="BAD_TOKEN_REPLY")
        say("FLEX_LIVE_JOB:%s" % re.sub(r"[^A-Za-z0-9_\-\.]", "", self.job_id)[:80])
        self.ws_url = str(reply.get("ws_url") or "")
        if not self.ws_url:
            raise LiveError("The Flex server did not say where to stream the audio.", kind="failed",
                            code="BAD_TOKEN_REPLY")
        self.token_param = str(reply.get("token_param") or "access_token")
        setup = reply.get("setup")
        if not isinstance(setup, dict) or not setup:
            raise LiveError("The Flex server did not send the Live session setup.", kind="failed",
                            code="BAD_TOKEN_REPLY")
        self.setup = setup
        try:
            self.session_seconds = float(reply.get("session_seconds") or SESSION_SECONDS)
        except (TypeError, ValueError):
            self.session_seconds = SESSION_SECONDS
        try:
            if reply.get("max_parallel") is not None:
                self.parallel = int(max(1, min(self.parallel, int(reply.get("max_parallel")))))
        except (TypeError, ValueError):
            pass
        audio = reply.get("audio") if isinstance(reply.get("audio"), dict) else {}
        try:
            self.chunk_ms = int(audio.get("chunk_ms") or CHUNK_MS)
        except (TypeError, ValueError):
            self.chunk_ms = CHUNK_MS
        if int(audio.get("sample_rate") or RATE) != RATE:
            raise LiveError("The Flex server asked for %s Hz audio; this engine sends %d Hz."
                            % (audio.get("sample_rate"), RATE), kind="failed", code="BAD_TOKEN_REPLY")
        self.mime = str(audio.get("mime_type") or self.mime)
        self._take_tokens(reply.get("tokens"))
        if reply.get("available_credits") is not None:
            say("FLEXAI_CREDITS:%s" % reply.get("available_credits"))
        n = int(math.ceil(self.total_s / self.session_seconds - 1e-9))
        n = max(1, n)
        self.session_count = n
        missing = [i for i in range(n) if i not in self.tokens]
        if missing:
            raise LiveError("The Flex server sent %d session token(s) for audio that needs %d."
                            % (len(self.tokens), n), kind="failed", code="BAD_TOKEN_REPLY")
        return n

    def _take_tokens(self, tokens):
        if not isinstance(tokens, list):
            return
        for position, entry in enumerate(tokens):
            if not isinstance(entry, dict) or not entry.get("token"):
                continue
            try:
                index = int(entry.get("session", position))
            except (TypeError, ValueError):
                index = position
            self.tokens[index] = {"token": _secret(entry.get("token")),
                                  "new_session_expires_at": _parse_time(entry.get("new_session_expires_at")),
                                  "expires_at": _parse_time(entry.get("expires_at")),
                                  "used": False}

    def token_for(self, index, force_refresh=False):


        if self.dev_key:
            return self.dev_key
        with self.lock:
            entry = self.tokens.get(index)
            stale = entry is None or entry["used"] or (
                entry["new_session_expires_at"] is not None and time.time() > entry["new_session_expires_at"] - 3.0)
            if stale:
                if self.refreshes >= MAX_REFRESHES:
                    raise LiveError("Gemini Live session tokens ran out (3 refreshes per job).",
                                    kind="failed", code="REFRESH_LIMIT")
                want = [index]
                for i, e in self.tokens.items():
                    if i != index and not e["used"] and e["new_session_expires_at"] is not None \
                            and time.time() > e["new_session_expires_at"] - 3.0:
                        want.append(i)
                self.refreshes += 1
                say("Refreshing %d session token(s) (refresh %d of %d)..."
                    % (len(want), self.refreshes, MAX_REFRESHES))
                reply = self.server.call("refresh", {"job_id": self.job_id,
                                                     "sessions": int(getattr(self, "session_count", 0) or max(want) + 1)})
                self._take_tokens(reply.get("tokens"))
                entry = self.tokens.get(index)
                if entry is None or entry["used"]:
                    raise LiveError("The Flex server did not refresh the token for session %d." % (index + 1),
                                    kind="failed", code="REFRESH_FAILED")
            entry["used"] = True
            return entry["token"]

    def url_for(self, token):
        sep = "&" if "?" in self.ws_url else "?"
        return self.ws_url + sep + self.token_param + "=" + quote(token, safe="")

    def done(self):
        if not self.server or not self.job_id:
            return
        try:
            reply = self.server.call("done", {"job_id": self.job_id}, timeout=30.0)
            billing = reply.get("billing") if isinstance(reply.get("billing"), dict) else {}
            left = billing.get("balance_remaining", reply.get("available_credits"))
            if left is not None:
                say("FLEXAI_CREDITS:%s" % left)
            self.closed_state = "done"
            say("FLEX_LIVE_CLOSED:done")
        except LiveError as done_error:
            self.closed_state = "done-failed"
            say("NOTE: the Flex server did not confirm the end of the Live job (%s). "
                "It is settled on your next Gemini Live run." % done_error)
            say("FLEX_LIVE_CLOSED:done-failed")

    def cancel(self, reason):
        if not self.server or not self.job_id or self.closed_state:
            return
        reason = re.sub(r"\s+", " ", str(reason or "cancelled"))[:300]
        try:
            self.server.call("cancel", {"job_id": self.job_id, "reason": _redact(reason)}, timeout=15.0)
            self.closed_state = "cancel"
            say("FLEX_LIVE_CLOSED:cancel")
        except LiveError as cancel_error:
            self.closed_state = "cancel-failed"
            say("NOTE: could not tell the Flex server the Live job was cancelled (%s)." % cancel_error)
            say("FLEX_LIVE_CLOSED:cancel-failed")


def _bcp47(language):


    table = {
        "en": "en-US", "hi": "hi-IN", "hinglish": "hi-IN", "es": "es-ES", "fr": "fr-FR", "de": "de-DE",
        "it": "it-IT", "pt": "pt-BR", "ja": "ja-JP", "ko": "ko-KR", "zh": "cmn-Hans-CN", "ru": "ru-RU",
        "ar": "ar-EG", "bn": "bn-IN", "ta": "ta-IN", "te": "te-IN", "mr": "mr-IN", "gu": "gu-IN",
        "kn": "kn-IN", "ml": "ml-IN", "pa": "pa-IN", "nl": "nl-NL", "pl": "pl-PL", "tr": "tr-TR",
        "uk": "uk-UA", "vi": "vi-VN", "th": "th-TH", "id": "id-ID", "ms": "ms-MY", "fil": "fil-PH",
        "tl": "fil-PH", "sv": "sv-SE", "da": "da-DK", "fi": "fi-FI", "no": "nb-NO", "nb": "nb-NO",
        "cs": "cs-CZ", "el": "el-GR", "he": "he-IL", "hu": "hu-HU", "ro": "ro-RO", "sk": "sk-SK",
        "bg": "bg-BG", "hr": "hr-HR", "sr": "sr-RS", "sl": "sl-SI", "et": "et-EE", "lv": "lv-LV",
        "lt": "lt-LT", "fa": "fa-IR", "sw": "sw-KE", "af": "af-ZA", "ne": "ne-NP", "ur": None,
    }
    code = str(language or "").strip().lower()
    if not code or code == "auto":
        return []
    mapped = table.get(code)
    if mapped:
        return [mapped]
    if "-" in code:
        return [language]
    say("NOTE: no Live language code for '%s'; Gemini Live detects the language itself." % code)
    return []





def run_sessions(job, count):
    sessions = []
    for i in range(count):
        a = i * job.session_seconds
        b = min(job.total_s, (i + 1) * job.session_seconds)
        if b - a <= 0.001:
            break
        sessions.append(Session(job, i, a, b))

    job.final_wait = max(60.0, min(job.session_seconds, 600.0) + 30.0)
    state = {"pace": job.pace, "failed": None, "next": 0, "results": {}}
    pending_lock = threading.Lock()

    def worker():
        while True:
            with pending_lock:
                if state["failed"] or job.cancel_event.is_set() or state["next"] >= len(sessions):
                    return
                s = sessions[state["next"]]
                state["next"] += 1
            try:
                run_one(s)
            except Cancelled:
                return
            except (SessionFailed, LiveError) as failure:
                with pending_lock:
                    if not state["failed"]:
                        state["failed"] = (s, failure)
                job.stop_all("session %d failed: %s" % (s.index + 1, failure))
                return
            except Exception as unexpected:
                with pending_lock:
                    if not state["failed"]:
                        state["failed"] = (s, SessionFailed("failed", "internal error: %r" % (unexpected,)))
                job.stop_all("session %d failed: internal error" % (s.index + 1))
                return

    def run_one(s):
        auth_retry = False
        pace_retry = False
        while True:
            job.check()
            pace = state["pace"]
            token = job.token_for(s.index, force_refresh=auth_retry and not job.dev_key)
            s.attempts += 1
            try:
                s.run(job.url_for(token), job.setup, pace)
            except SessionFailed as failure:
                if failure.kind == "auth" and not auth_retry and not job.dev_key:
                    auth_retry = True
                    say("Session %d: %s Getting a fresh token..." % (s.index + 1, failure))
                    continue
                if failure.kind in ("pace", "maybe_pace") and not pace_retry:
                    pace_retry = True
                    fallback = job.fallback_pace
                    say("PACE: session %d - %s. Retrying it at %s pace%s."
                        % (s.index + 1, failure, "real-time" if fallback == 1.0 else "%gx real-time" % fallback,
                           " in case that was the reason" if failure.kind == "maybe_pace" else ""))
                    with pending_lock:
                        state["pace"] = fallback
                        job.burst = 0.0
                    auth_retry = True
                    continue
                raise
            state["results"][s.index] = (s, s.env)
            s.pcm = None
            s.done = True
            if s.notes:
                say("Session %d: %s" % (s.index + 1, "; ".join(s.notes)))
            return

    threads = [threading.Thread(target=worker, name="flex-live-%d" % k, daemon=True)
               for k in range(min(job.parallel, len(sessions)))]
    total_mb = job.total_s * RATE * 2 / 1048576.0
    say("Uploading %.1f MB of audio (streamed live in %d session%s, up to %d at once)..."
        % (total_mb, len(sessions), "" if len(sessions) == 1 else "s", min(job.parallel, len(sessions))))
    say("Transcribing on Flex AI... (%s)" % LABEL)
    stage("transcribe", 0, "%d session%s" % (len(sessions), "" if len(sessions) == 1 else "s"))
    for t in threads:
        t.start()
    shown = -1
    while any(t.is_alive() for t in threads):
        for t in threads:
            t.join(0.2)
        if job.cancel_event.is_set():
            continue
        covered = 0.0
        live = 0
        for s in sessions:
            if s.done:
                covered += s.length
            else:
                covered += min(s.length, 0.3 * s.sent_s + 0.7 * s.heard_s)
                live += 1 if s.sent_s > 0 else 0
        pct = int(100.0 * covered / max(0.001, job.total_s))
        pct = max(0, min(99, pct))
        if pct >= shown + 4 or (pct > shown and pct >= 95):
            shown = pct
            done_n = sum(1 for s in sessions if s.done)
            say("Transcribing... %d%%" % pct)
            stage("transcribe", pct, "%d of %d sessions done" % (done_n, len(sessions)))
    if state["failed"]:
        s, failure = state["failed"]
        if getattr(failure, "kind", "") == "quota":
            raise LiveError("Gemini Live has reached its Google usage limit right now. Try again in a minute, "
                            "or use your usual engine. (%s)" % failure, kind="busy",
                            code=getattr(failure, "code", "") or "QUOTA", retryable=True)
        raise LiveError("Session %d of %d failed: %s" % (s.index + 1, len(sessions), failure),
                        kind="failed", code=getattr(failure, "code", "") or "SESSION")
    job.check()
    return [state["results"][s.index] for s in sessions]


def build_result(job, finished, language):

    utterances = []
    for s, env in finished:
        known = []
        for order, u in enumerate(s.finals):
            start = u["start"]
            end = u["end"]
            if start is not None:
                start = min(max(0.0, start), s.length)
            if end is not None:
                end = min(max(0.0, end), s.length)
            known.append({"text": u["text"], "start": start, "end": end, "lang": u["lang"], "order": order})
        _fill_missing_times(known, s.length)
        for u in known:
            u["start"] += s.start_s
            u["end"] += s.start_s
            u["session"] = s
            u["env"] = env
            utterances.append(u)
    utterances.sort(key=lambda u: (u["start"], u["session"].index, u["order"]))
    prev_end = 0.0
    segments = []
    detected = None
    for u in utterances:
        start = max(u["start"], prev_end)
        n_words = max(1, len(u["text"].split()))
        end = max(u["end"], start + MIN_WORD * n_words)
        session_end = u["session"].end_s
        if end > session_end and start + MIN_WORD * n_words <= session_end:
            end = session_end
        placed = place_words(u["text"], start, end, u["env"], u["session"].start_s)
        if not placed:
            continue
        words = [{"word": " " + w, "start": round(a, 3), "end": round(b, 3)} for (w, a, b) in placed]

        for k, w in enumerate(words):
            if k and w["start"] < words[k - 1]["end"]:
                w["start"] = words[k - 1]["end"]
            if w["end"] <= w["start"]:
                w["end"] = round(w["start"] + 0.001, 3)
        text = " ".join(w["word"].strip() for w in words)
        segments.append({"id": len(segments), "start": words[0]["start"], "end": words[-1]["end"],
                         "text": " " + text, "words": words})
        prev_end = words[-1]["end"]
        detected = detected or u.get("lang")
    return {"text": " ".join(seg["text"].strip() for seg in segments).strip(),
            "language": language or detected, "segments": segments,
            "engine": MODEL_ID, "word_timing": "estimated"}


def _fill_missing_times(items, length):


    missing = [u for u in items if u["start"] is None or u["end"] is None]
    if not missing:
        return
    i = 0
    while i < len(items):
        if items[i]["start"] is not None and items[i]["end"] is not None:
            if items[i]["end"] < items[i]["start"]:
                items[i]["end"] = items[i]["start"]
            i += 1
            continue
        j = i
        while j < len(items) and (items[j]["start"] is None or items[j]["end"] is None):
            j += 1
        left = items[i - 1]["end"] if i > 0 else 0.0
        right = items[j]["start"] if j < len(items) else length
        run = items[i:j]
        if run[0]["start"] is not None:
            left = max(left, run[0]["start"])
        if run[-1]["end"] is not None:
            right = min(right, run[-1]["end"]) if run[-1]["end"] > left else right
        if right <= left:
            right = min(length, left + 0.4 * len(run))
        chars = [max(1, len(u["text"])) for u in run]
        total = float(sum(chars))
        cursor = left
        for u, c in zip(run, chars):
            u["start"] = cursor
            cursor = cursor + (right - left) * c / total
            u["end"] = cursor
        i = j
    say("NOTE: Gemini Live sent %d line(s) without timing; their timing is estimated from the lines around them."
        % len(missing))





def write_outputs(helpers, result, args):
    output_path = args.output
    say("Formatting subtitles...")
    srt_content = helpers.generate_srt(
        result,
        max_words=args.max_words,
        fill_gaps=args.fill_gaps,
        start_time=args.start_time,
        end_time=args.end_time,
        pad_start=0.0,
        real_preroll=0.0,
    )
    if getattr(args, "emit_json", None):
        try:
            os.makedirs(os.path.dirname(os.path.abspath(args.emit_json)), exist_ok=True)
            with open(args.emit_json, "w", encoding="utf-8") as jf:
                json.dump(result, jf, ensure_ascii=False)
            say("SUCCESS: Transcript JSON written to %s" % args.emit_json)
        except Exception as emit_error:
            say("NOTE: could not write the transcript JSON: %s" % emit_error)
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt_content)
    say(f"SUCCESS: Subtitles written to {output_path}")
    if not helpers.writes_sidecar:
        return
    try:
        words = []
        for segment in result.get("segments", []) or []:
            for word in segment.get("words", []) or []:
                text = (word.get("word") or "").strip()
                if not text:
                    continue
                try:
                    w_start = float(word.get("start", segment.get("start", 0.0)))
                    w_end = float(word.get("end", segment.get("end", 0.0)))
                except (TypeError, ValueError):
                    continue
                if w_end <= w_start:
                    continue
                w_start -= 0.0
                w_end -= 0.0
                if w_end <= 0.0:
                    continue
                if w_start < 0.0:
                    w_start = 0.0
                words.append({"word": text, "start": round(w_start, 4), "end": round(w_end, 4)})
        if words:
            words_path = re.sub(r"\.srt$", "", output_path, flags=re.IGNORECASE) + ".words.json"
            with open(words_path, "w", encoding="utf-8") as wf:
                json.dump({"words": words, "count": len(words)}, wf, ensure_ascii=False)
            say(f"SUCCESS: Word timings written to {words_path}")
        else:
            say("NOTE: no word-level timings available.")
    except Exception as word_error:
        say(f"NOTE: could not write word timings: {word_error}")


def apply_roman(helpers, result):

    converted = 0
    for segment in result.get("segments", []):
        if helpers.has_devanagari(segment.get("text", "")):
            roman = helpers.to_roman(segment["text"])
            if roman is None:
                say("NOTE: Roman script needs autocaptions.py beside this engine; captions stay in Devanagari.")
                return
            segment["text"] = roman
            converted += 1
        for word in segment.get("words", []) or []:
            key = "word" if "word" in word else ("text" if "text" in word else None)
            if key and helpers.has_devanagari(word.get(key, "")):
                word[key] = helpers.to_roman(word[key])
    if "text" in result and helpers.has_devanagari(result["text"]):
        result["text"] = helpers.to_roman(result["text"])
    say("Converted %d segment(s) to Roman script." % converted)





def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Flex AutoCaptions - Gemini 3.5 Transcribe Live (testing)")

    parser.add_argument("--emit-json", default=None)
    parser.add_argument("--engine", default="local")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--model", default=MODEL_ID)
    parser.add_argument("--max-words", type=int, default=0)
    parser.add_argument("--language", default=None)
    parser.add_argument("--initial-prompt", default=None)
    parser.add_argument("--translate-to", default=None)
    parser.add_argument("--roman", action="store_true")
    parser.add_argument("--fill-gaps", action="store_true")
    parser.add_argument("--start-time", "--start", type=float, default=None)
    parser.add_argument("--end-time", "--end", type=float, default=None)

    parser.add_argument("--pace", type=float, default=None,
                        help="audio sending pace as a multiple of real time; 0 = as fast as the socket takes it")
    return parser.parse_args(argv)


def offer(kind):
    usual = str(os.environ.get("FLEX_LIVE_USUAL_LABEL", "") or "").strip() or "your usual engine"
    usual = re.sub(r"[^\x20-\x7e]", "", usual)[:60] or "your usual engine"
    say("FLEX_LIVE_OFFER:%s" % kind)
    say("Switch TRANSCRIPTION MODEL back to %s to caption this now." % usual)


def main(argv=None):
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass
    args = parse_args(argv)
    say("%s (testing) - Flex Live engine %s" % (LABEL, VERSION))
    if not os.path.exists(args.input):
        say(f"Error: Input file does not exist: {args.input}")
        return 1
    say(f"Processing input file: {args.input}")
    helpers = _Helpers()
    if args.translate_to:
        say("NOTE: Translate To needs Whisper; Gemini Live captions stay in the spoken language.")
    if args.initial_prompt:
        say("NOTE: the initial prompt is not used by Gemini Live.")

    start_time, end_time = args.start_time, args.end_time
    if (start_time is None) != (end_time is None):
        start_time = end_time = None
    args.start_time, args.end_time = start_time, end_time

    pcm_path = os.path.join(tempfile.gettempdir(), "flex_live_audio_%d.pcm" % os.getpid())
    job = None
    state = {"signal": None, "defer": False}

    def on_signal(signum, _frame):
        if state["signal"] is not None:
            return
        state["signal"] = signum
        if job is not None:
            job.stop_all("user cancelled")
        if state["defer"]:
            return
        raise Cancelled("user cancelled")

    for name in ("SIGTERM", "SIGINT", "SIGHUP", "SIGBREAK"):
        if hasattr(signal, name):
            try:
                signal.signal(getattr(signal, name), on_signal)
            except (ValueError, OSError):
                pass

    try:
        say("Extracting audio for Gemini Live (16 kHz mono PCM)...")
        total_s = decode_audio(args.input, pcm_path, start_time, end_time)
        say("Audio ready: %.1f s" % total_s)
        language = args.language if args.language and args.language.lower() != "auto" else None
        job = Job(args, pcm_path, total_s)
        if job.pace:
            say("Pace: %gx real time." % job.pace)
        waited = 0.0
        while True:
            busy = None
            state["defer"] = True
            try:
                count = job.open(language)
            except LiveError as failure:


                if failure.kind != "busy" or not getattr(failure, "retry_after", None) or waited >= 240.0:
                    raise
                busy = failure
            finally:
                state["defer"] = False
            if state["signal"] is not None:
                raise Cancelled("user cancelled")
            if busy is None:
                break
            wait = max(5.0, min(120.0, float(busy.retry_after), 240.0 - waited))
            say("Gemini Live is busy for everyone right now: waiting %d s for a free slot..." % int(round(wait)))
            stage("queue", None, "Waiting %d s for a free Gemini Live slot" % int(round(wait)))
            end = time.time() + wait
            while time.time() < end:
                if state["signal"] is not None:
                    raise Cancelled("user cancelled")
                time.sleep(0.25)
            waited += wait
        finished = run_sessions(job, count)
        result = build_result(job, finished, language)
        if not result["segments"]:
            job.cancel("no speech in the transcript")
            say("ERROR: Gemini Live heard no speech in that audio.")
            return 1
        stage("polish", None, "Placing words (word timing is estimated)")
        if args.roman:
            apply_roman(helpers, result)
        job.done()
        write_outputs(helpers, result, args)
        say("Words: %d in %d line(s); timing estimated from Live utterances (SRT built by %s)."
            % (sum(len(s["words"]) for s in result["segments"]), len(result["segments"]), helpers.source))
        return 0
    except Cancelled:
        if job is not None:
            job.stop_all("user cancelled")
            job.cancel("user cancelled")
        say("Cancelled.")
        return 130
    except LiveError as failure:
        if job is not None:
            job.stop_all(str(failure))
            job.cancel(str(failure))
        say("ERROR: %s" % failure)
        if state["signal"] is None and (failure.kind in ("not_on", "relink", "credits", "busy", "network") or (
                failure.kind != "local" and (job is None or not job.job_id) and not (job and job.dev_key))):
            offer(failure.kind)
        return 1
    except Exception as unexpected:
        if job is not None:
            job.stop_all("internal error")
            job.cancel("internal error: %s" % type(unexpected).__name__)
        say("ERROR: Gemini Live stopped: %s" % unexpected)
        return 1
    finally:
        try:
            if os.path.exists(pcm_path):
                os.remove(pcm_path)
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
