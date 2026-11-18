



























import hashlib
import json
import os
import re
import shutil
import sys
import tarfile
import tempfile
import threading
import time
import wave
from pathlib import Path

ENGINES = ('qwen3-asr', 'moonshine', 'canary', 'sravaani', 'indicconformer')

QWEN_NAMES = {'zh': 'Chinese', 'en': 'English', 'yue': 'Cantonese', 'ar': 'Arabic', 'de': 'German', 'fr': 'French',
              'es': 'Spanish', 'pt': 'Portuguese', 'id': 'Indonesian', 'it': 'Italian', 'ko': 'Korean', 'ru': 'Russian',
              'th': 'Thai', 'vi': 'Vietnamese', 'ja': 'Japanese', 'tr': 'Turkish', 'hi': 'Hindi', 'ms': 'Malay',
              'nl': 'Dutch', 'sv': 'Swedish', 'da': 'Danish', 'fi': 'Finnish', 'pl': 'Polish', 'cs': 'Czech',
              'fil': 'Filipino', 'tl': 'Filipino', 'fa': 'Persian', 'el': 'Greek', 'hu': 'Hungarian',
              'mk': 'Macedonian', 'ro': 'Romanian'}
QWEN_CODES = dict((v.lower(), k) for k, v in QWEN_NAMES.items() if k != 'tl')
QWEN_ALIGN = ('zh', 'en', 'yue', 'fr', 'de', 'it', 'ja', 'ko', 'pt', 'ru', 'es')
INDIC_CODES = ('as', 'bn', 'brx', 'doi', 'gu', 'hi', 'kn', 'kok', 'ks', 'mai', 'ml', 'mni', 'mr', 'ne', 'or', 'pa',
               'sa', 'sat', 'sd', 'ta', 'te', 'ur')
CANARY_CODES = ('bg', 'hr', 'cs', 'da', 'nl', 'en', 'et', 'fi', 'fr', 'de', 'el', 'hu', 'it', 'lv', 'lt', 'mt', 'pl', 'pt',
                'ro', 'sk', 'sl', 'es', 'sv', 'ru', 'uk')
CHUNK_SECONDS = {'qwen3-asr': 28.0, 'moonshine': 0, 'canary': 28.0, 'sravaani': 20.0, 'indicconformer': 15.0}
GATED = {'sravaani': 'https://huggingface.co/ARTPARK-IISc/SraVaani-1.0',
         'indicconformer': 'https://huggingface.co/ai4bharat/indic-conformer-600m-multilingual'}


def custom_on():



    return os.environ.get('FLEX_STT_CUSTOM', '').strip() == '1'


def emit(**kw):
    sys.stdout.write(json.dumps(kw, ensure_ascii=False) + '\n')
    sys.stdout.flush()


def say(msg):
    emit(event='progress', msg=msg)


def hf_token():

    for key in ('HF_TOKEN', 'HUGGING_FACE_HUB_TOKEN'):
        if os.environ.get(key):
            return os.environ[key].strip()
    try:
        with open(os.path.join(os.path.expanduser('~'), '.flexgui', 'hf_token.txt')) as fh:
            tok = fh.read().strip()
            if tok:
                return tok
    except Exception:
        pass
    return None


def gated_message(engine, error):
    text = str(error)
    low = text.lower()
    if engine in GATED and any(k in low for k in ('401', '403', 'gated', 'restricted', 'access to model', 'authenticat', 'awaiting')):
        return ('%s is a gated model on Hugging Face. 1) Sign in at huggingface.co and accept the terms on %s. '
                '2) Create a read token (Settings > Access Tokens) and save it in ~/.flexgui/hf_token.txt. '
                'Then run Auto Captions again. (%s)' % (LABELS[engine], GATED[engine], text.splitlines()[0][:160]))
    return None


LABELS = {'qwen3-asr': 'Qwen3-ASR', 'moonshine': 'Moonshine', 'canary': 'NVIDIA Canary 1B v2', 'sravaani': 'SraVaani 1.0',
          'indicconformer': 'AI4Bharat IndicConformer'}







MIRROR_BASE = "https://github.com/Captureflex1/FlexGUI/releases/download/stt-models-v1/"
MIRROR = {
    "canary": {
        "repo": "nvidia/canary-1b-v2",
        "revision": "d455706339a6b32e1aa40f82c713a482a0c938e2",
        "licence": "CC-BY-4.0",
        "tar_sha256": "9920c4909a33ac3e5d60297cea88c3b8e2202f1b2a97c17905751c5645f0744a",
        "tar_size": 3918458880,
        "extracted_size": 3918441284,
        "files": 10,
        "parts": [
            {
                "name": "stt-canary-d455706.tar.001",
                "size": 1900000000,
                "sha256": "402ac8ba9051e1a4a718372474a61b51b117fd19221531949ecc427b77a7ace4"
            },
            {
                "name": "stt-canary-d455706.tar.002",
                "size": 1900000000,
                "sha256": "b5c8ffabd6a8a4683957d9f078103f302f9028db4a10a9d70d887c1ffe898c6f"
            },
            {
                "name": "stt-canary-d455706.tar.003",
                "size": 118458880,
                "sha256": "00461ddeee4c6274ad16efc6e05a8a4d4934430a4f61303b889c35a013c89d48"
            }
        ]
    },
    "sravaani": {
        "repo": "ARTPARK-IISc/SraVaani-1.0",
        "revision": "f5dd5358325a5208775b91dad98918e079ea2b27",
        "licence": "MIT",
        "tar_sha256": "79e8b62e57e0d6f44bfe25b56f7f4a321051ca2e05cb1be680ede53d4a808093",
        "tar_size": 909352960,
        "extracted_size": 909340934,
        "files": 12,
        "parts": [
            {
                "name": "stt-sravaani-f5dd535.tar.001",
                "size": 909352960,
                "sha256": "79e8b62e57e0d6f44bfe25b56f7f4a321051ca2e05cb1be680ede53d4a808093"
            }
        ]
    },
    "indicconformer": {
        "repo": "ai4bharat/indic-conformer-600m-multilingual",
        "revision": "2a77d305038dfc502fd9464e7d028b90381976cb",
        "licence": "MIT",
        "tar_sha256": "2fff70b7dae80766b53a6f838ab7b1d38718a8b655a7627412adaaa89f3ed492",
        "tar_size": 2556723200,
        "extracted_size": 2556499800,
        "files": 405,
        "parts": [
            {
                "name": "stt-indicconformer-2a77d30.tar.001",
                "size": 1900000000,
                "sha256": "3d94a81188cb4a731b65faa0c6db3c06bc9756db3bc71e82c97709fc8c24768b"
            },
            {
                "name": "stt-indicconformer-2a77d30.tar.002",
                "size": 656723200,
                "sha256": "ac375723bc97d28b52f4e1f245db9325f5c099bc201b929eb84889443c7d4880"
            }
        ]
    }
}

REPOS = {'canary': 'nvidia/canary-1b-v2', 'sravaani': 'ARTPARK-IISc/SraVaani-1.0',
         'indicconformer': 'ai4bharat/indic-conformer-600m-multilingual'}
MIRROR_MARKER = '.flex-mirror.json'
_HEX40 = re.compile(r'^[0-9a-f]{40}$')
_HEX64 = re.compile(r'^[0-9a-f]{64}$')
_PART_NAME = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]{0,150}$')
_RETRY_DELAY = 2.0
_RETRIES = 5
_PROGRESS_BYTES = 1 << 20
_LOCK_STALE = 180.0
_LOCK_BEAT = 10.0
_LOCK_POLL = 2.0
_RENAME_TRIES = 6
_RENAME_DELAY = 1.0
_SPARE_BYTES = 256 * 1024 * 1024


class MirrorError(Exception):
    pass


def _first_line(error):
    return (str(error).strip().splitlines() or [type(error).__name__])[0][:200]


def mirror_entry(engine):


    entry = MIRROR.get(engine)
    if not isinstance(entry, dict):
        return None
    if not _HEX40.match(str(entry.get('revision') or '')) or not _HEX64.match(str(entry.get('tar_sha256') or '')):
        return None
    parts = entry.get('parts')
    if not isinstance(parts, list) or not parts:
        return None
    names, total = set(), 0
    for part in parts:
        if not isinstance(part, dict):
            return None
        name, size = part.get('name'), part.get('size')
        if not isinstance(name, str) or not _PART_NAME.match(name) or name in names:
            return None
        if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
            return None
        if not _HEX64.match(str(part.get('sha256') or '')):
            return None
        names.add(name)
        total += size
    if entry.get('tar_size') and entry.get('tar_size') != total:
        return None
    return entry


def models_dir():


    chosen = os.environ.get('FLEX_STT_MODELS_DIR', '').strip()
    if chosen:
        return chosen
    hf_home = os.environ.get('HF_HOME', '').strip()
    if hf_home:
        return os.path.dirname(os.path.abspath(hf_home))
    try:
        with open(os.path.join(os.path.expanduser('~'), '.flexgui', 'stt_engines.json'), encoding='utf-8') as fh:
            picked = str(json.load(fh).get('models_dir') or '').strip()
            if picked:
                return picked
    except Exception:
        pass
    if sys.platform == 'win32':
        return os.path.join(os.environ.get('APPDATA') or os.path.expanduser('~'), 'Flex', 'stt-engines')
    if sys.platform == 'darwin':
        return os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'Flex', 'stt-engines')
    return os.path.join(os.path.expanduser('~'), '.local', 'share', 'flex', 'stt-engines')


def _offline():
    return os.environ.get('HF_HUB_OFFLINE', '').strip().lower() in ('1', 'true', 'yes', 'on')


def _tq(n):

    n = float(n)
    for unit in ('', 'k', 'M', 'G', 'T'):
        if abs(n) < 999.5:
            if abs(n) < 99.95:
                return ('%1.2f' if abs(n) < 9.995 else '%2.1f') % n + unit
            return '%3.0f' % n + unit
        n /= 1024.0
    return '%3.1fP' % n


def _clock(seconds):
    seconds = int(max(0, seconds))
    if seconds >= 3600:
        return '%d:%02d:%02d' % (seconds // 3600, seconds % 3600 // 60, seconds % 60)
    return '%02d:%02d' % (seconds // 60, seconds % 60)


class _Bar(object):



    def __init__(self, label, total):
        self.label, self.total = label, max(1, int(total))
        self.t0 = time.time()
        self.base = None
        self.pct = -1
        self.at = 0.0

    def show(self, done, final=False):
        now = time.time()
        if self.base is None:
            self.base = done
        pct = max(0, min(100, int(done * 100 / self.total)))
        if not final and (now - self.at < 0.25 or (pct == self.pct and now - self.at < 2.0)):
            return
        self.pct, self.at = pct, now
        elapsed = now - self.t0
        speed = (done - self.base) / elapsed if elapsed > 0.5 else 0.0
        left = _clock((self.total - done) / speed) if speed > 0 else '?'
        rate = (_tq(speed) + 'B/s') if speed > 0 else '?B/s'
        fill = int(pct / 10)
        try:
            sys.stderr.write('%s: %3d%%|%s%s| %s/%s [%s<%s, %s]\n' % (
                self.label, pct, '#' * fill, ' ' * (10 - fill), _tq(done), _tq(self.total), _clock(elapsed), left, rate))
            sys.stderr.flush()
        except Exception:
            pass


class _Lock(object):




    def __init__(self, path, token):
        self.path, self.token = path, token
        self.at = 0.0
        self.lost = False
        self.stop = threading.Event()
        self.beat = threading.Thread(target=self._beat, name='flex-mirror-lock')
        self.beat.daemon = True
        self.beat.start()

    def _beat(self):
        while not self.stop.wait(_LOCK_BEAT):
            try:
                if self.ours():
                    self.touch(force=True)
                else:
                    self.lost = True
            except Exception:
                pass

    def check(self):

        if self.lost:
            raise MirrorError('another Flex app took this download over')

    def touch(self, force=False):
        now = time.time()
        if force or now - self.at >= 5.0:
            self.at = now
            try:
                os.utime(self.path, None)
            except OSError:
                pass

    def ours(self):

        try:
            with open(self.path, 'r') as fh:
                return fh.read().strip() == self.token
        except OSError:
            return False

    def release(self):
        self.stop.set()
        if self.ours():
            try:
                os.remove(self.path)
            except OSError:
                pass


def _pid_alive(pid):

    if pid <= 0 or pid == os.getpid():
        return False
    if os.name == 'nt':
        try:
            import ctypes
            kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
            handle = kernel32.OpenProcess(0x1000, False, pid)
            if not handle:
                return ctypes.get_last_error() != 87
            code = ctypes.c_ulong()
            ok = kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
            kernel32.CloseHandle(handle)
            return not ok or code.value == 259
        except Exception:
            return True
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except Exception:
        return True
    return True


def _lock_owner(path):

    try:
        with open(path, 'r') as fh:
            m = re.match(r'\s*(\d+)', fh.read())
        pid = int(m.group(1)) if m else 0
        return pid if pid > 0 else None
    except (OSError, ValueError):
        return None


def _take_lock(engine, work, dest, entry):






    path = os.path.join(work, '.lock')
    token = '%d %s' % (os.getpid(), hashlib.sha256(os.urandom(16)).hexdigest()[:16])
    waited, fails = False, 0
    seen, quiet, tick = None, 0.0, time.monotonic()
    while True:
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, token.encode('ascii'))
            os.close(fd)
            return _Lock(path, token)
        except OSError as lock_error:
            if mirror_complete(dest, entry):
                return None
            if not os.path.isdir(work):
                os.makedirs(work, exist_ok=True)
                continue
            if not os.path.exists(path):
                fails += 1
                if fails >= 3:
                    raise MirrorError('cannot write in %s (%s)' % (work, _first_line(lock_error)))
                continue
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            continue
        now = time.monotonic()
        if mtime != seen:
            seen, quiet = mtime, 0.0
        else:
            quiet += min(now - tick, _LOCK_POLL * 2.5)
        tick = now
        age = time.time() - mtime
        owner = _lock_owner(path)
        if owner is not None:
            gone = not _pid_alive(owner) or (age > _LOCK_STALE and quiet > _LOCK_STALE)
        else:
            gone = age > _LOCK_STALE
        if gone:
            try:
                os.remove(path)
            except OSError:
                time.sleep(1.0)
            seen = None
            continue
        if not waited:
            say('%s: another Flex app is downloading it from the Flex mirror; waiting for it to finish...' % LABELS[engine])
            waited = True
        time.sleep(_LOCK_POLL)


def mirror_complete(dest, entry):

    try:
        with open(os.path.join(dest, MIRROR_MARKER), 'r', encoding='utf-8') as fh:
            info = json.load(fh)
        if info.get('tar_sha256') != entry['tar_sha256'] or info.get('revision') != entry['revision']:
            return False
        for name, size in info.get('files') or []:
            if os.path.getsize(os.path.join(dest, *name.split('/'))) != size:
                return False
        return True
    except Exception:
        return False


def _have(path, size):
    try:
        return min(size, os.path.getsize(path))
    except OSError:
        return 0


_SSL_CONTEXT = []


def _ssl_context():




    if not _SSL_CONTEXT:
        import ssl
        ctx = ssl.create_default_context()
        try:
            import certifi
            ctx.load_verify_locations(cafile=certifi.where())
        except Exception:
            pass
        _SSL_CONTEXT.append(ctx)
    return _SSL_CONTEXT[0]


class _Odd(Exception):
    pass


def _fetch_part(url, path, size, progress):





    import ssl
    import urllib.error
    import urllib.request
    from http.client import HTTPException
    last, fails = None, 0
    while True:
        have = os.path.getsize(path) if os.path.exists(path) else 0
        if have > size:
            os.remove(path)
            have = 0
        if have == size:
            return
        if fails >= _RETRIES:
            break
        if fails:
            time.sleep(_RETRY_DELAY * fails)
        headers = {'User-Agent': 'Flex-AutoCaptions', 'Accept': 'application/octet-stream'}
        if have:
            headers['Range'] = 'bytes=%d-%d' % (have, size - 1)
        start = got = have
        try:
            resp = urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60,
                                          context=_ssl_context())
            try:
                if have and resp.getcode() != 206:
                    start = got = have = 0
                elif have:
                    m = re.match(r'bytes\s+(\d+)-', resp.headers.get('Content-Range') or '')
                    if not m or int(m.group(1)) != have:
                        os.remove(path)
                        raise _Odd('the server answered a different range')
                with open(path, 'ab' if have else 'wb') as out:
                    while True:
                        chunk = resp.read(1 << 20)
                        if not chunk:
                            break
                        got += len(chunk)
                        if got > size:
                            out.close()
                            os.remove(path)
                            raise MirrorError('%s is larger than the app expects' % os.path.basename(path))
                        out.write(chunk)
                        progress(got)
            finally:
                resp.close()
        except MirrorError:
            raise
        except _Odd as odd:
            last = odd
        except urllib.error.HTTPError as http_error:
            if http_error.code == 416:
                try:
                    os.remove(path)
                except OSError:
                    pass
            elif http_error.code in (401, 403, 404, 410):
                raise MirrorError('HTTP %d for %s' % (http_error.code, os.path.basename(path)))
            last = http_error
        except (OSError, HTTPException, ValueError) as net_error:
            if getattr(net_error, 'errno', None) == 28:
                raise MirrorError('the disk is full')
            reason = getattr(net_error, 'reason', None)
            if isinstance(net_error, ssl.CertificateError) or isinstance(reason, ssl.CertificateError):
                raise MirrorError("the mirror's certificate could not be checked (%s)" % _first_line(reason or net_error))
            last = net_error
        fails = 1 if got - start >= min(_PROGRESS_BYTES, size - start) else fails + 1
    raise MirrorError('could not download %s (%s)' % (os.path.basename(path), _first_line(last or 'no data')))


def _check_parts(parts, work, lock=None):

    whole, bad = hashlib.sha256(), []
    for part in parts:
        h = hashlib.sha256()
        with open(os.path.join(work, part['name']), 'rb') as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b''):
                h.update(chunk)
                whole.update(chunk)
                if lock is not None:
                    lock.touch()
                    lock.check()
        if h.hexdigest() != part['sha256']:
            bad.append(part)
    return bad, whole.hexdigest()


def _download(engine, entry, work, lock):
    from urllib.parse import quote
    parts = entry['parts']
    total = sum(p['size'] for p in parts)
    bar = _Bar('%s from the Flex mirror' % LABELS[engine], total)
    rejected = set()
    while True:
        for i, part in enumerate(parts):
            others = sum(_have(os.path.join(work, p['name']), p['size']) for j, p in enumerate(parts) if j != i)

            def progress(have, others=others):
                bar.show(others + have)
                lock.touch()
                lock.check()
            progress(_have(os.path.join(work, part['name']), part['size']))
            _fetch_part(MIRROR_BASE + quote(part['name']), os.path.join(work, part['name']), part['size'], progress)
        bar.show(total, final=True)
        say('%s: checking the download...' % LABELS[engine])
        bad, whole = _check_parts(parts, work, lock)
        if not bad:
            break
        for part in bad:
            os.remove(os.path.join(work, part['name']))
            if part['name'] in rejected:
                raise MirrorError('%s failed its checksum twice' % part['name'])
            rejected.add(part['name'])
        say('%s: %s failed its checksum; downloading it again...' % (LABELS[engine], ', '.join(p['name'] for p in bad)))
    if whole != entry['tar_sha256']:
        raise MirrorError('the joined parts do not match the archive checksum')


class _Joined(object):



    def __init__(self, paths):
        self.paths, self.i, self.fh = list(paths), 0, None
        self.hash, self.size = hashlib.sha256(), 0

    def read(self, n=-1):
        data = self._read(n)
        self.hash.update(data)
        self.size += len(data)
        return data

    def drain(self):
        while self.read(1 << 20):
            pass

    def _read(self, n=-1):
        out, need = [], n
        while self.i < len(self.paths) and (n < 0 or need > 0):
            if self.fh is None:
                self.fh = open(self.paths[self.i], 'rb')
            chunk = self.fh.read(-1 if n < 0 else need)
            if not chunk:
                self.fh.close()
                self.fh, self.i = None, self.i + 1
                continue
            out.append(chunk)
            if n >= 0:
                need -= len(chunk)
        return b''.join(out)

    def close(self):
        if self.fh is not None:
            self.fh.close()
            self.fh = None


def _member_path(name):


    if not isinstance(name, str) or not name or '\x00' in name or '\\' in name:
        raise MirrorError('the archive holds an unsafe name (%r)' % (name,))
    if name.startswith('/') or re.match(r'^[A-Za-z]:', name):
        raise MirrorError('the archive holds an absolute path (%s)' % name)
    parts = [p for p in name.split('/') if p not in ('', '.')]
    if not parts or any(p == '..' or ':' in p for p in parts):
        raise MirrorError('the archive holds a path outside its folder (%s)' % name)
    return '/'.join(parts)


def _rename_dir(src, dst):


    for attempt in range(1, _RENAME_TRIES + 1):
        try:
            os.rename(src, dst)
            return
        except PermissionError:
            if attempt == _RENAME_TRIES:
                raise
            time.sleep(_RENAME_DELAY * attempt)


def _leftovers(dest):


    work = dest + '.download'
    owner = _lock_owner(os.path.join(work, '.lock'))
    if owner is not None and owner != os.getpid() and _pid_alive(owner):
        return
    for old in (work, dest + '.extract'):
        if os.path.isdir(old):
            shutil.rmtree(old, ignore_errors=True)


def _extract(engine, entry, work, dest, lock):

    say('%s: unpacking...' % LABELS[engine])
    staging = dest + '.extract'
    for old in (staging, dest):
        if os.path.isdir(old):
            shutil.rmtree(old)
    os.makedirs(staging)
    root = os.path.realpath(staging)
    limit = entry.get('extracted_size') or 0
    reader = _Joined(os.path.join(work, p['name']) for p in entry['parts'])
    files, seen, total = [], set(), 0
    try:
        with tarfile.open(fileobj=reader, mode='r|') as tar:
            for member in tar:
                rel = _member_path(member.name)
                target = os.path.join(staging, *rel.split('/'))
                if not os.path.realpath(target).startswith(root + os.sep):
                    raise MirrorError('the archive holds a path outside its folder (%s)' % member.name)
                if member.isdir():
                    os.makedirs(target, exist_ok=True)
                    continue
                if not member.isreg():
                    raise MirrorError('the archive holds a link or special file (%s)' % member.name)
                if rel in seen or rel == MIRROR_MARKER:
                    raise MirrorError('the archive holds %s twice' % rel)
                seen.add(rel)
                total += member.size
                if limit and total > limit:
                    raise MirrorError('the archive is larger than the app expects')
                parent = os.path.dirname(target)
                if not os.path.isdir(parent):
                    os.makedirs(parent)
                src = tar.extractfile(member)
                with open(target, 'wb') as out:
                    shutil.copyfileobj(src, out, 1 << 20)
                files.append([rel, member.size])
                lock.touch()
                lock.check()
        if limit and total != limit:
            raise MirrorError('the archive is smaller than the app expects')
        reader.drain()
        if reader.hash.hexdigest() != entry['tar_sha256'] or (entry.get('tar_size') and reader.size != entry['tar_size']):
            raise MirrorError('the parts changed on disk while they were unpacked')
        if not lock.ours():
            raise MirrorError('another Flex app took this download over')
        with open(os.path.join(staging, MIRROR_MARKER), 'w', encoding='utf-8') as fh:
            json.dump({'engine': engine, 'repo': entry.get('repo'), 'revision': entry['revision'],
                       'tar_sha256': entry['tar_sha256'], 'files': files,
                       'at': time.strftime('%Y-%m-%dT%H:%M:%S')}, fh)
        _rename_dir(staging, dest)
    except BaseException:
        reader.close()
        if lock.ours():
            shutil.rmtree(staging, ignore_errors=True)
        raise
    reader.close()


def mirror_fetch(engine, entry):


    root = os.path.join(models_dir(), 'mirror', engine)
    dest = os.path.join(root, entry['revision'])
    if mirror_complete(dest, entry):
        if os.path.isdir(dest + '.download') or os.path.isdir(dest + '.extract'):
            _leftovers(dest)
        return dest
    if _offline():
        raise MirrorError('HF_HUB_OFFLINE is set and the mirror copy is not on this computer')
    work = dest + '.download'
    os.makedirs(work, exist_ok=True)
    lock = _take_lock(engine, work, dest, entry)
    if lock is None:
        return dest
    done = False
    try:
        if mirror_complete(dest, entry):
            return dest


        for old in (dest + '.extract', dest):
            if os.path.isdir(old):
                shutil.rmtree(old)
        missing = sum(p['size'] - _have(os.path.join(work, p['name']), p['size']) for p in entry['parts'])
        need = missing + (entry.get('extracted_size') or entry.get('tar_size') or 0) + _SPARE_BYTES
        free = shutil.disk_usage(work).free
        if free < need:
            raise MirrorError('not enough free space in %s (%s needed, %s free)' % (root, _tq(need) + 'B', _tq(free) + 'B'))
        say('%s: downloading %sB from the Flex mirror (no Hugging Face account needed)...' % (LABELS[engine], _tq(missing)))
        _download(engine, entry, work, lock)
        _extract(engine, entry, work, dest, lock)
        done = True
    finally:
        lock.release()
    if done:
        shutil.rmtree(work, ignore_errors=True)
        say('%s: the Flex mirror copy is ready.' % LABELS[engine])
    return dest


def model_source(engine):


    repo = REPOS[engine]
    entry = mirror_entry(engine)
    if entry is None:
        return repo
    try:
        return mirror_fetch(engine, entry)
    except Exception as mirror_error:
        say('%s: the Flex mirror did not work (%s) - downloading from Hugging Face instead.' % (LABELS[engine], _first_line(mirror_error)))
        return repo


def load_model(engine, from_hub, from_folder=None):



    repo = REPOS[engine]
    source = model_source(engine)
    if source == repo:
        return from_hub(repo)
    try:
        return (from_folder or from_hub)(source)
    except ImportError:
        raise
    except Exception as load_error:
        say('%s: the Flex mirror copy did not load (%s) - trying Hugging Face instead.' % (LABELS[engine], _first_line(load_error)))
        return from_hub(repo)


def indic_from_folder(folder):



    from transformers.dynamic_module_utils import get_class_from_dynamic_module
    with open(os.path.join(folder, 'config.json'), 'r', encoding='utf-8') as fh:
        auto = json.load(fh).get('auto_map') or {}
    config_class = get_class_from_dynamic_module(auto.get('AutoConfig') or 'model_onnx.IndicASRConfig', folder)
    model_class = get_class_from_dynamic_module(auto.get('AutoModel') or 'model_onnx.IndicASRModel', folder)
    return model_class(config_class(ts_folder=folder))


def read_wav(path):

    import numpy as np
    with wave.open(path, 'rb') as w:
        ch, width, rate, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        raw = w.readframes(n)
    if width == 2:
        a = np.frombuffer(raw, dtype='<i2').astype('float32') / 32768.0
    elif width == 4:
        a = np.frombuffer(raw, dtype='<i4').astype('float32') / 2147483648.0
    else:
        a = (np.frombuffer(raw, dtype='u1').astype('float32') - 128.0) / 128.0
    if ch > 1:
        a = a.reshape(-1, ch).mean(axis=1)
    if rate != 16000 and len(a):
        idx = np.arange(0, len(a), rate / 16000.0)
        a = np.interp(idx, np.arange(len(a)), a).astype('float32')
    return a


def chunks(a, max_seconds, sr=16000):


    import numpy as np
    n, hop = len(a), int(0.02 * sr)
    if n == 0:
        return []
    frames = n // hop
    e = np.sqrt(np.mean(a[:frames * hop].reshape(frames, hop) ** 2, axis=1)) if frames else np.zeros(1)
    out, start, limit = [], 0, int(max_seconds * sr)
    while start < n:
        end = min(n, start + limit)
        if end < n:
            f0, f1 = (start + limit // 2) // hop, max((start + limit // 2) // hop + 1, end // hop)
            k = f0 + int(np.argmin(e[f0:f1]))
            end = max(start + hop, min(n, k * hop + hop // 2))
        piece = a[start:end]
        if len(piece) and float(np.max(np.abs(piece))) > 0.003:
            out.append((start, end))
        start = end
    return out


def attach_punctuation(items, text, joiner):

    toks = text.split() if joiner == ' ' else []
    out, j = [], 0
    for it in items:
        word = it['word']
        if toks:
            bare = ''.join(c for c in word.lower() if c.isalnum())
            for k in range(j, min(len(toks), j + 4)):
                if ''.join(c for c in toks[k].lower() if c.isalnum()) == bare and bare:
                    word, j = toks[k], k + 1
                    break
        out.append(dict(it, word=word))
    return out




_PUNCT_BEFORE = re.compile(r'\s+([,.!?;:%)\]}\u0964\u0965\u2026\u3001\u3002]+)')
_PUNCT_AFTER = re.compile(r'([(\[{])\s+')


def _bare(word):
    return ''.join(c for c in word.lower() if c.isalnum())


def tidy_text(text):
    return re.sub(r'\s{2,}', ' ', _PUNCT_AFTER.sub(r'\1', _PUNCT_BEFORE.sub(r'\1', text or ''))).strip()


def tidy_words(words):
    out = []
    for w in words:
        t = (w.get('word') or '').strip()
        if not t:
            continue
        if not _bare(t):
            if out:
                out[-1] = dict(out[-1], word=out[-1]['word'] + t, end=max(out[-1]['end'], w.get('end', out[-1]['end'])))
            else:
                out.append(dict(w, word=t))
            continue
        if out and not _bare(out[-1]['word']):
            t = out[-1]['word'] + t
            w = dict(w, start=out[-1]['start'])
            out.pop()
        out.append(dict(w, word=t))
    return out


def tidy_segments(segs):
    return [dict(s, text=tidy_text(s.get('text')), words=tidy_words(s.get('words') or [])) for s in segs]


def drop_repeated_head(prev, words, most=5):



    if not prev or not words:
        return words
    for k in range(min(most, len(prev), len(words)), 0, -1):
        if all(_bare(prev[len(prev) - k + i]['word']) == _bare(words[i]['word']) for i in range(k)) \
                and words[0]['start'] < prev[-1]['end'] + 0.3:
            return words[k:]
    return words



class Moonshine(object):

    def __init__(self):
        import moonshine_voice
        self.mv = moonshine_voice
        self.cache = {}

    def get(self, lang):
        if lang not in self.cache:
            say('Moonshine: getting the %s model (first use downloads it)...' % lang)
            root = os.environ.get('FLEX_MOONSHINE_CACHE')
            path, arch = self.mv.get_model_for_language(lang, None, include_word_timestamps=True,
                                                        cache_root=Path(root) if root else None)
            self.cache[lang] = self.mv.Transcriber(model_path=path, model_arch=arch, options={'word_timestamps': True})
        return self.cache[lang]

    def transcribe(self, a, language, keyterms):
        lang = {'fil': 'tl'}.get(language or 'en', language or 'en')
        if lang not in self.mv.supported_languages():
            raise ValueError('Moonshine has no %s model (it does %s).' % (lang, ', '.join(self.mv.supported_languages())))
        tr = self.get(lang)
        if keyterms:
            try:
                tr.set_keyterms(list(keyterms))
            except Exception:
                pass
        res = tr.transcribe_without_streaming(a.tolist(), 16000)
        segs, prev = [], []
        for line in res.lines:
            words = []
            for w in (line.words or []):
                t = (w.word or '').strip()
                if not t:
                    continue
                cur = {'word': t, 'start': float(w.start), 'end': float(w.end), 'probability': float(w.confidence)}
                last = words[-1] if words else (prev[-1] if prev else None)

                if last and _bare(t) == _bare(last['word']) and cur['end'] - cur['start'] < 0.05:
                    continue
                words.append(cur)
            words = drop_repeated_head(prev, words)
            if not words and not (line.text or '').strip():
                continue
            if words:
                prev = words
            text = ' '.join(x['word'] for x in words) if words else line.text.strip()
            segs.append({'start': float(line.start_time), 'end': float(line.start_time + line.duration), 'text': text, 'words': words})
        return lang, segs


class Qwen(object):


    def __init__(self):
        import torch
        from qwen_asr import Qwen3ASRModel
        self.torch = torch
        cuda = torch.cuda.is_available()
        self.device = 'cuda:0' if cuda else 'cpu'
        self.dtype = torch.bfloat16 if cuda else torch.float32
        say('Qwen3-ASR: loading the 0.6B model on %s (first use downloads ~1.9 GB)...' % ('the GPU' if cuda else 'the CPU'))
        self.model = Qwen3ASRModel.from_pretrained('Qwen/Qwen3-ASR-0.6B', dtype=self.dtype, device_map=self.device,
                                                   max_inference_batch_size=4, max_new_tokens=1024)
        self.aligner = None

    def align_model(self):
        if self.aligner is None:
            from qwen_asr import Qwen3ForcedAligner
            say('Qwen3-ASR: loading the word aligner (first use downloads ~1.9 GB)...')
            self.aligner = Qwen3ForcedAligner.from_pretrained('Qwen/Qwen3-ForcedAligner-0.6B', dtype=self.dtype, device_map=self.device)
        return self.aligner

    def transcribe(self, a, language, keyterms):
        sr, segs, detected = 16000, [], None
        name = QWEN_NAMES.get(language) if language else None
        for (s, e) in chunks(a, CHUNK_SECONDS['qwen3-asr']):
            piece = a[s:e]
            r = self.model.transcribe(audio=(piece, sr), language=name)[0]
            text = (r.text or '').strip()
            if not text:
                continue
            code = QWEN_CODES.get(str(r.language or '').lower(), language)
            detected = detected or code
            words = []
            if code in QWEN_ALIGN:
                try:
                    items = self.align_model().align(audio=(piece, sr), text=text, language=QWEN_NAMES[code])[0]
                    joiner = '' if code in ('zh', 'ja', 'yue') else ' '
                    words = attach_punctuation([{'word': str(it.text), 'start': s / sr + float(it.start_time),
                                                 'end': s / sr + float(it.end_time), 'probability': 1.0} for it in items], text, joiner)
                except Exception as align_error:
                    say('Qwen3-ASR: word aligner skipped a chunk (%s); Whisper will time it.' % str(align_error).splitlines()[0][:120])
                    words = []
            segs.append({'start': s / sr, 'end': e / sr, 'text': text, 'words': words})
        return detected or language, segs


class Canary(object):


    def __init__(self):
        import torch
        from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq
        self.torch = torch
        dev = 'cuda' if torch.cuda.is_available() else 'cpu'
        say('NVIDIA Canary 1B v2: loading (first use downloads ~4 GB)...')

        def load(name):
            return AutoProcessor.from_pretrained(name), AutoModelForSpeechSeq2Seq.from_pretrained(name).to(dev).eval()
        self.processor, self.model = load_model('canary', load)

    def transcribe(self, a, language, keyterms):
        lang = language or 'en'
        if lang not in CANARY_CODES:
            raise ValueError('Canary does not cover "%s" (it does %s).' % (lang, ', '.join(CANARY_CODES)))
        sr, segs = 16000, []
        for (s, e) in chunks(a, CHUNK_SECONDS['canary']):
            inputs = self.processor.apply_transcription_request(audio=a[s:e], source_language=lang).to(self.model.device)
            with self.torch.inference_mode():
                ids = self.model.generate(**inputs, max_new_tokens=448)
            text = str(self.processor.decode(ids, skip_special_tokens=True)[0] or '').strip()
            if text:
                segs.append({'start': s / sr, 'end': e / sr, 'text': text, 'words': []})
        return lang, segs


class SraVaani(object):

    def __init__(self):
        import torch
        from transformers import AutoModel
        dev = 'cuda' if torch.cuda.is_available() else 'cpu'
        say('SraVaani 1.0: loading (first use downloads ~900 MB)...')
        self.model = load_model('sravaani', lambda name: AutoModel.from_pretrained(name, trust_remote_code=True,
                                                                                    token=hf_token()).to(dev).eval())

    def transcribe(self, a, language, keyterms):
        sr, segs, paths, spans = 16000, [], [], chunks(a, CHUNK_SECONDS['sravaani'])
        tmp = tempfile.mkdtemp(prefix='flex-sravaani-')
        try:
            for i, (s, e) in enumerate(spans):
                p = os.path.join(tmp, '%05d.wav' % i)
                write_wav(p, a[s:e])
                paths.append(p)
            if not paths:
                return language, []
            hyps = self.model.transcribe(paths, return_hypotheses=True)
            if isinstance(hyps, tuple):
                hyps = hyps[0]
            for (s, e), h in zip(spans, hyps):
                text = (getattr(h, 'text', None) if not isinstance(h, str) else h) or ''
                text = str(text).strip()
                if text:
                    segs.append({'start': s / sr, 'end': e / sr, 'text': text, 'words': []})
        finally:
            for p in paths:
                try:
                    os.remove(p)
                except OSError:
                    pass
            try:
                os.rmdir(tmp)
            except OSError:
                pass
        return language, segs


class IndicConformer(object):


    def __init__(self):
        import torch
        from transformers import AutoModel
        self.torch = torch
        say('AI4Bharat IndicConformer: loading (first use downloads ~2.4 GB)...')
        self.model = load_model('indicconformer',
                                lambda name: AutoModel.from_pretrained(name, trust_remote_code=True, token=hf_token()),
                                indic_from_folder)

    def transcribe(self, a, language, keyterms):
        lang = language or 'hi'
        if lang not in INDIC_CODES:
            raise ValueError('IndicConformer does not cover "%s" (it does %s).' % (lang, ', '.join(INDIC_CODES)))
        sr, segs = 16000, []
        for (s, e) in chunks(a, CHUNK_SECONDS['indicconformer']):
            wav = self.torch.from_numpy(a[s:e].copy()).unsqueeze(0)
            with self.torch.inference_mode():
                text = self.model(wav, lang, 'rnnt')
            if isinstance(text, (list, tuple)):
                text = text[0] if text else ''
            text = str(text or '').strip()
            if text:
                segs.append({'start': s / sr, 'end': e / sr, 'text': text, 'words': []})
        return lang, segs


def write_wav(path, a):
    import numpy as np
    pcm = (np.clip(a, -1, 1) * 32767).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(pcm.tobytes())


def make(engine):
    return {'qwen3-asr': Qwen, 'moonshine': Moonshine, 'canary': Canary, 'sravaani': SraVaani,
            'indicconformer': IndicConformer}[engine]()


class _LineBars(object):



    def __init__(self, stream):
        self.stream = stream

    def write(self, text):
        return self.stream.write(text.replace('\r', '\n') if '\r' in text else text)

    def flush(self):
        self.stream.flush()

    def __getattr__(self, name):
        return getattr(self.stream, name)


def serve(engine):
    sys.stderr = _LineBars(sys.stderr)
    try:
        model = make(engine)
    except ModuleNotFoundError as missing:
        emit(event='need', module=missing.name or str(missing))
        return
    except Exception as load_error:
        emit(event='error', id=None, error=gated_message(engine, load_error) or '%s could not load: %s' % (LABELS[engine], load_error))
        return
    emit(event='ready')
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            job = json.loads(line)
        except Exception:
            emit(event='error', id=None, error='bad request')
            continue
        if job.get('quit'):
            break
        try:
            a = read_wav(job['audio'])
            keyterms = (job.get('keyterms') or []) if custom_on() else []
            lang, segs = model.transcribe(a, job.get('language') or None, keyterms)
            emit(event='result', id=job.get('id'), language=lang, segments=tidy_segments(segs))
        except ModuleNotFoundError as missing:
            emit(event='need', module=missing.name or str(missing))
            return
        except Exception as e:
            emit(event='error', id=job.get('id'), error=gated_message(engine, e) or '%s: %s' % (type(e).__name__, e))


def prefetch(engine, language):

    try:
        model = make(engine)
        if engine == 'moonshine':
            model.get({'fil': 'tl'}.get(language or 'en', language or 'en'))
        elif engine == 'qwen3-asr':
            model.align_model()
    except ModuleNotFoundError as missing:
        emit(event='need', module=missing.name or str(missing))
        return 3
    except Exception as e:
        emit(event='error', id=None, error=gated_message(engine, e) or '%s could not load: %s' % (LABELS[engine], e))
        return 1
    emit(event='ready')
    return 0


if __name__ == '__main__':
    args = sys.argv[1:]
    if '--prefetch' in args and '--engine' in args:
        lang = args[args.index('--language') + 1] if '--language' in args else None
        sys.exit(prefetch(args[args.index('--engine') + 1], lang))
    if '--serve' in args and '--engine' in args:
        eng = args[args.index('--engine') + 1]
        if eng not in ENGINES:
            emit(event='error', id=None, error='unknown engine ' + eng)
            sys.exit(2)
        serve(eng)
    else:
        print(__doc__)
