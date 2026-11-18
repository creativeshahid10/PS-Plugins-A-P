import os
import sys
import argparse
import json
import time
import contextlib
import re
import tempfile
import warnings
import typing




















_BACKPORTED = [
    "TypeGuard", "TypeAlias", "ParamSpec", "ParamSpecArgs", "ParamSpecKwargs",
    "Concatenate", "Self", "Never", "Unpack", "TypeVarTuple", "LiteralString",
    "NotRequired", "Required", "assert_never", "override", "dataclass_transform",
]

_missing = [n for n in _BACKPORTED if not hasattr(typing, n)]
if _missing:
    try:
        import typing_extensions
    except ImportError:
        typing_extensions = None

    if typing_extensions is None:
        print(
            "ERROR: This Python (%d.%d, %s) is too old for Whisper's dependencies, "
            "and typing_extensions is not installed to bridge the gap.\n"
            "  Fix A (best): install Python 3.11 or 3.12 and run Install / Fix "
            "Dependencies again — Whisper's dependencies target 3.10 and newer.\n"
            "  Fix B (quick): \"%s\" -m pip install typing_extensions"
            % (sys.version_info[0], sys.version_info[1], sys.executable, sys.executable)
        )
        sys.exit(1)

    _unbridged = []
    for _name in _missing:
        if hasattr(typing_extensions, _name):
            setattr(typing, _name, getattr(typing_extensions, _name))
        else:
            _unbridged.append(_name)

    if _unbridged:
        print(
            "ERROR: Python %d.%d is missing %s, and the installed typing_extensions "
            "cannot supply %s.\n"
            "  Fix A (best): install Python 3.11 or 3.12 and run Install / Fix Dependencies again.\n"
            "  Fix B: \"%s\" -m pip install --upgrade typing_extensions"
            % (sys.version_info[0], sys.version_info[1], ", ".join(_missing),
               ", ".join(_unbridged), sys.executable)
        )
        sys.exit(1)


warnings.filterwarnings("ignore")


def _flex_run(args, timeout=900):
    import subprocess
    try:
        return subprocess.run(args, capture_output=True, text=True, errors="replace", timeout=timeout)
    except Exception as e:
        class _R(object):
            returncode = 1
            stdout = ""
            stderr = str(e)
        return _R()


def _flex_numpy_cap(numba_err=""):


    m = re.search(r"Numba needs NumPy (\d+)\.(\d+) or less", numba_err or "")
    if m:
        return "numpy<%d.%d" % (int(m.group(1)), int(m.group(2)) + 1)
    try:
        import importlib.metadata as md
        for req in md.requires("numba") or []:
            r = req.split(";")[0].replace(" ", "").replace("(", "").replace(")", "")
            if r.lower().startswith("numpy") and "<" in r:
                return "numpy" + r[5:]
    except Exception:
        pass
    return "numpy<2.5"


def _flex_fix_numpy(spec=None, say=None):





    import site
    say = say or (lambda s: (print("FLEX_FIX " + s), sys.stdout.flush()))
    py = sys.executable
    probe = _flex_run([py, "-c", "import numba"], 120)
    spec = spec or _flex_numpy_cap(getattr(probe, "stderr", ""))
    say("step Target: %s (Python %s)" % (spec, py))
    dirs = []
    try:
        dirs = list(site.getsitepackages())
    except Exception:
        pass
    try:
        dirs.append(site.getusersitepackages())
    except Exception:
        pass
    dirs += [p for p in sys.path if p.rstrip("/\\").endswith(("site-packages", "dist-packages"))]
    removed = 0
    for d in sorted(set(dirs)):
        try:
            names = os.listdir(d)
        except Exception:
            continue
        for n in names:
            if n.startswith("~") and "umpy" in n.lower():
                full = os.path.join(d, n)
                try:
                    import shutil
                    if os.path.isdir(full):
                        shutil.rmtree(full)
                    else:
                        os.remove(full)
                    removed += 1
                except Exception as e:
                    say("warn Could not delete leftover %s: %s" % (full, e))
    if removed:
        say("step Deleted %d half-removed NumPy leftover%s" % (removed, "" if removed == 1 else "s"))
    locked = False
    for i in range(5):
        shown = _flex_run([py, "-m", "pip", "show", "--disable-pip-version-check", "numpy"], 120)
        if shown.returncode != 0:
            break
        loc = re.search(r"^Location:\s*(.+)$", shown.stdout or "", re.M)
        ver = re.search(r"^Version:\s*(.+)$", shown.stdout or "", re.M)
        say("step Removing NumPy %s from %s" % (ver.group(1).strip() if ver else "?", loc.group(1).strip() if loc else "?"))
        un = _flex_run([py, "-m", "pip", "uninstall", "-y", "--disable-pip-version-check", "numpy"], 300)
        if un.returncode != 0:
            text = (un.stdout or "") + (un.stderr or "")
            if re.search(r"WinError 5|Access is denied|being used by another process|PermissionError", text):
                locked = True
            say("warn Could not remove it (%s); the new copy will be installed for this user instead"
                % (text.strip().splitlines() or ["no reason given"])[-1][:160])
            break
    ok_install = False
    for extra in ([], ["--user"], ["--user", "--break-system-packages"]):
        r = _flex_run([py, "-m", "pip", "install", "--disable-pip-version-check", "--no-cache-dir",
                       "--force-reinstall", "--no-deps", spec] + extra, 900)
        if r.returncode == 0:
            ok_install = True
            break
        text = (r.stdout or "") + (r.stderr or "")
        if re.search(r"WinError 5|Access is denied|being used by another process", text):
            locked = True
    if not ok_install:
        if locked:
            return False, ("NumPy is in use by another program. Close running caption jobs (or restart "
                           "the Adobe app) and press FIX NUMPY again.")
        return False, ("NumPy could not be installed. Run this once in a terminal: \"%s\" -m pip install \"%s\""
                       % (py, spec))
    check = _flex_run([py, "-c", "import numpy; print(numpy.__version__)\n"
                                 "try:\n import numba; print(numba.__version__)\n"
                                 "except ImportError as e:\n print('no-numba' if 'No module named' in str(e) else 'ERR ' + str(e))"], 300)
    lines = (check.stdout or "").strip().splitlines()
    if check.returncode != 0 or len(lines) < 2 or lines[1].startswith("ERR"):
        detail = (lines[1] if len(lines) > 1 else (check.stderr or "").strip().splitlines()[-1:] or ["?"])
        return False, "NumPy was reinstalled but still does not load: %s" % (detail if isinstance(detail, str) else detail[0])[:200]
    msg = "NumPy %s is ready%s." % (lines[0], "" if lines[1] == "no-numba" else " (numba %s)" % lines[1])
    return True, msg












def _flex_numpy_guard():
    if os.environ.get("FLEX_NUMPY_REPAIRED"):
        return
    try:
        import importlib.util
        import subprocess
        if importlib.util.find_spec("numba") is None:
            return
        probe = subprocess.run([sys.executable, "-c", "import numba"],
                               capture_output=True, text=True, errors="replace")
        if probe.returncode == 0:
            return
        if not re.search(r"Numba needs NumPy (\d+)\.(\d+) or less|numpy|NumPy", probe.stderr or ""):
            return
        spec = _flex_numpy_cap(probe.stderr)
    except Exception:
        return
    print("Repairing Python packages: Whisper's numba needs %s (one time)..." % spec)
    sys.stdout.flush()
    ok, msg = _flex_fix_numpy(spec, lambda s: (print("  " + s.split(" ", 1)[-1]), sys.stdout.flush()))
    if ok:
        print(msg + " Starting again.")
        sys.stdout.flush()
        env = dict(os.environ, FLEX_NUMPY_REPAIRED="1")
        sys.exit(subprocess.call([sys.executable] + sys.argv, env=env))
    print("ERROR: Error loading Whisper model: numba needs %s and the automatic repair did not work: %s\n"
          "  Press FIX NUMPY in AutoCaptions to try again." % (spec, msg))
    sys.exit(1)


if __name__ == "__main__" and "--fix-numpy" in sys.argv[1:]:
    _ok, _msg = _flex_fix_numpy()
    print(("FLEX_FIX OK " if _ok else "FLEX_FIX FAIL ") + _msg)
    sys.stdout.flush()
    sys.exit(0 if _ok else 1)


if __name__ == "__main__":

    try:
        _fp = os.path.join(os.path.expanduser("~"), ".flexgui")
        os.makedirs(_fp, exist_ok=True)
        with open(os.path.join(_fp, "caption_python.txt"), "w", encoding="utf-8") as _fh:
            _fh.write(sys.executable)
    except Exception:
        pass
    _flex_numpy_guard()

def format_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def segment_bounds(segment):






















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


def _clamp_to_range(start, end, real_preroll):







    if start >= 0.0:
        return (start, end)
    if end > 0.0:
        return (0.0, end)
    if real_preroll > 0.001:
        return None
    return (0.0, max(0.05, end - start))





















_HEAD_GAP_SECONDS = 2.0
_HEAD_MAX_SECONDS = 90.0
_HEAD_SILENCE_RMS = 0.004
_HEAD_PAD_SECONDS = 1.0
_HEAD_FILLERS = ("thank you", "thanks for watching", "thank you for watching", "thanks for watching!",
                 "please subscribe", "subscribe", "subtitles by the amara.org community", "you", "bye",
                 "music", "applause", "so", "okay", "oh")


def _flex_num(value, fallback=None):
    try:
        number = float(value)
        if number != number:
            return fallback
        return number
    except (TypeError, ValueError):
        return fallback


def _flex_first_heard(result):
    for segment in result.get('segments') or []:
        for word in segment.get('words') or []:
            start = _flex_num(word.get('start'))
            if start is not None:
                return start
        start = _flex_num(segment.get('start'))
        if start is not None and str(segment.get('text') or '').strip():
            return start
    return None


def _flex_is_filler(text):
    plain = re.sub(r"[\[\(].*?[\]\)]", " ", text or "")
    plain = re.sub(r"[^\w\s']", " ", plain, flags=re.UNICODE)
    plain = re.sub(r"\s+", " ", plain).strip().lower()
    return (not plain) or plain in _HEAD_FILLERS


def _flex_head_rescue(model, result, wav_path, head_at, transcribe_args):

    temp_path = None
    try:
        import wave
        import array
        import math
        with wave.open(wav_path, 'rb') as source:
            if source.getnchannels() != 1 or source.getsampwidth() != 2:
                return 0
            rate = source.getframerate()
            total = source.getnframes() / float(rate)
            first = _flex_first_heard(result)
            if first is None:
                first = total
            if first - head_at < _HEAD_GAP_SECONDS:
                return 0
            span_end = min(first + 0.25, head_at + _HEAD_MAX_SECONDS, total)
            if span_end - head_at < 1.0:
                return 0
            source.setpos(int(head_at * rate))
            raw = source.readframes(int((span_end - head_at) * rate))
        samples = array.array('h')
        samples.frombytes(raw[:len(raw) - (len(raw) % 2)])
        if sys.byteorder == 'big':
            samples.byteswap()
        if not len(samples):
            return 0
        step = max(1, len(samples) // 200000)
        picked = samples[::step]
        rms = math.sqrt(sum(float(v) * float(v) for v in picked) / len(picked)) / 32768.0
        if rms < _HEAD_SILENCE_RMS:
            return 0

        print("No captions were found for the first %.1fs although there is sound there. Listening to the opening again on its own..." % (first - head_at))
        temp_path = os.path.join(tempfile.gettempdir(), "flex_head_%d.wav" % os.getpid())
        with wave.open(temp_path, 'wb') as target:
            target.setnchannels(1)
            target.setsampwidth(2)
            target.setframerate(rate)
            target.writeframes(b"\x00\x00" * int(_HEAD_PAD_SECONDS * rate))
            if sys.byteorder == 'big':
                samples.byteswap()
            target.writeframes(samples.tobytes())
            target.writeframes(b"\x00\x00" * int(0.5 * rate))

        retry = dict(transcribe_args or {})
        retry['word_timestamps'] = True
        retry['condition_on_previous_text'] = False
        if 'language' not in retry and result.get('language'):
            retry['language'] = result.get('language')
        head = model.transcribe(temp_path, verbose=False, **retry)

        limit = first - 0.05
        recovered = []
        for segment in head.get('segments') or []:
            if _flex_num(segment.get('avg_logprob'), 0.0) < -1.0:
                continue
            if _flex_num(segment.get('compression_ratio'), 0.0) > 2.4:
                continue
            if _flex_num(segment.get('no_speech_prob'), 0.0) > 0.6:
                continue
            words = []
            for word in segment.get('words') or []:
                start = _flex_num(word.get('start'))
                end = _flex_num(word.get('end'))
                if start is None or end is None:
                    continue
                start = start - _HEAD_PAD_SECONDS + head_at
                end = end - _HEAD_PAD_SECONDS + head_at
                if end > limit:
                    break
                if start < head_at:
                    start = head_at
                if end <= start:
                    end = start + 0.05
                placed = dict(word)
                placed['start'] = round(start, 3)
                placed['end'] = round(end, 3)
                words.append(placed)
            text = "".join(str(w.get('word') or '') for w in words).strip()
            if not words or _flex_is_filler(text):
                continue
            recovered.append({'start': words[0]['start'], 'end': words[-1]['end'], 'text': " " + text,
                              'words': words, 'avg_logprob': segment.get('avg_logprob'),
                              'no_speech_prob': segment.get('no_speech_prob'), 'flex_rescued': True})
        if not recovered:
            print("Nothing intelligible in the opening; leaving it without captions.")
            return 0
        merged = recovered + list(result.get('segments') or [])
        for number, segment in enumerate(merged):
            segment['id'] = number
        result['segments'] = merged
        result['text'] = " ".join(str(s.get('text') or '').strip() for s in merged).strip()
        count = sum(len(s['words']) for s in recovered)
        print("Recovered %d word(s) from the opening %.1fs." % (count, first - head_at))
        return count
    except Exception as rescue_error:
        print("Could not re-check the opening (%s); continuing with the first pass." % rescue_error)
        return 0
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


def _flex_sort_words_into_range(result, pad_start, real_preroll, sel_duration):

    segments = result.get('segments') or []
    low = float(pad_start or 0.0)
    high = (low + float(sel_duration)) if sel_duration is not None else None
    synthetic = not (real_preroll and real_preroll > 0.001)
    kept_segments, early, dropped_before, dropped_after = [], [], 0, 0
    for segment in segments:
        words = segment.get('words') or []
        if not words:
            kept_segments.append(segment)
            continue
        kept, changed = [], False
        for word in words:
            start = _flex_num(word.get('start'), _flex_num(segment.get('start'), low))
            end = _flex_num(word.get('end'), _flex_num(segment.get('end'), start))
            if end <= low + 0.02:
                if not synthetic:
                    dropped_before += 1
                    changed = True
                    continue
                early.append(word)
                changed = True
            elif start < low:
                word['start'] = low
                changed = True
            if high is not None and start >= high - 0.02:
                dropped_after += 1
                changed = True
                continue
            kept.append(word)
        if not kept:
            continue
        if changed:
            segment['words'] = kept
            segment['text'] = " " + "".join(str(w.get('word') or '') for w in kept).strip()
        kept_segments.append(segment)

    if early:
        following = None
        for segment in kept_segments:
            for word in segment.get('words') or []:
                if word not in early:
                    following = _flex_num(word.get('start'))
                    break
            if following is not None:
                break
        lengths = [max(0.08, (_flex_num(w.get('end'), 0.0) - _flex_num(w.get('start'), 0.0))) for w in early]
        room = (following - low) if following is not None else sum(lengths)
        room = max(room, 0.05 * len(early))
        scale = min(1.0, room / sum(lengths))
        cursor = low
        for word, length in zip(early, lengths):
            word['start'] = round(cursor, 3)
            cursor += length * scale
            word['end'] = round(cursor, 3)

    for segment in kept_segments:
        words = segment.get('words') or []
        if words:
            first_start = _flex_num(words[0].get('start'))
            last_end = _flex_num(words[-1].get('end'))
            if first_start is not None and last_end is not None and last_end > first_start:
                if _flex_num(segment.get('start'), first_start) < first_start or segment.get('flex_rescued'):
                    segment['start'] = first_start
                if high is not None and _flex_num(segment.get('end'), last_end) > max(last_end, high):
                    segment['end'] = last_end
    result['segments'] = kept_segments
    if dropped_before or dropped_after or early:
        print("Range edges: %d word(s) before it and %d after it left out, %d opening word(s) kept at the top." % (dropped_before, dropped_after, len(early)))
    return result


def _flex_fix_opening(model, result, wav_path, pad_start, real_preroll, start_time, end_time, transcribe_args):
    try:
        is_wav = bool(wav_path) and str(wav_path).lower().endswith(".wav")
        if is_wav:
            _flex_head_rescue(model, result, wav_path, float(pad_start or 0.0), transcribe_args)
        sel_duration = (end_time - start_time) if (start_time is not None and end_time is not None) else None
        _flex_sort_words_into_range(result, pad_start, real_preroll, sel_duration)
    except Exception as opening_error:
        print("Opening check skipped (%s)." % opening_error)
    return result


def generate_srt(result, max_words=0, fill_gaps=False, start_time=None, end_time=None, pad_start=0.0, real_preroll=0.0):
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


                    _placed = _clamp_to_range(start, end, real_preroll)
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


                    _placed = _clamp_to_range(start, end, real_preroll)
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



            raw_start, raw_end = segment_bounds(segment)

            start = raw_start - pad_start
            end = raw_end - pad_start


            _placed = _clamp_to_range(start, end, real_preroll)
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
            next_start = blocks[i+1]['start']
            if next_start > curr_end and (next_start - curr_end) < 2.0:
                blocks[i]['end'] = next_start

    srt_content = ""
    idx = 1
    for b in blocks:
        srt_content += f"{idx}\n{format_timestamp(b['start'])} --> {format_timestamp(b['end'])}\n{b['text']}\n\n"
        idx += 1
    return srt_content


















_VOWELS = {
    'अ': 'a', 'आ': 'aa', 'इ': 'i', 'ई': 'ee', 'उ': 'u', 'ऊ': 'oo',
    'ऋ': 'ri', 'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au',
    'ऑ': 'o', 'ऍ': 'e',
}

_MATRAS = {
    'ा': 'aa', 'ि': 'i', 'ी': 'ee', 'ु': 'u', 'ू': 'oo', 'ृ': 'ri',
    'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au', 'ॉ': 'o', 'ॅ': 'e',
}

_CONSONANTS = {
    'क': 'k', 'ख': 'kh', 'ग': 'g', 'घ': 'gh', 'ङ': 'n',
    'च': 'ch', 'छ': 'chh', 'ज': 'j', 'झ': 'jh', 'ञ': 'n',
    'ट': 't', 'ठ': 'th', 'ड': 'd', 'ढ': 'dh', 'ण': 'n',
    'त': 't', 'थ': 'th', 'द': 'd', 'ध': 'dh', 'न': 'n',
    'प': 'p', 'फ': 'ph', 'ब': 'b', 'भ': 'bh', 'म': 'm',
    'य': 'y', 'र': 'r', 'ल': 'l', 'व': 'v', 'ळ': 'l',
    'श': 'sh', 'ष': 'sh', 'स': 's', 'ह': 'h',

    'क़': 'q', 'ख़': 'kh', 'ग़': 'gh', 'ज़': 'z', 'ड़': 'r', 'ढ़': 'rh',
    'फ़': 'f', 'य़': 'y',
}

_SIGNS = {
    'ं': 'n', 'ँ': 'n', 'ः': 'h', 'ॐ': 'om',
    '।': '.', '॥': '.', '़': '',
}

_DIGITS = {'०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
           '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'}

_VIRAMA = '्'
_ZWNJ = '‌'
_ZWJ = '‍'


def _is_devanagari(ch):
    return 'ऀ' <= ch <= 'ॿ'


def transliterate_word(word):

    out = []
    i = 0
    n = len(word)
    while i < n:
        ch = word[i]


        if i + 1 < n and word[i + 1] == '़' and (ch + '़') in _CONSONANTS:
            ch = ch + '़'
            i += 1

        if ch in _CONSONANTS:
            out.append(_CONSONANTS[ch])
            nxt = word[i + 1] if i + 1 < n else ''
            if nxt == _VIRAMA:

                i += 2
                continue
            if nxt in _MATRAS:
                out.append(_MATRAS[nxt])
                i += 2
                continue
            if nxt in (_ZWNJ, _ZWJ):
                i += 2
                continue



            at_end = (i + 1 >= n) or not _is_devanagari(word[i + 1])
            if not at_end:
                out.append('a')
            i += 1
            continue

        if ch in _VOWELS:
            out.append(_VOWELS[ch]); i += 1; continue
        if ch in _MATRAS:
            out.append(_MATRAS[ch]); i += 1; continue
        if ch in _SIGNS:
            out.append(_SIGNS[ch]); i += 1; continue
        if ch in _DIGITS:
            out.append(_DIGITS[ch]); i += 1; continue
        if ch == _VIRAMA or ch in (_ZWNJ, _ZWJ):
            i += 1; continue



        out.append(ch)
        i += 1
    return ''.join(out)


def has_devanagari(text):
    return any(_is_devanagari(c) for c in (text or ''))


def to_roman(text):

    if not text or not has_devanagari(text):
        return text
    parts = []
    for token in text.split(' '):
        parts.append(transliterate_word(token) if has_devanagari(token) else token)
    return ' '.join(parts)





_COMMON = {
    'हम': 'hum', 'नहीं': 'nahi', 'हूँ': 'hoon', 'हूं': 'hoon',
    'यह': 'yeh', 'वह': 'woh', 'ये': 'ye', 'वो': 'wo',
    'यहाँ': 'yahan', 'वहाँ': 'wahan', 'कहाँ': 'kahan', 'जहाँ': 'jahan',
    'मैंने': 'maine', 'तुमने': 'tumne', 'उसने': 'usne', 'हमने': 'humne',
    'कुछ': 'kuch', 'बहुत': 'bahut', 'और': 'aur', 'मुझे': 'mujhe',
    'तुम्हें': 'tumhe', 'हमें': 'hamein', 'उन्हें': 'unhe',
    'क्यों': 'kyun', 'क्योंकि': 'kyunki', 'इसलिए': 'isliye',
    'लेकिन': 'lekin', 'सिर्फ़': 'sirf', 'सिर्फ': 'sirf',
    'ज़्यादा': 'zyada', 'ठीक': 'theek', 'साथ': 'saath',
    'अभी': 'abhi', 'कभी': 'kabhi', 'सब': 'sab', 'लोग': 'log',
}


def _polish(word):

    if len(word) > 2 and word.endswith('aa'):
        return word[:-2] + 'a'
    return word


_transliterate_word_raw = transliterate_word


def transliterate_word(word):
    stripped = word.strip('।॥.,!?;:"‘’“”()')
    if stripped in _COMMON:
        return word.replace(stripped, _COMMON[stripped])
    return _polish(_transliterate_word_raw(word))


















CLOUD_BASE = os.environ.get("FLEX_AI_BASE", "https://www.captureflex.in")




CLOUD_PREFIX = os.environ.get("FLEX_AI_TRANSCRIBE_PREFIX", "/v1/flex-ai/transcribe")
CLOUD_POLL_CEILING = 5.0
CLOUD_JOB_DEADLINE = 900.0


class CloudError(Exception):


    def __init__(self, message, code="", retryable=False, payload=None):
        Exception.__init__(self, message)
        self.code = code
        self.retryable = retryable
        self.payload = payload or {}


def _cloud_auth_headers():






    headers = {"Accept": "application/json"}
    jwt = os.environ.get("FLEX_SESSION_JWT", "").strip()
    if jwt:
        headers["Authorization"] = "Bearer " + jwt
        return headers
    key = os.environ.get("FLEX_LICENSE_KEY", "").strip()
    install = os.environ.get("FLEX_INSTALL_ID", "").strip()
    if not key:
        raise CloudError(
            "No licence key was supplied to the cloud engine. The panel passes it in "
            "the environment as FLEX_LICENSE_KEY.",
            code="INVALID_LICENSE")
    headers["X-Flex-License-Key"] = key
    if install:
        headers["X-Install-ID"] = install
    return headers


def _cloud_call(method, url, body=None, headers=None, timeout=60.0, raw_body=None,
                content_type="application/json"):








    import urllib.request
    import urllib.error

    send = raw_body if raw_body is not None else (
        json.dumps(body).encode("utf-8") if body is not None else None)

    req = urllib.request.Request(url, data=send, method=method)
    for name, value in (headers or {}).items():
        req.add_header(name, value)
    if send is not None:
        req.add_header("Content-Type", content_type)

    try:
        response = urllib.request.urlopen(req, timeout=timeout)
        status, text = response.getcode(), response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as http_error:
        status = http_error.code
        try:
            text = http_error.read().decode("utf-8", "replace")
        except Exception:
            text = ""
    except Exception as transport_error:
        raise CloudError("Could not reach Flex AI: %s" % transport_error,
                         code="NETWORK", retryable=True)

    try:
        parsed = json.loads(text) if text.strip() else {}
    except ValueError:
        snippet = " ".join(text.split())[:180]
        raise CloudError(
            "Flex AI returned something that is not JSON (HTTP %s). %s" % (status, snippet),
            code="BAD_GATEWAY_BODY", retryable=True)







    if isinstance(parsed, dict):
        err = parsed.get("error")
        failed = parsed.get("success") is False or (
            isinstance(err, dict) and err.get("message") and parsed.get("success") is not True)
        if failed:
            err = err if isinstance(err, dict) else {}
            raise CloudError(err.get("message") or "The request was refused.",
                             code=str(err.get("code") or (status if status >= 400 else "")),
                             retryable=bool(err.get("retryable")),
                             payload=parsed)




        if status >= 400 and not err and parsed.get("success") is not True:
            raise CloudError("Flex AI answered HTTP %s with no explanation." % status,
                             code=str(status), retryable=status >= 500, payload=parsed)
    return parsed


def _audio_duration(path):









    import re
    import subprocess

    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, timeout=30)
        value = float((out.stdout or "").strip())
        if value > 0:
            return value
    except Exception:
        pass



    try:
        out = subprocess.run(["ffmpeg", "-i", path],
                             capture_output=True, text=True, timeout=60)
        found = re.search(r"Duration:\s*(\d+):(\d\d):(\d\d(?:\.\d+)?)",
                          (out.stderr or "") + (out.stdout or ""))
        if found:
            hours, minutes, seconds = found.groups()
            value = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
            if value > 0:
                return value
    except Exception:
        pass

    try:
        import wave
        with contextlib.closing(wave.open(path, "rb")) as handle:
            return handle.getnframes() / float(handle.getframerate())
    except Exception:
        pass



    try:
        kbps = float(os.environ.get("FLEX_UPLOAD_KBPS", "") or 0)
        if kbps > 0:
            return (os.path.getsize(path) * 8.0) / (kbps * 1000.0)
    except Exception:
        pass
    return 0.0


AUDIO_MIME = {
    ".wav": "audio/wav",   ".m4a": "audio/mp4",  ".mp4": "audio/mp4",
    ".mp3": "audio/mpeg",  ".aac": "audio/aac",  ".flac": "audio/flac",
    ".ogg": "audio/ogg",   ".opus": "audio/opus", ".aiff": "audio/aiff",
}


def _audio_mime(path):
    return AUDIO_MIME.get(os.path.splitext(path)[1].lower(), "audio/wav")






GEMINI_ENGINE = "gemini-3.5-transcribe"



try:
    CLOUD_DIRECT_MAX_BYTES = int(os.environ.get("FLEX_CLOUD_DIRECT_MAX_BYTES", "") or 4400000)
except ValueError:
    CLOUD_DIRECT_MAX_BYTES = 4400000


CLOUD_BUSY_DELAYS = (5.0, 10.0, 20.0, 40.0, 60.0)


class CloudCancelled(BaseException):
    pass





_CLOUD_SIGNAL = {"defer": False, "pending": False}


def _cloud_init_call(url, body, headers):

    _CLOUD_SIGNAL.update(defer=True, pending=False)
    try:
        return _cloud_call("POST", url, body=body, headers=headers, timeout=45.0)
    except CloudError:
        if _CLOUD_SIGNAL["pending"]:
            raise CloudCancelled("cancelled by the user")
        raise
    finally:
        _CLOUD_SIGNAL["defer"] = False


def _cloud_wait_in_line(init, headers, say, began, budget):




    import urllib.parse
    ticket = str(init.get("ticket") or "")
    if init.get("job_id") or str(init.get("status") or "").lower() != "queued" or not ticket:
        return init
    url = CLOUD_BASE + CLOUD_PREFIX + "/queue?ticket=" + urllib.parse.quote(ticket)
    said = ""
    try:
        while True:
            line = str(init.get("message") or "Server is busy. Please wait.")
            if init.get("position"):
                line += " (place %s in line)" % init.get("position")
            if line != said:
                say(line)
                said = line

            _flex_stage("queue", None, "Gemini 3.5 Transcribe", "%s;%s;%s" % (
                init.get("position") or "", init.get("eta_seconds") or "",
                str(init.get("message") or "Server is busy. Please wait.").replace(";", ",")))
            if time.time() - began > budget:
                raise CloudError("The Flex server's line did not move within %d minutes." % int(budget / 60),
                                 code="QUEUE_TIMEOUT", retryable=True)
            try:
                wait = float(init.get("poll_after_ms") or 3000) / 1000.0
            except (TypeError, ValueError):
                wait = 3.0
            time.sleep(min(10.0, max(1.0, wait)))
            init = _cloud_call("GET", url, headers=headers, timeout=45.0)
            status = str(init.get("status") or "").lower()
            if init.get("job_id") or status == "ready":
                return init
            if status != "queued":
                raise CloudError("The Flex server's line answered '%s'." % (status or "nothing"), code="QUEUE_FAILED")
    except BaseException:
        try:
            _cloud_call("POST", url + "&action=leave", body={}, headers=headers, timeout=15.0)
        except BaseException:
            pass
        raise


@contextlib.contextmanager
def _cloud_cancellable():



    import signal
    hits = {"n": 0}
    _CLOUD_SIGNAL.update(defer=False, pending=False)

    def on_signal(_signum, _frame):
        hits["n"] += 1
        if hits["n"] == 1:
            if _CLOUD_SIGNAL["defer"]:
                _CLOUD_SIGNAL["pending"] = True
                return
            raise CloudCancelled("cancelled by the user")

    previous = []
    for name in ("SIGTERM", "SIGINT", "SIGHUP", "SIGBREAK"):
        sig = getattr(signal, name, None)
        if sig is None:
            continue
        try:
            previous.append((sig, signal.signal(sig, on_signal)))
        except (ValueError, OSError, RuntimeError):
            pass
    try:
        yield
    finally:
        for sig, handler in previous:
            try:
                signal.signal(sig, handler)
            except (ValueError, OSError, RuntimeError, TypeError):
                pass


def _cloud_mark(line):


    try:
        print(line)
        sys.stdout.flush()
    except Exception:
        pass


def _google_upload(google, payload):



    import urllib.request
    import urllib.error

    url = str(google.get("url") or "")
    if not url.lower().startswith(("https://", "http://")):
        raise CloudError("Flex AI sent no usable Google upload address.", code="GOOGLE_UPLOAD_FAILED")
    req = urllib.request.Request(url, data=payload, method=str(google.get("method") or "POST").upper())
    for name, value in (google.get("headers") or {}).items():
        req.add_header(str(name), str(value))
    req.add_header("Content-Length", str(len(payload)))
    try:
        response = urllib.request.urlopen(req, timeout=max(120.0, len(payload) / 20000.0))
        status, text = response.getcode(), response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as http_error:
        status = http_error.code
        try:
            text = http_error.read().decode("utf-8", "replace")
        except Exception:
            text = ""
    except Exception as transport_error:
        raise CloudError("could not reach Google: %s" % transport_error,
                         code="GOOGLE_UPLOAD_FAILED", retryable=True)
    try:
        parsed = json.loads(text) if text.strip() else {}
    except ValueError:
        parsed = {}
    parsed = parsed if isinstance(parsed, dict) else {}
    found = parsed.get("file") if isinstance(parsed.get("file"), dict) else {}
    name = str(found.get("name") or "")
    if status >= 400 or not name.startswith("files/"):
        err = parsed.get("error") if isinstance(parsed.get("error"), dict) else {}
        detail = (": " + str(err.get("message"))[:160]) if err.get("message") else ""
        raise CloudError("Google answered HTTP %s%s" % (status, detail),
                         code="GOOGLE_UPLOAD_FAILED", retryable=True)
    return name


def _flex_ffmpeg():

    import shutil
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def _cloud_small_copy(audio_path, duration, limit):




    import subprocess
    exe = _flex_ffmpeg()
    if not exe or not duration or duration <= 0:
        return None
    for codec, ext, low, label in (("libopus", ".ogg", 12, "Opus"), ("aac", ".m4a", 16, "AAC")):
        out = os.path.join(tempfile.gettempdir(), "flex_cloud_small_%d%s" % (os.getpid(), ext))
        kbps = max(low, min(32, int(limit * 0.92 * 8 / 1000.0 / duration)))
        while True:
            cmd = [exe, "-y", "-v", "error", "-i", audio_path, "-vn", "-ac", "1", "-ar", "16000",
                   "-c:a", codec, "-b:a", "%dk" % kbps]
            if codec == "libopus":
                cmd += ["-application", "voip"]
            try:
                subprocess.run(cmd + [out], check=True, capture_output=True, timeout=900)
                size = os.path.getsize(out)
            except Exception:
                size = -1
            if 0 < size <= limit:
                return out, "%s %d kbps mono 16 kHz" % (label, kbps)
            if size < 0 or kbps <= low:
                break
            kbps = max(low, int(kbps * 0.8))
        try:
            if os.path.exists(out):
                os.remove(out)
        except Exception:
            pass
    return None


def _cloud_put(upload_url, path, say):




    size = os.path.getsize(path)
    with open(path, "rb") as handle:
        payload = handle.read()
    say("Uploading %.1f MB of audio..." % (size / 1048576.0))
    for attempt in (1, 2):
        try:
            return _cloud_call("PUT", upload_url, raw_body=payload, headers={"Accept": "*/*"},
                               content_type=_audio_mime(path), timeout=max(120.0, size / 20000.0))
        except CloudError as put_error:
            if attempt == 2 or put_error.code != "UPLOAD_FAILED":
                raise
            say("The Flex server could not pass the audio on (UPLOAD_FAILED); sending it once more...")


def _cloud_send_direct(upload_url, audio_path, duration, say, scratch):


    path = audio_path
    size = os.path.getsize(audio_path)
    if size > CLOUD_DIRECT_MAX_BYTES:
        limit_mb = CLOUD_DIRECT_MAX_BYTES / 1e6
        say("The audio is %.1f MB, over the %.1f MB the Flex server takes directly; making a smaller copy..."
            % (size / 1e6, limit_mb))
        small = _cloud_small_copy(audio_path, duration, CLOUD_DIRECT_MAX_BYTES)
        if not small:
            if not _flex_ffmpeg():
                raise CloudError("The audio is %.1f MB, over the %.1f MB the Flex server takes directly, and "
                                 "ffmpeg is not available to make it smaller. Press Install / Fix Dependencies."
                                 % (size / 1e6, limit_mb), code="AUDIO_TOO_LARGE_FOR_UPLOAD")
            raise CloudError("This audio (%.0f min) does not fit the %.1f MB the Flex server takes directly even "
                             "at the smallest size (about %.0f min fits). Caption a shorter range."
                             % (duration / 60.0, limit_mb, CLOUD_DIRECT_MAX_BYTES * 8 / 12000.0 / 60.0),
                             code="AUDIO_TOO_LARGE_FOR_UPLOAD")
        path, label = small
        scratch.append(path)
        say("Smaller copy ready: %.1f MB (%s)." % (os.path.getsize(path) / 1e6, label))
    _cloud_put(upload_url, path, say)
    return path


def cloud_transcribe(audio_path, language=None, diarization=False, on_status=None, tier="standard",
                     gemini=False):






    def say(message):
        if on_status:
            on_status(message)
        else:
            print(message)
            try:
                sys.stdout.flush()
            except Exception:
                pass

    headers = _cloud_auth_headers()
    duration = _audio_duration(audio_path)
    began = time.time()
    track = {"progress": -1.0, "budget": CLOUD_JOB_DEADLINE, "began": began}
    with _cloud_cancellable():
        attempt = 0
        while True:
            attempt += 1
            try:
                return _cloud_job(audio_path, duration, language, diarization, tier, headers, say, track, gemini)
            except CloudError as busy:
                if busy.code not in ("PROVIDER_BUSY", "RATE_LIMITED") or attempt > len(CLOUD_BUSY_DELAYS):
                    raise
                wait = CLOUD_BUSY_DELAYS[attempt - 1]
                err = (busy.payload or {}).get("error")
                after = (err.get("retry_after_seconds") if isinstance(err, dict) else None) or (busy.payload or {}).get("retry_after_seconds")
                try:
                    if after:
                        wait = min(60.0, max(1.0, float(after)))
                except (TypeError, ValueError):
                    pass
                if time.time() - began + wait > track["budget"]:
                    raise
                if busy.code == "RATE_LIMITED":
                    say("Flex AI is busy for this licence (RATE_LIMITED); trying again in %d s..." % int(wait))
                else:
                    say("Gemini is busy right now (%s); trying again in %d s..." % (busy.code, int(wait)))
                time.sleep(wait)


def _cloud_job(audio_path, duration, language, diarization, tier, headers, say, track, gemini):


    size = os.path.getsize(audio_path)
    mime = _audio_mime(audio_path)



    say("Checking your Flex AI balance...")
    init = _cloud_init_call(CLOUD_BASE + CLOUD_PREFIX + "/init", {
        "duration_seconds": round(duration, 2),


        "file_size_bytes": size,
        "mime_type": mime,
        "audio_format": os.path.splitext(audio_path)[1].lstrip(".").lower(),
        "language": language or None,
        "diarization": bool(diarization),




        "tier": tier or "standard",
    }, headers)
    init = _cloud_wait_in_line(init, headers, say, track["began"], track["budget"])



    available = init.get("available_credits")
    if available is not None:
        print("FLEXAI_CREDITS:%s" % available)

    job_id = init.get("job_id")





    upload_url = str(init.get("direct_upload_url") or init.get("upload_url") or "")
    if upload_url and not upload_url.lower().startswith(("http://", "https://")):
        upload_url = CLOUD_BASE.rstrip("/") + "/" + upload_url.lstrip("/")

    if not job_id or not upload_url:
        raise CloudError("Flex AI did not return a job to upload to.", code="BAD_INIT")

    engine = str(init.get("engine") or "legacy").strip().lower()
    on_gemini = engine == GEMINI_ENGINE
    _cloud_mark("FLEX_CLOUD_JOB:%s" % job_id)
    _cloud_mark("FLEX_CLOUD_ENGINE:%s" % ("gemini" if on_gemini else "legacy"))
    if on_gemini:
        say("Model: %s (Gemini 3.5 Transcribe)" % (init.get("model") or GEMINI_ENGINE))
    elif gemini:
        why = {"gemini_minute_cap": " (Gemini's per-minute limit is reached)",
               "gemini_daily_cap": " (today's Gemini limit is reached)",
               "google_quota": " (Gemini is at capacity)"}.get(str(init.get("engine_fallback") or ""), "")
        say("NOTE: the Flex server is running this audio on its older cloud engine, not Gemini 3.5 Transcribe%s." % why)




    try:
        server_deadline = float(init.get("deadline_seconds") or 0)
    except (TypeError, ValueError):
        server_deadline = 0.0
    budget = max(CLOUD_JOB_DEADLINE, server_deadline + 120.0) if server_deadline else CLOUD_JOB_DEADLINE
    track["budget"] = budget
    scratch = []
    try:
        if _CLOUD_SIGNAL.get("pending"):
            _CLOUD_SIGNAL["pending"] = False
            raise CloudCancelled("cancelled by the user")


        google_name = ""
        google = init.get("google_upload") if isinstance(init.get("google_upload"), dict) else None
        if google and google.get("url"):
            try:
                announced = int(google.get("size_bytes") if google.get("size_bytes") is not None else size)
            except (TypeError, ValueError):
                announced = size
            if announced != size:
                say("NOTE: Google's upload was opened for %d bytes, not %d; sending through the Flex server."
                    % (announced, size))
                google = None
        else:
            google = None
        if google:
            with open(audio_path, "rb") as handle:
                payload = handle.read()
            say("Uploading %.1f MB of audio..." % (size / 1048576.0))
            for attempt in (1, 2):
                try:
                    google_name = _google_upload(google, payload)
                    break
                except CloudError as up_error:
                    if attempt == 1:
                        say("Google's upload did not take the audio (%s); trying once more..." % up_error)
                    else:
                        say("Google's upload failed again (%s); sending the audio through the Flex server instead."
                            % up_error)
            payload = None
        if not google_name:
            _cloud_send_direct(upload_url, audio_path, duration, say, scratch)

        say("Transcribing on Flex AI...")

        def start_job(named):
            return _cloud_call("POST", CLOUD_BASE + CLOUD_PREFIX + "/jobs/%s/start" % job_id,
                               body={"google_file_name": named} if named else {},
                               headers=headers, timeout=45.0)

        def start_or_problem(named):
            try:
                return start_job(named), None
            except CloudError as problem:
                return None, problem

        started, problem = start_or_problem(google_name)
        if problem is not None and (problem.code == "ENGINE_SWITCHED" or (problem.payload or {}).get("reupload")):


            again = str((problem.payload or {}).get("flat_upload_url") or (problem.payload or {}).get("upload_url") or "") or upload_url
            if not again.lower().startswith(("http://", "https://")):
                again = CLOUD_BASE.rstrip("/") + "/" + again.lstrip("/")
            on_gemini = False
            google_name = ""
            _cloud_mark("FLEX_CLOUD_ENGINE:legacy")
            say("NOTE: Gemini is at capacity, so the Flex server moved this job to its older cloud engine; "
                "sending the audio again...")
            _cloud_send_direct(again, audio_path, duration, say, scratch)
            started, problem = start_or_problem("")
        if problem is not None:





            if problem.code != "AUDIO_NOT_UPLOADED":
                raise problem
            if google_name:
                say("Flex AI could not find the audio Google received; sending it through the Flex server...")
                _cloud_send_direct(upload_url, audio_path, duration, say, scratch)
            else:
                say("Flex AI did not see the upload; sending it once more...")
                sent = scratch[-1] if scratch else audio_path
                with open(sent, "rb") as handle:
                    resend = handle.read()
                _cloud_call("POST", upload_url, raw_body=resend,
                            headers={"Accept": "*/*"},
                            content_type=_audio_mime(sent),
                            timeout=max(120.0, len(resend) / 20000.0))
            started = start_job("")


        interval = min(CLOUD_POLL_CEILING,
                       max(1.0, float(started.get("poll_interval_ms",
                                                  init.get("poll_interval_ms", 3000))) / 1000.0))
        deadline = time.time() + budget


        first_poll = True
        while True:
            if time.time() > deadline:
                raise CloudError(
                    "Flex AI did not finish within %d minutes. The job was cancelled and any "
                    "held credits released." % int(budget / 60), code="TIMEOUT")

            if first_poll:
                first_poll = False
            else:
                time.sleep(interval)
            state = _cloud_call("GET",
                                CLOUD_BASE + CLOUD_PREFIX + "/jobs/%s" % job_id,
                                headers=headers, timeout=45.0)
            status = str(state.get("status", "")).lower()



            served = state.get("provider") or state.get("tier")
            if not on_gemini and served and not getattr(cloud_transcribe, "_said_provider", None) == served:
                cloud_transcribe._said_provider = served
                say("Engine: %s" % served)

            if status in ("completed", "done", "succeeded"):
                done = _cloud_normalise(state.get("result") or state, tier)
                done["engine"] = GEMINI_ENGINE if on_gemini else "legacy"
                done["model"] = str(state.get("model") or init.get("model") or "")

                if not done.get("billing") and isinstance(state.get("billing"), dict):
                    done["billing"] = state["billing"]
                left = (done.get("billing") or {}).get("balance_remaining")
                if left is not None:
                    print("FLEXAI_CREDITS:%s" % left)
                if on_gemini:
                    count = sum(len(s.get("words") or []) for s in done["segments"])
                    speakers = done.get("speakers") or []
                    say("Gemini 3.5 Transcribe: %d words in %d line(s)%s." % (
                        count, len(done["segments"]),
                        (", %d speakers" % len(speakers)) if len(speakers) > 1 else ""))
                _cloud_mark("FLEX_CLOUD_CLOSED:done")
                return done
            if status in ("failed", "error", "cancelled"):
                err = state.get("error") or {}
                raise CloudError(err.get("message") or "Flex AI could not transcribe that audio.",
                                 code=err.get("code", "FAILED"), payload=state)





            progress = float(state.get("progress") or 0.0)
            if progress > 1.0:
                progress = progress / 100.0
            if progress > 1.0:
                progress = 1.0
            if progress > track["progress"] + 0.04:
                track["progress"] = progress
                say("Transcribing... %d%%" % int(round(progress * 100)))
    except CloudCancelled:
        cloud_cancel(job_id)
        _cloud_mark("FLEX_CLOUD_CLOSED:cancelled")
        raise
    except CloudError:
        cloud_cancel(job_id)
        _cloud_mark("FLEX_CLOUD_CLOSED:failed")
        raise
    finally:
        for leftover in scratch:
            try:
                os.remove(leftover)
            except Exception:
                pass


def cloud_cancel(job_id):

    try:
        _cloud_call("POST",
                    CLOUD_BASE + CLOUD_PREFIX + "/jobs/%s/cancel" % job_id,
                    body={}, headers=_cloud_auth_headers(), timeout=20.0)
    except Exception:
        pass


def _cloud_failure(error):


    code = str(getattr(error, "code", "") or "").upper()
    payload = getattr(error, "payload", None) or {}
    err = payload.get("error") if isinstance(payload.get("error"), dict) else {}
    if code in ("INVALID_LICENSE", "AUTHENTICATION_REQUIRED", "LICENSE_REQUIRED", "401"):
        return "relink", ("Flex AI needs your licence re-linked: activate it again in AI Settings. "
                          "Nothing was charged.")
    if code in ("PROVIDER_BILLING", "PROVIDER_NOT_CONFIGURED", "404", "NOT_FOUND", "503") or (
            code == "BAD_GATEWAY_BODY" and "(HTTP 404)" in str(error)):
        return "not_on", "Gemini transcription is not available on the Flex server right now. Nothing was charged."
    if code in ("INSUFFICIENT_CREDITS", "402"):
        need = err.get("required_credits", payload.get("required_credits"))
        have = err.get("available_credits", payload.get("available_credits"))
        extra = (" (needs %s, you have %s)" % (need, have)) if need is not None and have is not None else ""
        return "credits", "Not enough Flex AI credits for this audio%s. Nothing was charged." % extra
    if code in ("PROVIDER_BUSY", "RATE_LIMITED", "429"):
        return "busy", "Gemini is still busy after several tries. Try again in a few minutes. Nothing was charged."
    if code == "AUDIO_UNREADABLE":
        return "unreadable", ("Gemini could not read this audio (AUDIO_UNREADABLE). Nothing was charged. "
                              "Your usual engine reads the file on this computer.")
    if code == "NETWORK":
        return "network", "Could not reach the Flex server (%s). Check the internet connection." % error
    if code == "AUDIO_TOO_LARGE_FOR_UPLOAD":
        return "too_long", "%s Nothing was charged." % error
    if code == "TIMEOUT":
        return "failed", str(error)
    return "failed", "Gemini 3.5 Transcribe could not finish this audio: %s%s. Held credits were released." % (
        str(error).rstrip(". "), (" (%s)" % code) if code and code not in str(error) else "")


def _cloud_offer(kind):

    usual = str(os.environ.get("FLEX_CLOUD_USUAL_LABEL", "") or "").strip() or "your usual engine"
    usual = re.sub(r"[^\x20-\x7e]", "", usual)[:60] or "your usual engine"
    _cloud_mark("FLEX_CLOUD_OFFER:%s" % kind)
    _cloud_mark("Switch TRANSCRIPTION MODEL back to %s to caption this now." % usual)

def _cloud_normalise(result, tier="standard"):







    segments = []
    for raw in (result.get("segments") or []):
        words = []
        for word in (raw.get("words") or []):
            text = str(word.get("word") or word.get("text") or "").strip()
            if not text:
                continue
            try:
                start, end = float(word.get("start")), float(word.get("end"))
            except (TypeError, ValueError):
                continue
            if end <= start:
                continue






            entry = {"word": " " + text, "start": start, "end": end}
            if word.get("speaker"):
                entry["speaker"] = word["speaker"]
            words.append(entry)

        try:
            seg_start = float(raw.get("start", 0.0))
            seg_end = float(raw.get("end", 0.0))
        except (TypeError, ValueError):
            continue

        segment = {"start": seg_start, "end": seg_end,
                   "text": str(raw.get("text") or "").strip(), "words": words}
        if raw.get("speaker"):
            segment["speaker"] = raw["speaker"]
        segments.append(segment)

    if not segments:




        if (tier or "standard") == "high":
            raise CloudError(
                "Flex AI 3.5 High returned an empty transcript for this audio. "
                "Switch TRANSCRIPTION MODEL to 'Flex AI Transcribe' and run it "
                "again — the standard tier is unaffected.",
                code="EMPTY_RESULT")
        raise CloudError("Flex AI returned no speech for that audio.", code="EMPTY_RESULT")

    return {
        "text": str(result.get("text") or " ".join(s["text"] for s in segments)).strip(),
        "language": result.get("language"),
        "segments": segments,
        "speakers": result.get("speakers") or [],
        "billing": result.get("billing") or {},
    }


class _CloudModel(object):







    def __init__(self, diarization=True, tier="standard", gemini=False):
        self.diarization = diarization
        self.tier = tier
        self.gemini = gemini

    def transcribe(self, path, verbose=False, **kwargs):
        return cloud_transcribe(
            path,
            language=kwargs.get("language"),
            diarization=self.diarization,
            tier=self.tier,
            gemini=self.gemini,
        )


def _flex_cloud_words(result):
    words = []
    for segment in result.get("segments", []) or []:
        for word in segment.get("words", []) or []:
            try:
                start, end = float(word.get("start")), float(word.get("end"))
            except (TypeError, ValueError):
                continue
            if end > start:
                words.append((start, end, word))
    words.sort(key=lambda item: item[0])
    return words


def _flex_cloud_cut(result, total):






    words = _flex_cloud_words(result)
    if not words or total <= 0:
        return None
    lengths = sorted(end - start for start, end, _ in words)
    median = lengths[len(lengths) // 2]
    limit = max(2.5, median * 6.0)
    for start, end, _ in words:
        if end - start > limit and total - start > 2.0:
            return start
    last_end = max(end for _, end, _ in words)
    if total - last_end > 3.0:
        return last_end
    return None


def _flex_cut_audio(src, start, dst, for_upload):
    import subprocess
    cmd = ["ffmpeg", "-y", "-ss", "%.3f" % max(0.0, start), "-i", src, "-vn", "-ac", "1", "-ar", "16000"]
    if for_upload:
        cmd += ["-c:a", "aac", "-b:a", "64k"]
    else:
        cmd += ["-c:a", "pcm_s16le"]
    subprocess.run(cmd + [dst], check=True, capture_output=True)
    return dst


def _flex_shift(result, offset, keep_from):

    out = []
    for segment in result.get("segments", []) or []:
        words = []
        for word in segment.get("words", []) or []:
            try:
                start, end = float(word.get("start")) + offset, float(word.get("end")) + offset
            except (TypeError, ValueError):
                continue
            if end <= start or (start + end) / 2.0 < keep_from:
                continue
            moved = dict(word)
            moved["start"], moved["end"] = start, end
            words.append(moved)
        if not words:
            continue
        seg = dict(segment)
        seg["words"] = words
        seg["start"], seg["end"] = words[0]["start"], words[-1]["end"]
        seg["text"] = "".join(w.get("word", "") for w in words).strip()
        out.append(seg)
    return out


def _flex_head(result, cut):

    out = []
    for segment in result.get("segments", []) or []:
        words = []
        for word in segment.get("words", []) or []:
            try:
                start, end = float(word.get("start")), float(word.get("end"))
            except (TypeError, ValueError):
                continue
            if start < cut - 0.02 and end <= cut + 0.35:
                words.append(word)
        if not words:
            continue
        seg = dict(segment)
        seg["words"] = words
        seg["end"] = min(float(segment.get("end", words[-1]["end"])), float(words[-1]["end"]))
        seg["text"] = "".join(w.get("word", "") for w in words).strip()
        out.append(seg)
    return out


def _flex_trim_stretched(result):

    words = _flex_cloud_words(result)
    for i, (start, end, word) in enumerate(words):
        text = str(word.get("word") or "").strip()
        natural = min(1.6, max(0.35, 0.2 + 0.09 * len(text)))
        if end - start > max(2.5, natural * 4):
            nxt = words[i + 1][0] if i + 1 < len(words) else None
            new_end = start + natural
            if nxt is not None:
                new_end = min(new_end, max(start + 0.05, nxt))
            word["end"] = new_end
    for segment in result.get("segments", []) or []:
        ws = segment.get("words") or []
        if ws:
            try:
                segment["end"] = float(ws[-1]["end"])
            except (TypeError, ValueError, KeyError):
                pass
    return result


def _flex_join_tail(result, tail, cut, lead):


    head = _flex_head(result, cut)
    head_end = cut
    for segment in head:
        for word in segment.get("words", []) or []:
            try:
                head_end = max(head_end, float(word.get("end")))
            except (TypeError, ValueError):
                pass
    added = []
    for segment in _flex_shift(tail, cut - lead, cut - 0.05):
        kept = []
        for word in segment["words"]:
            if word["start"] < head_end:
                if word["end"] <= head_end + 0.05:
                    continue
                word["start"] = head_end
            kept.append(word)
        if kept:
            segment["words"] = kept
            segment["start"] = kept[0]["start"]
            segment["text"] = "".join(w.get("word", "") for w in kept).strip()
            added.append(segment)
    result["segments"] = head + added
    result["text"] = " ".join(s.get("text", "") for s in result["segments"]).strip()
    return bool(added)


def _flex_local_complete(model, result, audio_path, transcribe_args):




    total = 0.0
    try:
        total = float(_audio_duration(audio_path) or 0.0)
    except Exception:
        total = 0.0
    args = dict(transcribe_args)
    if not _FLEX_STATE["keep_prompt"]:
        args.pop("initial_prompt", None)
    args["condition_on_previous_text"] = False
    for attempt in range(4):
        cut = _flex_cloud_cut(result, total)
        if cut is None:
            break
        print("Whisper stopped following the speech at %.1fs of %.1fs; transcribing the rest again..." % (cut, total))
        lead = min(0.3, cut)
        tail_file = None
        try:
            tail_file = _flex_cut_audio(audio_path, cut - lead, os.path.join(tempfile.gettempdir(), "flex_local_tail_%d_%d.wav" % (os.getpid(), attempt)), False)
            tail = model.transcribe(tail_file, verbose=False, **args)
        except Exception as tail_error:
            print("  could not transcribe the rest: %s" % tail_error)
            tail = None
        if tail_file:
            try:
                os.remove(tail_file)
            except Exception:
                pass
        if tail is None:
            break
        if not _flex_join_tail(result, tail, cut, lead):
            print("  no more speech after %.1fs." % cut)
            break
    return _flex_trim_stretched(result)


def _flex_cloud_complete(model, result, audio_path, transcribe_args, local_model_name):



    total = 0.0
    try:
        total = float(_audio_duration(audio_path) or 0.0)
    except Exception:
        total = 0.0
    local = None
    for attempt in range(4):
        cut = _flex_cloud_cut(result, total)
        if cut is None:
            break
        print("Flex AI stopped following the speech at %.1fs of %.1fs; transcribing the rest..." % (cut, total))
        lead = min(0.3, cut)
        tail = None
        tail_file = None
        try:
            if local is None:
                import whisper
                local = _flex_load_model(whisper, local_model_name)
            tail_file = _flex_cut_audio(audio_path, cut - lead, os.path.join(tempfile.gettempdir(), "flex_tail_%d_%d.wav" % (os.getpid(), attempt)), False)
            tail = local.transcribe(tail_file, verbose=False, **transcribe_args)
            print("  the rest came from the local Whisper engine.")
        except Exception:
            tail = None
        if tail is None:
            try:
                tail_file = _flex_cut_audio(audio_path, cut - lead, os.path.join(tempfile.gettempdir(), "flex_tail_%d_%d.m4a" % (os.getpid(), attempt)), True)
                tail = model.transcribe(tail_file, verbose=False, **transcribe_args)
                print("  the rest came from a second Flex AI pass (%.0fs of audio)." % (total - cut + lead))
            except CloudError as tail_error:
                print("  could not transcribe the rest: %s" % tail_error)
                tail = None
            except Exception as tail_error:
                print("  could not transcribe the rest: %s" % tail_error)
                tail = None
        if tail_file:
            try:
                os.remove(tail_file)
            except Exception:
                pass
        if tail is None:
            break
        if not _flex_join_tail(result, tail, cut, lead):
            print("  no more speech after %.1fs." % cut)
            break
        result["text"] = " ".join(s.get("text", "") for s in result["segments"]).strip()
    return _flex_trim_stretched(result)
















FLEX_STT_CUSTOM = False


def _flex_stock():

    if FLEX_STT_CUSTOM:
        return False
    return os.environ.get("FLEX_STT_CUSTOM", "").strip() != "1"










_FLEX_KEPT_MODELS = ("turbo", "medium", "large")
_FLEX_MODEL_ALIASES = {
    "tiny": "turbo", "tiny.en": "turbo", "base": "turbo", "base.en": "turbo",
    "small": "turbo", "small.en": "turbo", "medium.en": "medium",
    "large-v1": "large", "large-v2": "large", "large-v3": "large",
    "large-v3-turbo": "turbo",
}
_FLEX_MODEL_LABELS = {"turbo": "Large V3 Turbo", "medium": "Medium", "large": "Large V3", "hinglish": "Flex Hinglish"}


def _flex_whisper_cache():
    root = os.environ.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache")
    return os.path.join(root, "whisper")


def _flex_model_file(name):

    names = {"turbo": ("large-v3-turbo.pt",), "medium": ("medium.pt",),
             "large": ("large-v3.pt", "large-v2.pt")}.get(name, ())
    for filename in names:
        full = os.path.join(_flex_whisper_cache(), filename)
        try:
            if os.path.getsize(full) > 10000000:
                return filename
        except OSError:
            pass
    return None


def _flex_fallback_model():
    wanted = os.environ.get("FLEX_LOCAL_FALLBACK_MODEL", "").strip().lower()
    wanted = _FLEX_MODEL_ALIASES.get(wanted, wanted)
    if wanted in _FLEX_KEPT_MODELS:
        return wanted
    for name in ("turbo", "medium", "large"):
        if _flex_model_file(name):
            return name
    return "turbo"


def _flex_resolve_model(name):

    raw = (name or "").strip()
    key = raw.lower()
    if key in _FLEX_KEPT_MODELS:
        return key
    if key == "hinglish" and not _flex_stock() and _flex_hinglish_file():
        return key
    mapped = _FLEX_MODEL_ALIASES.get(key)
    if not mapped or not _flex_model_file(mapped):


        for name in ("turbo", "medium", "large"):
            if _flex_model_file(name):
                mapped = name
                break
        mapped = mapped or _flex_fallback_model()
    if mapped != key and key == "hinglish" and _flex_stock():
        print("Flex Hinglish is paused in this version (stock models); using %s." % _FLEX_MODEL_LABELS[mapped])
    elif mapped != key:
        print("Model '%s' is no longer offered; using %s." % (raw or "none", _FLEX_MODEL_LABELS[mapped]))
    return mapped


def _flex_load_name(name):


    if name == "large" and _flex_model_file("large") == "large-v2.pt":
        return "large-v2"
    return name


def _flex_decode_args(model_name):










    return {"condition_on_previous_text": False}


def _flex_detect_language(model, audio_path):



    try:
        import numpy as np
        import whisper
        audio = whisper.load_audio(audio_path)
    except Exception as detect_error:
        print("NOTE: language detection fell back to Whisper's own (%s)." % detect_error)
        return None
    rate, window = 16000, 30 * 16000
    if len(audio) < rate:
        return None
    hop = 10 * rate
    starts = list(range(0, max(1, len(audio) - window + 1), hop)) or [0]
    energy = []
    for start in starts:
        chunk = audio[start:start + window]
        energy.append(float(np.sqrt(np.mean(chunk * chunk))) if len(chunk) else 0.0)
    ranked = sorted(range(len(starts)), key=lambda i: -energy[i])[:4]
    totals = {}
    try:
        n_mels = getattr(model.dims, "n_mels", 80)
        for index in sorted(ranked):
            if energy[index] < 0.004:
                continue
            chunk = whisper.pad_or_trim(audio[starts[index]:starts[index] + window])
            mel = whisper.log_mel_spectrogram(chunk, n_mels).to(model.device)
            _, probs = model.detect_language(mel)
            for code, p in probs.items():
                totals[code] = totals.get(code, 0.0) + float(p)
    except Exception as detect_error:
        print("NOTE: language detection fell back to Whisper's own (%s)." % detect_error)
        return None
    if not totals:
        return None
    best = max(totals, key=totals.get)
    share = totals[best] / max(1e-9, sum(totals.values()))
    print("Detected language: %s (%d%% across %d part(s) of the audio)."
          % (_FLEX_LANGUAGE_NAMES.get(best, best).title(), round(share * 100), len(ranked)))
    return best


_FLEX_LANGUAGE_NAMES = {
    "en": "english", "zh": "chinese", "de": "german", "es": "spanish", "ru": "russian", "ko": "korean",
    "fr": "french", "ja": "japanese", "pt": "portuguese", "tr": "turkish", "pl": "polish", "ca": "catalan",
    "nl": "dutch", "ar": "arabic", "sv": "swedish", "it": "italian", "id": "indonesian", "hi": "hindi",
    "fi": "finnish", "vi": "vietnamese", "he": "hebrew", "uk": "ukrainian", "el": "greek", "ms": "malay",
    "cs": "czech", "ro": "romanian", "da": "danish", "hu": "hungarian", "ta": "tamil", "no": "norwegian",
    "th": "thai", "ur": "urdu", "hr": "croatian", "bg": "bulgarian", "lt": "lithuanian", "la": "latin",
    "mi": "maori", "ml": "malayalam", "cy": "welsh", "sk": "slovak", "te": "telugu", "fa": "persian",
    "lv": "latvian", "bn": "bengali", "sr": "serbian", "az": "azerbaijani", "sl": "slovenian", "kn": "kannada",
    "et": "estonian", "mk": "macedonian", "br": "breton", "eu": "basque", "is": "icelandic", "hy": "armenian",
    "ne": "nepali", "mn": "mongolian", "bs": "bosnian", "kk": "kazakh", "sq": "albanian", "sw": "swahili",
    "gl": "galician", "mr": "marathi", "pa": "punjabi", "si": "sinhala", "km": "khmer", "sn": "shona",
    "yo": "yoruba", "so": "somali", "af": "afrikaans", "oc": "occitan", "ka": "georgian", "be": "belarusian",
    "tg": "tajik", "sd": "sindhi", "gu": "gujarati", "am": "amharic", "yi": "yiddish", "lo": "lao",
    "uz": "uzbek", "fo": "faroese", "ht": "haitian creole", "ps": "pashto", "tk": "turkmen", "nn": "nynorsk",
    "mt": "maltese", "sa": "sanskrit", "lb": "luxembourgish", "my": "burmese", "bo": "tibetan",
    "tl": "tagalog", "mg": "malagasy", "as": "assamese", "tt": "tatar", "haw": "hawaiian", "ln": "lingala",
    "ha": "hausa", "ba": "bashkir", "jw": "javanese", "su": "sundanese", "yue": "cantonese",
}
_FLEX_TRANSLATE_EXTRA = {
    "hi-latn": "Hinglish: Hindi written in Roman (Latin) letters, with everyday English words left in English",
    "zh-tw": "Traditional Chinese",
    "pt-br": "Brazilian Portuguese",
}


_FLEX_NO_SPACE = ("zh", "zh-tw", "ja", "th", "lo", "km", "my", "bo", "yue")


def _flex_language_name(code):
    code = (code or "").strip().lower()
    if code in _FLEX_TRANSLATE_EXTRA:
        return _FLEX_TRANSLATE_EXTRA[code]
    return _FLEX_LANGUAGE_NAMES.get(code, code).title()


def _flex_split_units(text, lang):


    text = " ".join((text or "").split())
    if not text:
        return []
    if (lang or "").lower() not in _FLEX_NO_SPACE:
        return [" " + w for w in text.split(" ")]
    import unicodedata
    units = []
    for ch in text:
        if ch.isspace():
            if units and not units[-1].endswith(" "):
                units[-1] += " "
            continue
        cat = unicodedata.category(ch)
        joins = bool(units) and (
            cat in ("Mn", "Mc", "Me") or cat.startswith("P")
            or (ch.isascii() and ch.isalnum() and units[-1][-1:].isascii() and units[-1][-1:].isalnum()))
        if joins:
            units[-1] += ch
        else:
            units.append(ch)
    return units


def _flex_retime(segment, units):

    spoken = []
    for word in segment.get("words", []) or []:
        try:
            start, end = float(word.get("start")), float(word.get("end"))
        except (TypeError, ValueError):
            continue
        if end > start:
            spoken.append((start, end))
    if spoken:
        start, end = spoken[0][0], spoken[-1][1]
    else:
        start, end = float(segment.get("start", 0.0)), float(segment.get("end", 0.0))
    if end <= start:
        end = start + 0.25 * max(1, len(units))
    weights = [max(1, len(u.strip())) for u in units]
    total = float(sum(weights)) or 1.0
    out, cursor = [], start
    for unit, weight in zip(units, weights):
        step = (end - start) * weight / total
        out.append({"word": unit, "start": round(cursor, 3), "end": round(cursor + step, 3),
                    "probability": 1.0})
        cursor += step
    return out


def _flex_chat(payload):
    import uuid
    url = CLOUD_BASE.rstrip("/") + os.environ.get("FLEX_AI_CHAT_PATH", "/v1/flex-ai/chat")
    headers = _cloud_auth_headers()
    headers["Idempotency-Key"] = str(uuid.uuid4())
    headers["X-Product-Name"] = "Flex AI"
    install = os.environ.get("FLEX_INSTALL_ID", "").strip()
    if install:
        payload = dict(payload, installId=install)
    for attempt in range(3):
        try:
            return _cloud_call("POST", url, body=payload, headers=headers, timeout=150.0)
        except CloudError as chat_error:
            data = chat_error.payload or {}
            message = data.get("message") or data.get("error")
            if isinstance(message, str) and message and str(chat_error) == "The request was refused.":
                chat_error = CloudError(message, code=chat_error.code, retryable=chat_error.retryable, payload=data)
            limited = chat_error.code in ("429", "RATE_LIMITED") or "rate limit" in str(chat_error).lower()
            if attempt < 2 and (limited or chat_error.code in ("NETWORK", "BAD_GATEWAY_BODY", "500", "502", "503", "504")):
                wait = data.get("retry_after") or data.get("retryAfter") or (8 if limited else 3)
                try:
                    wait = min(30.0, max(1.0, float(wait)))
                except (TypeError, ValueError):
                    wait = 5.0
                print("Flex AI is busy; retrying the translation in %d s..." % wait)
                time.sleep(wait)
                continue
            raise chat_error


_FLEX_TRANSLATE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "items": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {"id": {"type": "INTEGER"}, "text": {"type": "STRING"}},
                "required": ["id", "text"],
                "propertyOrdering": ["id", "text"],
            },
        }
    },
    "required": ["items"],
}


def _flex_translate_batch(batch, context, source, target):
    tgt = _flex_language_name(target)
    src = _flex_language_name(source) if source else "the spoken language"
    instruction = (
        "You translate video captions from %s to %s. Translate every caption so it reads as natural, "
        "spoken %s that fits on screen. Keep the meaning and tone. Keep names, brands, numbers, URLs "
        "and code exactly as they are. Never merge, split, drop, reorder or add captions: return one "
        "item for every id you receive, with the same id. If a caption is already in %s, return it "
        "unchanged. Return only the translation, with no notes." % (src, tgt, tgt, tgt))
    body = {"captions": [{"id": i, "text": t} for i, t in batch]}
    if context:
        body["context_before"] = context
    payload = {
        "prompt": json.dumps(body, ensure_ascii=False),
        "system_instruction": instruction,
        "response_schema": _FLEX_TRANSLATE_SCHEMA,
        "max_tokens": 8192,
        "temperature": 0.2,
        "clientVersion": "flex-stt-2",
    }
    data = _flex_chat(payload)
    reply = data.get("reply") if isinstance(data, dict) else None
    if isinstance(data, dict) and data.get("remainingCredits") is not None:
        try:
            print("FLEXAI_CREDITS:%d" % int(data.get("remainingCredits")))
        except (TypeError, ValueError):
            pass
    try:
        parsed = json.loads(reply) if isinstance(reply, str) else (reply or {})
    except ValueError:
        parsed = {}
    out = {}
    for item in (parsed.get("items") if isinstance(parsed, dict) else None) or []:
        try:
            key = int(item.get("id"))
        except (TypeError, ValueError, AttributeError):
            continue
        text = " ".join(str(item.get("text") or "").split())
        if text:
            out[key] = text
    charged = data.get("creditsCharged", 0) if isinstance(data, dict) else 0
    return out, charged


def flex_translate_result(result, target, source=None):



    segments = [s for s in result.get("segments", []) or [] if (s.get("text") or "").strip()]
    if not segments:
        return 0
    lines = [(i, " ".join(s["text"].split())) for i, s in enumerate(segments)]
    batches, current, size = [], [], 0
    for item in lines:
        if current and (len(current) >= 40 or size + len(item[1]) > 4000):
            batches.append(current)
            current, size = [], 0
        current.append(item)
        size += len(item[1])
    if current:
        batches.append(current)

    translated, credits = {}, 0
    name = _flex_language_name(target)
    for number, batch in enumerate(batches):
        print("Translating to %s... %d%%" % (name, int(100 * number / len(batches))))
        context = [t for _, t in lines[max(0, batch[0][0] - 3):batch[0][0]]]
        got, charged = _flex_translate_batch(batch, context, source, target)
        credits += charged or 0
        missing = [item for item in batch if item[0] not in got]
        if missing:
            again, charged = _flex_translate_batch(missing, context, source, target)
            credits += charged or 0
            got.update(again)
        translated.update(got)

    kept = 0
    for i, segment in enumerate(segments):
        text = translated.get(i)
        if not text:
            kept += 1
            continue
        units = _flex_split_units(text, target)
        segment["text"] = ("" if target in _FLEX_NO_SPACE else " ") + text
        segment["words"] = _flex_retime(segment, units)
    result["text"] = "".join(s.get("text", "") for s in result.get("segments", []) or [])
    result["translated_to"] = target
    print("Translating to %s... 100%%" % name)
    print("Translated %d caption(s) to %s%s." % (len(segments) - kept, name,
          (" (%s Flex AI credit(s))" % credits) if credits else ""))
    if kept:
        print("NOTE: %d caption(s) came back untranslated and were left as spoken." % kept)
    return len(segments) - kept


def _flex_whisper_translate(model, model_name, audio_path, transcribe_args):


    import whisper
    translator = model
    if model_name == "turbo":
        translator = None
        for name in ("large", "medium"):
            if _flex_model_file(name):
                print("Loading %s for offline translation..." % _FLEX_MODEL_LABELS[name])
                translator = _flex_load_model(whisper, name)
                break
        if translator is None:
            return None
    args = dict(transcribe_args)
    args.pop("initial_prompt", None)
    args["task"] = "translate"
    if _FLEX_STATE.get("spoken"):
        args["language"] = _FLEX_STATE["spoken"]
        args.pop("carry_initial_prompt", None)
    print("Translating to English offline with Whisper...")
    return _flex_run_transcribe(translator, audio_path, args)


def _flex_apply_translation(target, result, model, model_name, audio_path, transcribe_args,
                            pad_start, real_preroll, start_time, end_time, local_engine):



    target = (target or "").strip().lower()
    if not target or target in ("off", "none"):
        return result
    source = (_FLEX_STATE.get("spoken") or result.get("language") or transcribe_args.get("language") or "").strip().lower() or None
    if source and source == target:
        print("Captions are already in %s; nothing to translate." % _flex_language_name(target))
        return result
    if target != "en":
        print("NOTE: translation to %s is not available offline; only English is." % _flex_language_name(target))
    if target == "en" and local_engine:
        try:
            english = _flex_whisper_translate(model, model_name, audio_path, transcribe_args)
            if english and english.get("segments"):
                sel_duration = (end_time - start_time) if (start_time is not None and end_time is not None) else None
                _flex_sort_words_into_range(english, pad_start, real_preroll, sel_duration)
                english["translated_to"] = "en"
                print("Translated to English offline (%d caption(s))." % len(english.get("segments") or []))
                return english
            print("NOTE: offline translation needs the Large V3 or Medium model; Turbo cannot translate.")
        except Exception as offline_error:
            print("NOTE: offline translation failed: %s" % offline_error)
    print("Captions were kept in the spoken language.")
    return result










_FLEX_HINGLISH_PROMPT = ("Kya aap bhi video editing seekhna chahte ho? Toh simply After Effects open karo, "
                         "layer select karo aur effect apply kar do.")
_FLEX_STATE = {"keep_prompt": False, "spoken": None}


def _flex_carry_supported():
    try:
        import inspect
        import whisper
        return "carry_initial_prompt" in inspect.signature(whisper.transcribe).parameters
    except Exception:
        return False


def _flex_hinglish_policy(transcribe_args, roman):


    prompt = transcribe_args.get("initial_prompt") or ""
    if prompt and has_devanagari(prompt):
        transcribe_args.pop("initial_prompt", None)
    if _flex_stock():


        if roman and transcribe_args.get("language") in ("hi", "ur"):
            print("Roman Script: Whisper writes %s as it is; the captions are converted to Roman letters afterwards."
                  % _flex_language_name(transcribe_args.get("language")))
        return transcribe_args
    if roman and transcribe_args.get("language") in ("hi", "ur"):
        _FLEX_STATE["spoken"] = transcribe_args.get("language")
        transcribe_args["language"] = "en"
        transcribe_args["initial_prompt"] = _FLEX_HINGLISH_PROMPT
        if _flex_carry_supported():


            transcribe_args["carry_initial_prompt"] = True
        else:

            transcribe_args["condition_on_previous_text"] = True
        _FLEX_STATE["keep_prompt"] = True
        print("Hinglish: Whisper writes Roman Hinglish directly; English words stay in English.")
    return transcribe_args


def _flex_tokens(text):
    return re.findall(r"[a-z0-9']+", str(text or "").lower())


def _flex_is_prompt_echo(text, prompt):


    a, b = _flex_tokens(text), _flex_tokens(prompt)
    if len(a) < 6 or len(b) < 6:
        return False
    grams = set(tuple(b[i:i + 6]) for i in range(len(b) - 5))
    return any(tuple(a[i:i + 6]) in grams for i in range(len(a) - 5))


def _flex_drop_prompt_echo(result, transcribe_args):
    prompt = (transcribe_args or {}).get("initial_prompt") or ""
    if not prompt:
        return result
    kept, dropped = [], 0
    for segment in result.get("segments") or []:
        if _flex_is_prompt_echo(segment.get("text"), prompt) or _flex_is_glossary_echo(segment.get("text")):
            dropped += 1
            continue
        kept.append(segment)
    if dropped:
        for number, segment in enumerate(kept):
            segment["id"] = number
        result["segments"] = kept
        result["text"] = " ".join(str(s.get("text") or "").strip() for s in kept).strip()
        print("Removed %d caption(s) that only repeated the transcription prompt." % dropped)
    return result







def _flex_vocabulary_path():
    return os.path.join(os.path.expanduser("~"), ".flexgui", "caption_words.txt")


def _flex_vocabulary():


    try:
        with open(_flex_vocabulary_path(), "r", encoding="utf-8") as handle:
            raw = handle.read()
    except Exception:
        return []
    words, seen, size = [], set(), 0
    for part in re.split(r"[,;\n\r]+", raw):
        word = " ".join(part.split())[:60]
        key = word.lower()
        if not word or key in seen:
            continue
        if len(words) >= 40 or size + len(word) + 2 > 400:
            break
        seen.add(key)
        words.append(word)
        size += len(word) + 2
    return words


def _flex_apply_vocabulary(transcribe_args):




    if _flex_stock():
        if _flex_vocabulary():
            print("Custom words are paused in this version (stock models); your saved list is kept.")
        return transcribe_args
    words = _flex_vocabulary()
    if not words:
        return transcribe_args
    glossary = ", ".join(words) + "."
    prompt = (transcribe_args.get("initial_prompt") or "").strip()
    transcribe_args["initial_prompt"] = (prompt + " " + glossary) if prompt else glossary
    if _flex_carry_supported():
        transcribe_args["carry_initial_prompt"] = True
    _FLEX_STATE["glossary"] = words
    print("Custom words: %s" % ", ".join(words))
    return transcribe_args


def _flex_is_glossary_echo(text):


    entries = _FLEX_STATE.get("glossary") or []
    if not entries:
        return False
    tokens = _flex_tokens(text)
    if len(tokens) < 2:
        return False
    vocab = set()
    for entry in entries:
        vocab.update(_flex_tokens(entry))
    if any(token not in vocab for token in tokens):
        return False
    joined = " " + " ".join(tokens) + " "
    found = sum(1 for entry in entries if _flex_tokens(entry) and (" " + " ".join(_flex_tokens(entry)) + " ") in joined)
    return found >= 2


def _flex_gap_rescue(model, result, wav_path, transcribe_args):



    temp_path = None
    try:
        import wave
        import array
        import math
        if not wav_path or not str(wav_path).lower().endswith(".wav"):
            return result
        with wave.open(wav_path, "rb") as source:
            if source.getnchannels() != 1 or source.getsampwidth() != 2:
                return result
            rate = source.getframerate()
            raw = source.readframes(source.getnframes())
        pcm = array.array("h")
        pcm.frombytes(raw[:len(raw) - (len(raw) % 2)])
        if sys.byteorder == "big":
            pcm.byteswap()

        def rms(a, b):
            lo, hi = max(0, int(a * rate)), min(len(pcm), int(b * rate))
            if hi - lo < rate // 10:
                return 0.0
            step = max(1, (hi - lo) // 40000)
            part = pcm[lo:hi:step]
            return math.sqrt(sum(float(v) * float(v) for v in part) / len(part)) / 32768.0

        words = []
        for segment in result.get("segments") or []:
            for word in segment.get("words") or []:
                start, end = _flex_num(word.get("start")), _flex_num(word.get("end"))
                if start is not None and end is not None and end > start:
                    words.append((start, end))
        words.sort()
        if len(words) < 2:
            return result
        spoken = sorted(rms(a, b) for a, b in words[:200])
        floor = max(0.01, 0.35 * spoken[len(spoken) // 2])
        gaps = []
        for (a0, a1), (b0, b1) in zip(words, words[1:]):
            if b0 - a1 >= 2.5 and rms(a1 + 0.05, b0 - 0.05) >= floor:
                gaps.append((a1, b0))
        gaps = sorted(gaps, key=lambda g: g[0] - g[1])[:6]
        added = []
        for g0, g1 in gaps:
            print("No captions between %.1fs and %.1fs although there is speech; listening again..." % (g0, g1))
            lo, hi = max(0.0, g0 - 0.1), g1 + 0.1
            temp_path = os.path.join(tempfile.gettempdir(), "flex_gap_%d.wav" % os.getpid())
            pad = int(0.5 * rate)
            with wave.open(temp_path, "wb") as target:
                target.setnchannels(1)
                target.setsampwidth(2)
                target.setframerate(rate)
                chunk = pcm[int(lo * rate):int(hi * rate)]
                if sys.byteorder == "big":
                    chunk = array.array("h", chunk)
                    chunk.byteswap()
                target.writeframes(b"\x00\x00" * pad + chunk.tobytes() + b"\x00\x00" * pad)
            retry = dict(transcribe_args or {})
            retry["word_timestamps"] = True
            retry["condition_on_previous_text"] = False
            again = model.transcribe(temp_path, verbose=False, **retry)
            prompt = retry.get("initial_prompt") or ""
            for segment in again.get("segments") or []:
                if _flex_num(segment.get("avg_logprob"), 0.0) < -1.0 or _flex_num(segment.get("compression_ratio"), 0.0) > 2.4:
                    continue
                if _flex_num(segment.get("no_speech_prob"), 0.0) > 0.6 or _flex_is_prompt_echo(segment.get("text"), prompt):
                    continue
                placed = []
                for word in segment.get("words") or []:
                    start, end = _flex_num(word.get("start")), _flex_num(word.get("end"))
                    if start is None or end is None:
                        continue
                    start, end = start - 0.5 + lo, end - 0.5 + lo
                    if start < g0 - 0.05 or end > g1 + 0.05:
                        continue
                    w = dict(word)
                    w["start"], w["end"] = round(start, 3), round(max(end, start + 0.05), 3)
                    placed.append(w)
                text = "".join(str(w.get("word") or "") for w in placed).strip()
                if placed and not _flex_is_filler(text):
                    added.append({"start": placed[0]["start"], "end": placed[-1]["end"], "text": " " + text,
                                  "words": placed, "avg_logprob": segment.get("avg_logprob"),
                                  "no_speech_prob": segment.get("no_speech_prob"), "flex_rescued": True})
        if added:
            merged = sorted(list(result.get("segments") or []) + added, key=lambda s: _flex_num(s.get("start"), 0.0))
            for number, segment in enumerate(merged):
                segment["id"] = number
            result["segments"] = merged
            result["text"] = " ".join(str(s.get("text") or "").strip() for s in merged).strip()
            print("Recovered %d word(s) from %d gap(s)." % (sum(len(s["words"]) for s in added), len(gaps)))
        return result
    except Exception as gap_error:
        print("Could not re-check gaps (%s); continuing." % gap_error)
        return result
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass






def _flex_hinglish_file():
    full = os.path.join(_flex_whisper_cache(), "flex-hinglish.pt")
    try:
        if os.path.getsize(full) > 10000000:
            return full
    except OSError:
        pass
    return None


_FLEX_GPU = {"hinted": False}


def _flex_cuda_error(error):
    text = ("%s %s" % (type(error).__name__, error)).lower()
    return any(k in text for k in ("out of memory", "outofmemory", "cuda", "cublas", "cudnn"))


def _flex_cuda_free():
    try:
        import gc
        gc.collect()
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass


def _flex_model_device(model):
    try:
        return next(model.parameters()).device
    except Exception:
        return None


def _flex_first_line(error):
    text = str(error).strip()
    return text.splitlines()[0][:160] if text else type(error).__name__


def _flex_nvidia_gpu():

    if sys.platform == "darwin":
        return None
    import shutil
    import subprocess
    tools = [shutil.which("nvidia-smi")]
    if os.name == "nt":
        tools.append(os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32", "nvidia-smi.exe"))
        tools.append(os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"),
                                  "NVIDIA Corporation", "NVSMI", "nvidia-smi.exe"))
    for tool in tools:
        if not tool or not os.path.isfile(tool):
            continue
        try:
            out = subprocess.run([tool, "--query-gpu=name", "--format=csv,noheader"],
                                 stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, universal_newlines=True,
                                 timeout=8, creationflags=0x08000000 if os.name == "nt" else 0).stdout
        except Exception:
            continue
        names = [line.strip() for line in (out or "").splitlines() if line.strip()]
        if names:
            return names[0]
    return None


def _flex_report_device(model):


    device = _flex_model_device(model)
    if device is None:
        return
    if device.type == "cuda":
        try:
            import torch
            print("Device: GPU - %s (CUDA %s)" % (torch.cuda.get_device_name(device), torch.version.cuda))
        except Exception:
            print("Device: GPU")
        return
    print("Device: CPU")
    if _FLEX_GPU["hinted"]:
        return
    _FLEX_GPU["hinted"] = True
    gpu = _flex_nvidia_gpu()
    if not gpu:
        return
    try:
        import torch
        built, version = torch.version.cuda, torch.__version__
    except Exception:
        return
    if not built:
        print("NOTE: this PC has an NVIDIA GPU (%s), but the installed PyTorch %s is the CPU-only build, "
              "so captions run on the processor. Auto Captions > Engine > Use NVIDIA GPU switches it "
              "(one download of about 2.5 GB); transcribing is then several times faster." % (gpu, version))
    else:
        print("NOTE: PyTorch %s is built for CUDA %s but cannot reach the %s - update the NVIDIA driver "
              "(nvidia.com/drivers) and run it again." % (version, built, gpu))
    print("FLEX_GPU_IDLE: %s" % gpu)









_FLEX_PROGRESS = {"label": "", "stage": "", "at": 0.0, "pct": None, "main": False}


def _flex_stage(stage, pct=None, label=None, detail=""):
    if label:
        _FLEX_PROGRESS["label"] = label
    now = time.time()
    if stage == _FLEX_PROGRESS["stage"]:
        if pct is not None and pct == _FLEX_PROGRESS["pct"]:
            return
        if now - _FLEX_PROGRESS["at"] < 0.4 and pct != 100:
            return
    _FLEX_PROGRESS.update(stage=stage, at=now, pct=pct)
    detail = str(detail or "").replace("\r", " ").replace("\n", " ").replace("|", "/")[:160]
    try:
        print("FLEX_STAGE:%s|%s|%s|%s" % (stage, "" if pct is None else int(pct), _FLEX_PROGRESS["label"], detail))
        sys.stdout.flush()
    except Exception:
        pass


def _flex_size(n):
    n = float(n or 0)
    if n >= 1000 * 1024 ** 2:
        return "%.2f GB" % (n / 1024 ** 3)
    if n >= 1024 ** 2:
        return "%.0f MB" % (n / 1024 ** 2)
    return "%.0f KB" % (n / 1024)


def _flex_clock(seconds):
    seconds = int(max(0, seconds))
    if seconds >= 3600:
        return "%d:%02d:%02d" % (seconds // 3600, seconds % 3600 // 60, seconds % 60)
    return "%d:%02d" % (seconds // 60, seconds % 60)


def _flex_eta(seconds):
    if seconds < 60:
        return "%d s" % max(1, seconds)
    return "%d min" % round(seconds / 60.0)


def _flex_whisper_label(name):
    if name == "hinglish":
        return _FLEX_MODEL_LABELS["hinglish"]
    return "Whisper " + _FLEX_MODEL_LABELS.get(name, str(name))


def _flex_bar_report(kind, done, total, elapsed):
    pct = max(0, min(100, int(done * 100 / total)))
    if kind == "download":
        if done >= total:
            _flex_stage("load", None, None, "Download finished - reading the model into memory")
            return
        detail = "%s of %s" % (_flex_size(done), _flex_size(total))
        speed = done / elapsed if elapsed > 1 else 0
        if speed > 0:
            detail += " - %s/s - %s left" % (_flex_size(speed), _flex_eta((total - done) / speed))
        _flex_stage("download", pct, None, detail)
    elif _FLEX_PROGRESS["main"]:

        _flex_stage("transcribe", pct, None, "%s of %s of audio" % (_flex_clock(done / 100.0), _flex_clock(total / 100.0)))


def _flex_bar_class(base, kind):
    class _FlexBar(base):
        def __init__(self, *args, **kwargs):
            super(_FlexBar, self).__init__(*args, **kwargs)
            self._flex_done = 0
            self._flex_t0 = time.time()

        def update(self, n=1):
            result = super(_FlexBar, self).update(n)
            try:
                self._flex_done += n or 0
                total = float(self.total or 0)
                if total > 0:
                    _flex_bar_report(kind, self._flex_done, total, time.time() - self._flex_t0)
            except Exception:
                pass
            return result
    _FlexBar._flex = True
    return _FlexBar


def _flex_watch_bars(whisper):

    try:
        import tqdm as tqdm_module
        if getattr(whisper, "tqdm", None) is tqdm_module.tqdm:
            whisper.tqdm = _flex_bar_class(tqdm_module.tqdm, "download")
        transcribe_module = sys.modules.get("whisper.transcribe")
        if transcribe_module is not None and getattr(transcribe_module, "tqdm", None) is tqdm_module:
            import types
            transcribe_module.tqdm = types.SimpleNamespace(tqdm=_flex_bar_class(tqdm_module.tqdm, "transcribe"))
    except Exception:
        pass


_FLEX_TQDM_LINE = re.compile(r"(\d{1,3})%\|[^|]*\|\s*([\d.]+)\s*([kKMGT]?)i?B?\s*/\s*([\d.]+)\s*([kKMGT]?)i?B?"
                             r"(?:[^\]]*?,\s*([\d.]+\s*[kKMGT]?i?B/s))?")
_FLEX_TQDM_UNITS = {"": "", "k": " KB", "K": " KB", "M": " MB", "G": " GB", "T": " TB"}


def _flex_tqdm_stage(line):

    m = _FLEX_TQDM_LINE.search(line)
    if not m:
        return False
    pct, done, done_unit, total, total_unit, speed = m.groups()
    if done_unit or total_unit:
        detail = "%s%s of %s%s" % (done, _FLEX_TQDM_UNITS[done_unit], total, _FLEX_TQDM_UNITS[total_unit])
        if speed:
            detail += " - " + speed.replace(" ", "")
    else:
        detail = "file %s of %s" % (done, total)
    name = line[:m.start()].strip().rstrip(":").strip()
    if name and len(name) < 60:
        detail = name + " - " + detail
    _flex_stage("download", int(pct), None, detail)
    return True


def _flex_load_model(whisper, name):



    if name == "hinglish" and _flex_stock():
        name = _flex_resolve_model(name)
    _flex_watch_bars(whisper)
    _flex_stage("load", None, _flex_whisper_label(name),
                "Reading the model into memory" if (name == "hinglish" or _flex_model_file(name))
                else "First use - downloading the model")
    try:
        model = _flex_load_model_dev(whisper, name, None)
    except Exception as gpu_error:
        if not _flex_cuda_error(gpu_error):
            raise
        print("NOTE: the GPU could not take the %s model (%s) - this run uses the CPU." % (name, _flex_first_line(gpu_error)))
        _FLEX_GPU["hinted"] = True
        _flex_cuda_free()
        model = _flex_load_model_dev(whisper, name, "cpu")
    _flex_report_device(model)
    _flex_stage("ready", None, None, "Model loaded")
    return model









import shutil
import subprocess

_FLEX_HF_PACKAGES = ["torch", "torchaudio", "transformers", "soundfile", "librosa", "sentencepiece",
                     "huggingface_hub", "onnxruntime==1.20.1", "onnx==1.20.1"]
_FLEX_ENGINES = {


    "qwen3-asr": {"env": "qwen", "label": "Qwen3-ASR 0.6B",
                  "packages": ["qwen-asr==0.0.6", "torch", "transformers==4.57.6", "accelerate==1.12.0"]},
    "moonshine": {"env": "moonshine", "label": "Moonshine Medium", "packages": ["moonshine-voice"]},
    "canary": {"env": "hf", "label": "NVIDIA Canary 1B v2", "packages": _FLEX_HF_PACKAGES},
    "sravaani": {"env": "hf", "label": "SraVaani 1.0", "packages": _FLEX_HF_PACKAGES},
    "indicconformer": {"env": "hf", "label": "AI4Bharat IndicConformer 600M", "packages": _FLEX_HF_PACKAGES},
}
_FLEX_PIP_NAMES = {"yaml": "pyyaml", "sklearn": "scikit-learn", "cv2": "opencv-python", "PIL": "pillow",
                   "google.protobuf": "protobuf", "Levenshtein": "python-Levenshtein"}
_FLEX_UNSPACED = ("zh", "ja", "yue", "th", "lo", "my", "km", "bo")


def _flex_engines_config_path():
    return os.path.join(os.path.expanduser("~"), ".flexgui", "stt_engines.json")


def _flex_engines_config():
    try:
        with open(_flex_engines_config_path(), "r", encoding="utf-8") as handle:
            data = json.load(handle)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _flex_engines_save(update):

    path = _flex_engines_config_path()
    data = _flex_engines_config()
    data.update(update)
    data.setdefault("version", 1)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path + ".part", "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=1)
        os.replace(path + ".part", path)
    except Exception as save_error:
        print("NOTE: could not save %s (%s)." % (path, save_error))


def _flex_models_dir():
    chosen = str(_flex_engines_config().get("models_dir") or "").strip()
    if chosen:
        return chosen
    if sys.platform == "win32":
        return os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), "Flex", "stt-engines")
    if sys.platform == "darwin":
        return os.path.join(os.path.expanduser("~"), "Library", "Application Support", "Flex", "stt-engines")
    return os.path.join(os.path.expanduser("~"), ".local", "share", "flex", "stt-engines")


def _flex_venv_python(env_dir):
    return os.path.join(env_dir, "Scripts", "python.exe") if sys.platform == "win32" else os.path.join(env_dir, "bin", "python")


def _flex_python_version(exe):
    try:
        out = subprocess.run([exe, "-c", "import sys; print('%d.%d' % sys.version_info[:2])"],
                             capture_output=True, text=True, timeout=20).stdout.strip()
        major, minor = out.split(".")
        return int(major), int(minor)
    except Exception:
        return None


def _flex_engine_base_python():


    if (3, 10) <= sys.version_info[:2] < (3, 14):
        return sys.executable
    candidates = []
    for minor in (12, 11, 10, 13):
        if sys.platform == "win32":
            local = os.environ.get("LOCALAPPDATA") or ""
            candidates += [os.path.join(local, "Programs", "Python", "Python3%d" % minor, "python.exe"),
                           "C:\\Python3%d\\python.exe" % minor]
        else:
            candidates += ["/opt/homebrew/bin/python3.%d" % minor, "/usr/local/bin/python3.%d" % minor,
                           "/Library/Frameworks/Python.framework/Versions/3.%d/bin/python3" % minor,
                           "/usr/bin/python3.%d" % minor]
        found = shutil.which("python3.%d" % minor)
        if found:
            candidates.append(found)
    for exe in candidates:
        if exe and os.path.exists(exe):
            v = _flex_python_version(exe)
            if v and (3, 10) <= v < (3, 14):
                return exe
    if sys.platform == "win32":
        for minor in (12, 11, 10, 13):
            try:
                out = subprocess.run(["py", "-3.%d" % minor, "-c", "import sys; print(sys.executable)"],
                                     capture_output=True, text=True, timeout=20).stdout.strip()
                if out and os.path.exists(out):
                    return out
            except Exception:
                pass
    return None


def _flex_pip(python, packages):
    print("Installing %s ..." % " ".join(packages))
    sys.stdout.flush()
    proc = subprocess.Popen([python, "-m", "pip", "install", "--disable-pip-version-check"] + list(packages),
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace")
    for line in proc.stdout:
        line = line.rstrip()
        if line and not line.startswith("  ") and "already satisfied" not in line:
            _flex_stage("setup", None, None, line[:120])
            print("  pip: " + line[:200])
            sys.stdout.flush()
    return proc.wait() == 0


def _flex_engine_env(name):

    spec = _FLEX_ENGINES[name]
    env_dir = os.path.join(_flex_models_dir(), "envs", spec["env"])
    python = _flex_venv_python(env_dir)
    stamp_path = os.path.join(env_dir, "flex-stamp.json")
    stamp = {}
    try:
        with open(stamp_path, "r", encoding="utf-8") as handle:
            stamp = json.load(handle)
    except Exception:
        stamp = {}
    if os.path.exists(python) and sorted(stamp.get("packages") or []) == sorted(spec["packages"]):
        return python
    base = _flex_engine_base_python()
    if not base:
        raise RuntimeError("%s needs Python 3.10, 3.11, 3.12 or 3.13 (this one is %d.%d). Install Python 3.12 from "
                           "python.org, or let Flex Product Manager set the engine up." % ((spec["label"],) + tuple(sys.version_info[:2])))
    _flex_stage("setup", None, spec["label"], "Installing its Python packages (one time, a few minutes)")
    if not os.path.exists(python):
        print("Setting up %s in %s (one time, a few minutes)..." % (spec["label"], env_dir))
        os.makedirs(os.path.dirname(env_dir), exist_ok=True)
        made = subprocess.run([base, "-m", "venv", env_dir], capture_output=True, text=True)
        if made.returncode != 0 or not os.path.exists(python):
            raise RuntimeError("could not create the %s environment: %s" % (spec["label"], (made.stderr or made.stdout).strip()[:300]))
        subprocess.run([python, "-m", "pip", "install", "--upgrade", "--disable-pip-version-check", "pip"], capture_output=True)
    if not _flex_pip(python, spec["packages"]):
        raise RuntimeError("installing %s's packages failed - see the lines above." % spec["label"])
    try:
        with open(stamp_path, "w", encoding="utf-8") as handle:
            json.dump({"packages": spec["packages"], "python": base, "at": time.strftime("%Y-%m-%dT%H:%M:%S")}, handle)
    except Exception:
        pass
    engines = _flex_engines_config().get("engines") or {}
    engines[name] = {"env": spec["env"], "python": python, "ready": True, "installed_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    _flex_engines_save({"engines": engines})
    return python


def _flex_engine_environ():
    env = dict(os.environ)
    root = _flex_models_dir()
    env["HF_HOME"] = os.path.join(root, "hf")
    env["FLEX_MOONSHINE_CACHE"] = os.path.join(root, "moonshine")
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    if not _flex_stock():
        env["FLEX_STT_CUSTOM"] = "1"
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    try:
        with open(os.path.join(os.path.expanduser("~"), ".flexgui", "hf_token.txt"), "r") as handle:
            token = handle.read().strip()
            if token:
                env["HF_TOKEN"] = token
    except Exception:
        pass
    return env


def _flex_engine_wav(path):

    if str(path).lower().endswith(".wav"):
        return path, None
    out = os.path.join(tempfile.gettempdir(), "flex_engine_%d.wav" % int(time.time() * 1000))
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", path, "-ac", "1", "-ar", "16000", out], capture_output=True)
    return out, out


def _flex_read_wav_16k(path):
    import numpy as np
    import wave as _wave
    with _wave.open(path, "rb") as w:
        ch, width, rate, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        raw = w.readframes(n)
    a = np.frombuffer(raw, dtype="<i2").astype("float32") / 32768.0 if width == 2 else np.frombuffer(raw, dtype="u1").astype("float32") / 128.0 - 1.0
    if ch > 1:
        a = a.reshape(-1, ch).mean(axis=1)
    if rate != 16000 and len(a):
        a = np.interp(np.arange(0, len(a), rate / 16000.0), np.arange(len(a)), a).astype("float32")
    return a


class _EngineModel(object):



    def __init__(self, name):
        self.name = name
        self.spec = _FLEX_ENGINES[name]
        self.proc = None
        self.python = None
        self.seq = 0
        self.aligner = None
        self._bar_at = 0.0

    def _log(self, line):
        line = line.rstrip()
        if not line:
            return
        if "%|" in line:
            _flex_tqdm_stage(line.split("\r")[-1] or line)
        if "%|" in line or "\r" in line:
            if time.time() - self._bar_at < 5:
                return
            self._bar_at = time.time()
            line = line.split("\r")[-1]
        print("  " + line[:220])
        sys.stdout.flush()

    def _event(self):
        while True:
            raw = self.proc.stdout.readline()
            if not raw:
                return {"event": "error", "error": "%s stopped unexpectedly (see the lines above)." % self.spec["label"]}
            text = raw.decode("utf-8", "replace") if isinstance(raw, bytes) else raw
            stripped = text.strip()
            if stripped.startswith("{") and '"event"' in stripped:
                try:
                    ev = json.loads(stripped)
                except Exception:
                    self._log(text)
                    continue
                if ev.get("event") == "progress":
                    msg = str(ev.get("msg", ""))
                    _flex_stage("load", None, None, msg.split(": ", 1)[-1] if msg.startswith(self.spec["label"].split(" ")[0]) else msg)
                    print(msg)
                    sys.stdout.flush()
                    continue
                return ev
            self._log(text)

    def _install_module(self, module):
        top = str(module).split(".")[0]
        package = _FLEX_PIP_NAMES.get(module) or _FLEX_PIP_NAMES.get(top) or top

        for spec in self.spec.get("packages") or []:
            if spec.split("==")[0].replace("_", "-").lower() == package.replace("_", "-").lower():
                package = spec
        print("%s needs the Python package '%s'; installing it into its environment..." % (self.spec["label"], package))
        return _flex_pip(self.python, [package])

    def _start(self):
        script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "flex_stt_engines.py")
        _flex_stage("load", None, self.spec["label"], "Starting its Python environment")
        for attempt in range(6):
            self.python = self.python or _flex_engine_env(self.name)
            self.proc = subprocess.Popen([self.python, "-u", script, "--serve", "--engine", self.name],
                                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                         env=_flex_engine_environ())
            ev = self._event()
            if ev.get("event") == "ready":
                _flex_stage("transcribe", None, None, "Listening to your audio")
                return
            self._stop()
            if ev.get("event") == "need" and self._install_module(ev.get("module")):
                continue
            raise RuntimeError(ev.get("error") or "%s could not start." % self.spec["label"])
        raise RuntimeError("%s kept asking for more packages; giving up." % self.spec["label"])

    def _stop(self):
        try:
            if self.proc and self.proc.poll() is None:
                self.proc.stdin.write(b'{"quit": true}\n')
                self.proc.stdin.flush()
                self.proc.wait(timeout=10)
        except Exception:
            try:
                self.proc.terminate()
            except Exception:
                pass
        self.proc = None

    def to(self, device):
        return self

    def transcribe(self, audio_path, verbose=False, **kwargs):
        wav, temp = _flex_engine_wav(audio_path)
        language = kwargs.get("language")
        language = None if language in (None, "", "auto") else language
        try:
            for attempt in range(6):
                if self.proc is None or self.proc.poll() is not None:
                    self._start()
                self.seq += 1
                request = {"id": self.seq, "audio": os.path.abspath(wav), "language": language,
                           "keyterms": [] if _flex_stock() else list(_FLEX_STATE.get("glossary") or [])}
                self.proc.stdin.write((json.dumps(request) + "\n").encode("utf-8"))
                self.proc.stdin.flush()
                ev = self._event()
                if ev.get("event") == "need":
                    self._stop()
                    if self._install_module(ev.get("module")):
                        continue
                if ev.get("event") != "result":
                    raise RuntimeError(ev.get("error") or "%s returned nothing." % self.spec["label"])
                lang = ev.get("language") or language or "en"
                return self._finish(ev.get("segments") or [], wav, lang)
            raise RuntimeError("%s kept asking for more packages; giving up." % self.spec["label"])
        finally:
            if temp:
                try:
                    os.remove(temp)
                except OSError:
                    pass


    def _whisper(self):


        if self.aligner is None:
            import whisper
            wanted = os.environ.get("FLEX_ALIGN_MODEL", "").strip()
            if not wanted:
                files = {"small": "small.pt", "base": "base.pt", "medium": "medium.pt", "turbo": "large-v3-turbo.pt",
                         "tiny": "tiny.pt", "large": "large-v3.pt"}
                wanted = "base"
                for key in ("small", "base", "medium", "turbo", "tiny", "large"):
                    if os.path.exists(os.path.join(_flex_whisper_cache(), files[key])):
                        wanted = key
                        break
            print("Timing the words with Whisper's aligner (%s)..." % wanted)
            self.aligner = whisper.load_model(_flex_load_name(wanted), device="cpu")
        return self.aligner

    def _align(self, segs, wav, lang):
        need = [s for s in segs if not s.get("words") and str(s.get("text") or "").strip()]
        if not need:
            return
        try:
            import whisper
            from whisper.timing import find_alignment
            from whisper.audio import HOP_LENGTH, N_SAMPLES
            model = self._whisper()
            audio = _flex_read_wav_16k(wav)
            code = lang if lang in whisper.tokenizer.LANGUAGES else ("hi" if lang in ("brx", "doi", "kok", "ks", "mai", "mni", "or", "sat") else "en")
            tokenizer = whisper.tokenizer.get_tokenizer(model.is_multilingual, num_languages=model.num_languages,
                                                        language=code, task="transcribe")
        except Exception as setup_error:
            print("NOTE: Whisper's aligner is not available (%s); words are spread evenly." % _flex_first_line(setup_error))
            model = None
        for seg in need:
            words = []
            if model is not None:
                try:
                    start = float(seg["start"])
                    clip = audio[int(start * 16000):int(float(seg["end"]) * 16000)][:N_SAMPLES]
                    mel = whisper.log_mel_spectrogram(whisper.pad_or_trim(clip), model.dims.n_mels).to(model.device)
                    tokens = tokenizer.encode(" " + str(seg["text"]).strip())
                    for t in find_alignment(model, tokenizer, tokens, mel, len(clip) // HOP_LENGTH):
                        if t.word.strip():
                            words.append({"word": t.word.strip(), "start": start + float(t.start), "end": start + float(t.end),
                                          "probability": float(t.probability)})
                except Exception as align_error:
                    print("NOTE: could not align a chunk (%s); its words are spread evenly." % _flex_first_line(align_error))
                    words = []
            if not words:
                parts = str(seg["text"]).split() if lang not in _FLEX_UNSPACED else list(str(seg["text"]).replace(" ", ""))
                total = sum(len(p) for p in parts) or 1
                t, span = float(seg["start"]), max(0.1, float(seg["end"]) - float(seg["start"]))
                for p in parts:
                    d = span * len(p) / total
                    words.append({"word": p, "start": t, "end": t + d, "probability": 0.5})
                    t += d
            seg["words"] = words

    @staticmethod
    def _merge_punctuation(words):


        out, lead = [], ""
        for w in words:
            t = str(w.get("word") or "").strip()
            if not t:
                continue
            if not any(c.isalnum() for c in t):
                if out and not t[0] in "([{\u00bf\u00a1\"'":
                    out[-1] = dict(out[-1], word=out[-1]["word"].strip() + t, end=max(out[-1]["end"], w.get("end", out[-1]["end"])))
                else:
                    lead += t
                continue
            out.append(dict(w, word=lead + t))
            lead = ""
        return out

    def _finish(self, segs, wav, lang):
        self._align(segs, wav, lang)
        spaced = lang not in _FLEX_UNSPACED
        words = []
        for seg in segs:
            for w in self._merge_punctuation(seg.get("words") or []):
                if str(w.get("word") or "").strip():
                    words.append(w)
        words.sort(key=lambda w: w["start"])
        out, current = [], []

        def close():
            if not current:
                return
            parts = [x["word"].strip() for x in current]
            text = (" " + " ".join(parts)) if spaced else "".join(parts)
            out.append({"id": len(out), "seek": 0, "start": current[0]["start"], "end": current[-1]["end"],
                        "text": text, "tokens": [], "temperature": 0.0, "avg_logprob": -0.2,
                        "compression_ratio": 1.2, "no_speech_prob": 0.0,
                        "words": [{"word": (" " if spaced else "") + x["word"].strip(), "start": round(x["start"], 3),
                                   "end": round(max(x["end"], x["start"] + 0.02), 3),
                                   "probability": x.get("probability", 1.0)} for x in current]})
            del current[:]

        for w in words:
            if current:
                gap = w["start"] - current[-1]["end"]
                ended = current[-1]["word"].strip()[-1:] in ".?!\u0964\u0965\u3002\uff1f\uff01"
                if ended or gap >= 0.6 or w["end"] - current[0]["start"] > 6.0 or len(current) >= 14:
                    close()
            current.append(w)
        close()
        return {"text": "".join(s["text"] for s in out).strip(), "segments": out, "language": lang}











_FLEX_CACHE_VERSION = 1
_FLEX_CACHE_MAX_BYTES = 300 * 1024 * 1024
_FLEX_CACHE_MAX_AGE = 90 * 24 * 3600


def _flex_cache_dir():
    if os.environ.get("FLEX_AC_CACHE_DIR"):
        return os.environ["FLEX_AC_CACHE_DIR"]
    home = os.path.expanduser("~")
    if sys.platform == "darwin":
        return os.path.join(home, "Library", "Application Support", "Flex", "caption-cache")
    if os.name == "nt":
        return os.path.join(os.environ.get("APPDATA") or home, "Flex", "caption-cache")
    return os.path.join(home, ".cache", "flex", "caption-cache")


def _flex_cache_key(audio_path, parts):
    import hashlib
    digest = hashlib.sha256()
    digest.update(json.dumps(parts, sort_keys=True, ensure_ascii=True).encode("utf-8"))
    with open(audio_path, "rb") as handle:
        while True:
            block = handle.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def _flex_cache_get(key):
    if not key:
        return None
    path = os.path.join(_flex_cache_dir(), key + ".json")
    try:
        if time.time() - os.path.getmtime(path) > _FLEX_CACHE_MAX_AGE:
            return None
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if data.get("v") != _FLEX_CACHE_VERSION or not isinstance(data.get("result"), dict):
            return None
        try:
            os.utime(path, None)
        except Exception:
            pass
        return data
    except Exception:
        return None


def _flex_cache_put(key, result, pad_start, preroll):
    if not key or not isinstance(result, dict) or not result.get("segments"):
        return
    folder = _flex_cache_dir()
    try:
        os.makedirs(folder, exist_ok=True)
        final = os.path.join(folder, key + ".json")
        temp = final + ".%d.tmp" % os.getpid()
        with open(temp, "w", encoding="utf-8") as handle:
            json.dump({"v": _FLEX_CACHE_VERSION, "at": time.time(), "pad_start": pad_start,
                       "preroll": preroll, "result": result}, handle, ensure_ascii=False)
        os.replace(temp, final)
        entries = []
        for name in os.listdir(folder):
            full = os.path.join(folder, name)
            try:
                st = os.stat(full)
            except Exception:
                continue
            if name.endswith(".tmp") and time.time() - st.st_mtime > 3600:
                try:
                    os.remove(full)
                except Exception:
                    pass
                continue
            if name.endswith(".json"):
                entries.append((st.st_mtime, st.st_size, full))
        entries.sort()
        total = sum(e[1] for e in entries)
        for mtime, size, full in entries:
            if total <= _FLEX_CACHE_MAX_BYTES and time.time() - mtime <= _FLEX_CACHE_MAX_AGE:
                break
            if full == final:
                continue
            try:
                os.remove(full)
                total -= size
            except Exception:
                pass
    except Exception as cache_error:
        print("NOTE: could not keep this transcript for next time: %s" % cache_error)


def _flex_run_transcribe(model, audio_path, args):

    try:
        return model.transcribe(audio_path, verbose=False, **args)
    except Exception as gpu_error:
        device = None if isinstance(model, (_CloudModel, _EngineModel)) else _flex_model_device(model)
        if device is None or device.type != "cuda" or not _flex_cuda_error(gpu_error):
            raise
        print("NOTE: the GPU ran out of room (%s) - finishing on the CPU." % _flex_first_line(gpu_error))
        model.to("cpu")
        _flex_cuda_free()
        print("Device: CPU")
        return model.transcribe(audio_path, verbose=False, **args)


def _flex_load_model_dev(whisper, name, device):


    if name == "hinglish":
        path = _flex_hinglish_file()
        model = whisper.load_model(path, device=device)
        try:
            import torch
            base = torch.load(path, map_location="cpu", weights_only=False).get("flex", {}).get("base", "medium")
            heads = getattr(whisper, "_ALIGNMENT_HEADS", {}).get(base)
            if heads:
                model.set_alignment_heads(heads)
        except Exception as heads_error:
            print("NOTE: word timings use default heads (%s)." % heads_error)
        return model
    return whisper.load_model(_flex_load_name(name), device=device)



def _flex_unpadded(result, pad):







    try:
        pad = float(pad or 0.0)
    except (TypeError, ValueError):
        pad = 0.0
    if pad <= 0.0 or not isinstance(result, dict):
        return result

    def number(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def shifted(item):

        moved = dict(item)
        end = number(item.get("end"))
        if end is not None:
            if end - pad <= 0.0:
                return None
            moved["end"] = end - pad
        start = number(item.get("start"))
        if start is not None:
            moved["start"] = max(0.0, start - pad)
        return moved

    out = dict(result)
    segments = []
    for segment in result.get("segments") or []:
        if not isinstance(segment, dict):
            continue
        moved = shifted(segment)
        if moved is None:
            continue
        if "words" in segment:
            words = []
            for word in segment.get("words") or []:
                if isinstance(word, dict):
                    w = shifted(word)
                    if w is not None:
                        words.append(w)
            moved["words"] = words
        segments.append(moved)
    out["segments"] = segments
    out["flex_pad_removed"] = pad
    return out

def _flex_lower_priority():








    if os.environ.get("FLEX_NORMAL_PRIORITY") == "1":
        return
    try:
        if sys.platform == "win32":
            import ctypes
            from ctypes import wintypes

            kernel32 = ctypes.WinDLL("kernel32")
            kernel32.GetCurrentProcess.restype = wintypes.HANDLE
            kernel32.GetPriorityClass.argtypes = [wintypes.HANDLE]
            kernel32.GetPriorityClass.restype = wintypes.DWORD
            kernel32.SetPriorityClass.argtypes = [wintypes.HANDLE, wintypes.DWORD]
            kernel32.SetPriorityClass.restype = wintypes.BOOL
            below_normal, idle = 0x4000, 0x40
            handle = kernel32.GetCurrentProcess()
            if kernel32.GetPriorityClass(handle) not in (below_normal, idle):
                kernel32.SetPriorityClass(handle, below_normal)
        elif hasattr(os, "getpriority") and hasattr(os, "setpriority"):

            if os.getpriority(os.PRIO_PROCESS, 0) < 10:
                os.setpriority(os.PRIO_PROCESS, 0, 10)
    except Exception:
        pass
























_RETAKE_PAUSE = 0.40
_RETAKE_HOP = 0.01
_RETAKE_RANGE_DB = 18.0
_RETAKE_UNHEARD = 0.45
_RETAKE_MAX_STRETCH = 28.0
_RETAKE_STOCK = set([
    "thank you", "thank you very much", "thank you so much", "thanks", "thanks a lot",
    "thanks for watching", "thank you for watching", "thanks for listening", "thank you for listening",
    "please subscribe", "subscribe", "like and subscribe", "please like and subscribe",
    "see you next time", "see you in the next video", "bye", "bye bye", "goodbye",
    "you", "music", "applause", "laughter", "silence", "the end", "so", "okay", "oh",
])
_RETAKE_STOCK_HEADS = ("subtitles by", "subtitle by", "subtitles made by", "captions by", "captioned by",
                       "transcribed by", "transcription by", "translated by", "translation by",
                       "thanks for watching", "thank you for watching", "amara org", "copyright")


def _flex_retake_plain(text):
    plain = re.sub(r"[\[\]\(\)]", " ", str(text or "")).lower()
    plain = re.sub(r"[^\w\s]", " ", plain, flags=re.UNICODE)
    return re.sub(r"\s+", " ", plain).strip()


def _flex_retake_is_stock(text):

    plain = _flex_retake_plain(text)
    if not plain:
        return True
    if plain in _RETAKE_STOCK:
        return True
    for head in _RETAKE_STOCK_HEADS:
        if plain == head or plain.startswith(head + " "):
            return True
    return False


def _flex_retake_levels(wav_path):

    import wave
    if not wav_path or not str(wav_path).lower().endswith(".wav") or not os.path.exists(wav_path):
        return None
    with wave.open(wav_path, "rb") as source:
        if source.getnchannels() != 1 or source.getsampwidth() != 2:
            return None
        rate = source.getframerate()
        raw = source.readframes(source.getnframes())
    raw = raw[:len(raw) - (len(raw) % 2)]
    hop = max(1, int(round(rate * _RETAKE_HOP)))
    try:
        import numpy as np
        pcm = np.frombuffer(raw, dtype="<i2")
        count = len(pcm) // hop
        if count < 50:
            return None
        frames = pcm[:count * hop].astype(np.float64).reshape(count, hop) / 32768.0
        levels = [float(v) for v in 10.0 * np.log10((frames * frames).mean(axis=1) + 1e-12)]
    except ImportError:
        import array
        import math
        pcm = array.array("h")
        pcm.frombytes(raw)
        if sys.byteorder == "big":
            pcm.byteswap()
        count = len(pcm) // hop
        if count < 50:
            return None
        levels = []
        for k in range(count):
            part = pcm[k * hop:(k + 1) * hop]
            levels.append(10.0 * math.log10(sum(float(v) * v for v in part) / hop / 1073741824.0 + 1e-12))
    return pcm, rate, levels


def _flex_retake_islands(levels):






    heard = sorted(v for v in levels if v > -100.0)
    if len(heard) < 50:
        return None
    floor = heard[int(len(heard) * 0.10)]
    peak = heard[int(len(heard) * 0.95)]
    if peak - floor < _RETAKE_RANGE_DB:
        return None
    threshold = max(floor + 12.0, peak - 30.0)
    voiced = [1 if v >= threshold else 0 for v in levels]
    need = int(round(_RETAKE_PAUSE / _RETAKE_HOP))
    spans, start, last, quiet = [], None, None, 0
    for k, on in enumerate(voiced):
        if on:
            if start is None:
                start = k
            last, quiet = k, 0
        elif start is not None:
            quiet += 1
            if quiet >= need:
                spans.append((start, last + 1))
                start, quiet = None, 0
    if start is not None:
        spans.append((start, last + 1))
    spans = [s for s in spans if sum(voiced[s[0]:s[1]]) >= 8]
    if not spans:
        return None
    total = [0]
    for on in voiced:
        total.append(total[-1] + on)
    islands = []
    for n, (a, b) in enumerate(spans):
        islands.append({"start": a * _RETAKE_HOP, "end": b * _RETAKE_HOP,
                        "pause": (a - spans[n - 1][1]) * _RETAKE_HOP if n else None})
    for n, isl in enumerate(islands):

        isl["lo"] = 0.0 if n == 0 else (islands[n - 1]["end"] + isl["start"]) / 2.0
        isl["hi"] = float("inf") if n == len(islands) - 1 else (isl["end"] + islands[n + 1]["start"]) / 2.0
    return {"islands": islands, "voiced": voiced, "sum": total,
            "threshold": threshold, "floor": floor, "peak": peak}


def _flex_retake_voiced(vad, a, b):

    count = len(vad["voiced"])
    lo = min(count, max(0, int(a / _RETAKE_HOP)))
    hi = min(count, max(lo, int(b / _RETAKE_HOP + 0.999)))
    return (vad["sum"][hi] - vad["sum"][lo]) * _RETAKE_HOP


def _flex_retake_home(vad, start, end):

    islands = vad["islands"]
    best, best_voice = None, 0.0
    for k, isl in enumerate(islands):
        if isl["end"] <= start - 0.5:
            continue
        if isl["start"] >= end + 0.5:
            break
        voice = _flex_retake_voiced(vad, max(start, isl["start"]), min(end, isl["end"])) if end > start else 0.0
        if voice > best_voice:
            best, best_voice = k, voice
    if best is not None:
        return best
    mid = (start + end) / 2.0
    for k, isl in enumerate(islands):
        if isl["lo"] <= mid < isl["hi"]:
            return k
    return len(islands) - 1


def _flex_retake_words(result):
    out = []
    for segment in result.get("segments") or []:
        for word in segment.get("words") or []:
            start, end = _flex_num(word.get("start")), _flex_num(word.get("end"))
            if start is not None and end is not None and end > start:
                out.append((start, end, word))
    out.sort(key=lambda item: item[0])
    return out


def _flex_retake_suspects(vad, result):

    islands, voiced = vad["islands"], vad["voiced"]
    words = _flex_retake_words(result)
    if not words:
        return []
    lengths = sorted(end - start for start, end, _ in words)
    long_word = max(1.2, 4.0 * lengths[len(lengths) // 2])
    weight, why = {}, {}

    def flag(k, amount, reason):
        if amount > weight.get(k, 0.0):
            weight[k], why[k] = amount, reason

    covered = bytearray(len(voiced))
    for start, end, _ in words:
        for f in range(max(0, int((start - 0.1) / _RETAKE_HOP)), min(len(voiced), int((end + 0.1) / _RETAKE_HOP) + 1)):
            covered[f] = 1
    for k, isl in enumerate(islands):
        run = best = 0
        for f in range(int(isl["start"] / _RETAKE_HOP), min(len(voiced), int(isl["end"] / _RETAKE_HOP))):
            if covered[f]:
                run = 0
            else:
                run += voiced[f]
                best = max(best, run)
        if best * _RETAKE_HOP >= _RETAKE_UNHEARD:
            flag(k, best * _RETAKE_HOP, "%.1fs of speech with no words" % (best * _RETAKE_HOP))
    for start, end, word in words:
        touched = []
        for k, isl in enumerate(islands):
            if isl["end"] <= start or isl["start"] >= end:
                continue
            if _flex_retake_voiced(vad, max(start, isl["start"]), min(end, isl["end"])) >= 0.08:
                touched.append(k)
        text = str(word.get("word") or "").strip()
        if len(touched) > 1:
            for k in touched:
                flag(k, 0.4, "'%s' runs across a pause" % text)
        if end - start > long_word and _flex_retake_voiced(vad, start, end) >= 0.6:
            for k in touched:
                flag(k, (end - start) / 2.0, "'%s' stretched over %.1fs" % (text, end - start))
    return sorted(((k, why[k]) for k in weight), key=lambda item: -weight[item[0]])


def _flex_retake_relisten(model, result, vad, pcm, rate, suspects, transcribe_args, total, pad):

    import wave
    islands = vad["islands"]



    budget = max(3, int(total / 30.0))
    chosen = [k for k, _ in suspects if islands[k]["end"] - islands[k]["start"] <= _RETAKE_MAX_STRETCH][:budget]
    if not chosen:
        return 0
    _flex_stage("polish", None, None, "Listening again where a restart may be hidden (%d)" % len(chosen))
    args = dict(transcribe_args or {})
    args["word_timestamps"] = True
    args["condition_on_previous_text"] = False
    prompt = args.get("initial_prompt") or ""
    reasons = dict(suspects)
    replaced = 0
    temp_path = os.path.join(tempfile.gettempdir(), "flex_retake_%d.wav" % os.getpid())
    lead = 0.5
    try:
        for k in sorted(chosen):
            isl = islands[k]
            lo = max(0.0, isl["lo"], isl["start"] - 0.2)
            hi = min(isl["hi"], isl["end"] + 0.2, total)
            chunk = pcm[int(lo * rate):int(hi * rate)]
            body = chunk.tobytes() if hasattr(chunk, "tobytes") else bytes(chunk)
            if sys.byteorder == "big" and not hasattr(chunk, "dtype"):
                import array
                swapped = array.array("h", chunk)
                swapped.byteswap()
                body = swapped.tobytes()
            with wave.open(temp_path, "wb") as target:
                target.setnchannels(1)
                target.setsampwidth(2)
                target.setframerate(rate)
                silence = b"\x00\x00" * int(lead * rate)
                target.writeframes(silence + body + silence)
            try:
                again = model.transcribe(temp_path, verbose=False, **args)
            except Exception as again_error:


                print("  %.1f-%.1fs: could not listen again (%s)." % (max(0.0, isl["start"] - pad), max(0.0, isl["end"] - pad), again_error))
                continue
            fresh = []
            for segment in again.get("segments") or []:
                if _flex_num(segment.get("avg_logprob"), 0.0) < -1.0 or _flex_num(segment.get("compression_ratio"), 0.0) > 2.4:
                    continue
                if _flex_num(segment.get("no_speech_prob"), 0.0) > 0.6 or _flex_is_prompt_echo(segment.get("text"), prompt):
                    continue
                placed = []
                for word in segment.get("words") or []:
                    start, end = _flex_num(word.get("start")), _flex_num(word.get("end"))
                    if start is None or end is None:
                        continue
                    start, end = start - lead + lo, end - lead + lo



                    if end <= lo or start >= hi:
                        continue
                    moved = dict(word)
                    moved["start"] = round(min(max(start, lo), hi - 0.05), 3)
                    moved["end"] = round(min(max(end, moved["start"] + 0.05), hi), 3)
                    placed.append(moved)
                text = "".join(str(w.get("word") or "") for w in placed).strip()
                if placed and not _flex_retake_is_stock(text):
                    fresh.append({"start": placed[0]["start"], "end": placed[-1]["end"], "text": " " + text,
                                  "words": placed, "avg_logprob": segment.get("avg_logprob"),
                                  "no_speech_prob": segment.get("no_speech_prob"),
                                  "compression_ratio": segment.get("compression_ratio"), "flex_relistened": True})
            old = [w for s, e, w in _flex_retake_words(result) if _flex_retake_home(vad, s, e) == k]
            heard = sum(len(s["words"]) for s in fresh)
            where = "%.1f-%.1fs" % (max(0.0, isl["start"] - pad), max(0.0, isl["end"] - pad))
            if heard < len(old) + 2:
                print("  %s (%s): no missed words (%d on its own, %d before)." % (where, reasons.get(k, ""), heard, len(old)))
                continue
            gone = set(id(w) for w in old)
            kept = []
            for segment in result.get("segments") or []:
                words = segment.get("words")
                if words:
                    left = [w for w in words if id(w) not in gone]
                    for w in left:

                        ws, we = _flex_num(w.get("start")), _flex_num(w.get("end"))
                        if ws is not None and we is not None and ws < isl["lo"] < we:
                            w["end"] = round(max(ws + 0.05, isl["lo"]), 3)
                    if not left:
                        continue
                    if len(left) != len(words):
                        segment = dict(segment)
                        segment["words"] = left
                        segment["start"], segment["end"] = left[0]["start"], left[-1]["end"]
                        segment["text"] = " " + "".join(str(w.get("word") or "") for w in left).strip()
                kept.append(segment)
            result["segments"] = sorted(kept + fresh, key=lambda s: _flex_num(s.get("start"), 0.0))
            replaced += 1
            print("  %s (%s): %d word(s) heard on their own, %d before." % (where, reasons.get(k, ""), heard, len(old)))
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
    return replaced


def _flex_retake_drop_stock(vad, result):


    islands = vad["islands"]
    speech_start, speech_end = islands[0]["start"], islands[-1]["end"]
    dropped, kept = [], []
    for segment in result.get("segments") or []:
        words = [w for w in (segment.get("words") or [])
                 if _flex_num(w.get("start")) is not None and _flex_num(w.get("end")) is not None]
        if words:
            a, b = _flex_num(words[0]["start"]), _flex_num(words[-1]["end"])
        else:
            a, b = _flex_num(segment.get("start"), 0.0), _flex_num(segment.get("end"), 0.0)
        text = str(segment.get("text") or "").strip()
        if _flex_retake_is_stock(text):
            span = max(0.05, b - a)
            share = _flex_retake_voiced(vad, a, b) / span
            if share < 0.35 or a >= speech_end - 0.05 or b <= speech_start + 0.05:
                dropped.append(text)
                continue
        elif len(words) > 1:

            cut = 0
            for n in range(1, min(6, len(words) - 1) + 1):
                tail = words[-n:]
                a2, b2 = _flex_num(tail[0]["start"]), _flex_num(tail[-1]["end"])
                if _flex_retake_is_stock("".join(str(w.get("word") or "") for w in tail)) and \
                        _flex_retake_voiced(vad, a2, b2) / max(0.05, b2 - a2) < 0.2:
                    cut = n
            if cut:
                dropped.append("".join(str(w.get("word") or "") for w in words[-cut:]).strip())
                segment = dict(segment)
                segment["words"] = words[:-cut]
                segment["end"] = segment["words"][-1]["end"]
                segment["text"] = " " + "".join(str(w.get("word") or "") for w in segment["words"]).strip()
        kept.append(segment)
    result["segments"] = kept
    return dropped


def _flex_retake_mark(vad, result):


    islands = vad["islands"]
    pieces = []
    for segment in result.get("segments") or []:
        words = [w for w in (segment.get("words") or [])
                 if _flex_num(w.get("start")) is not None and _flex_num(w.get("end")) is not None]
        if not words:
            piece = dict(segment)
            a, b = _flex_num(segment.get("start"), 0.0), _flex_num(segment.get("end"), 0.0)
            piece["flex_island"] = _flex_retake_home(vad, a, max(a, b))
            pieces.append(piece)
            continue
        groups = []
        for word in words:
            home = _flex_retake_home(vad, _flex_num(word["start"]), _flex_num(word["end"]))
            if groups and groups[-1][0] == home:
                groups[-1][1].append(word)
            else:
                groups.append((home, [word]))
        for home, group in groups:
            piece = dict(segment)
            if len(groups) > 1:
                piece["words"] = group
                piece["start"], piece["end"] = group[0]["start"], group[-1]["end"]
                piece["text"] = " " + "".join(str(w.get("word") or "") for w in group).strip()
            piece["flex_island"] = home
            pieces.append(piece)
    pieces.sort(key=lambda s: _flex_num(s.get("start"), 0.0))
    previous = None
    for number, piece in enumerate(pieces):
        piece["id"] = number
        home = piece.get("flex_island")
        if previous is not None and home is not None and home != previous:
            piece["flex_split"] = True
            piece["flex_pause_before"] = round(islands[home]["pause"] or 0.0, 3)
        if home is not None:
            previous = home
    result["segments"] = pieces
    result["text"] = " ".join(str(s.get("text") or "").strip() for s in pieces).strip()
    return result


def _flex_retake_refine(model, result, wav_path, transcribe_args, pad=0.0):


    import copy
    try:
        measured = _flex_retake_levels(wav_path)
        if measured is None:
            print("Retakes: the audio could not be measured; the transcript is used as it is.")
            return result
        pcm, rate, levels = measured
        vad = _flex_retake_islands(levels)
        if vad is None:
            print("Retakes: voice and background are too close in level to measure pauses; "
                  "the transcript is used as it is.")
            return result
        refined = copy.deepcopy(result)
        total = len(pcm) / float(rate)
        print("Retakes: %d stretch(es) of speech between pauses of %.1fs or more (voice above %.0f dB)."
              % (len(vad["islands"]), _RETAKE_PAUSE, vad["threshold"]))
        relistened = 0
        if model is not None:
            suspects = _flex_retake_suspects(vad, refined)
            if suspects:
                print("Retakes: %d stretch(es) may hide a restart; listening to them on their own..." % len(suspects))
                relistened = _flex_retake_relisten(model, refined, vad, pcm, rate, suspects, transcribe_args, total, pad)
        dropped = _flex_retake_drop_stock(vad, refined)
        for text in dropped:
            print("Retakes: dropped '%s' (no voice under it)." % text)
        refined = _flex_retake_mark(vad, refined)
        refined["flex_retakes"] = {"stretches": len(vad["islands"]), "relistened": relistened,
                                   "dropped": dropped, "voice_db": round(vad["threshold"], 1)}
        return refined
    except Exception as refine_error:
        print("Retakes: could not refine the transcript (%s); it is used as it is." % refine_error)
        return result


def main():
    parser = argparse.ArgumentParser(description="Whisper Transcription Script")
    parser.add_argument("--emit-json", default=None,
                        help="Also write the raw transcript (segments + words) to this path. "
                             "The Silence/Retakes tools consume the same shape Whisper's CLI "
                             "emits, so they can share this engine instead of running their own.")
    parser.add_argument("--engine", default="local", choices=["local", "cloud"],
                        help="cloud = Flex AI Transcribe (default); local = Whisper on this machine")
    parser.add_argument("--input", required=True, help="Input media file path")
    parser.add_argument("--output", required=True, help="Output SRT file path")
    parser.add_argument("--model", default="turbo", help="Whisper model: turbo, medium or large")
    parser.add_argument("--max-words", type=int, default=0, help="Maximum words per line")
    parser.add_argument("--language", default=None, help="Transcription language code")
    parser.add_argument("--initial-prompt", default=None, help="Initial prompt to guide Whisper")
    parser.add_argument("--translate-to", default=None,
                        help="Translate the captions into this language code (Flex AI)")
    parser.add_argument("--roman", action="store_true",
                        help="Transliterate Devanagari output to Roman/Hinglish script")
    parser.add_argument("--fill-gaps", action="store_true", help="Fill small gaps between subtitles to make them continuous")
    parser.add_argument("--script", default=None,
                        help="A text file with the script the speaker read: the captions take its wording where it matches")
    parser.add_argument("--no-cache", action="store_true",
                        help="Transcribe again even when this exact audio was transcribed before with the same settings")
    parser.add_argument("--start-time", "--start", type=float, default=None, help="Start time in seconds for selective transcription")
    parser.add_argument("--end-time", "--end", type=float, default=None, help="End time in seconds for selective transcription")
    parser.add_argument("--retakes", action="store_true",
                        help="Retakes task only: listen again where a restart may have been merged away, "
                             "mark measured pauses (flex_split) and drop stock phrases on silence")
    args = parser.parse_args()
    _flex_lower_priority()

    input_path = args.input
    output_path = args.output
    model_name = args.model
    max_words = args.max_words
    language = args.language
    initial_prompt = args.initial_prompt
    fill_gaps = args.fill_gaps
    start_time = args.start_time
    end_time = args.end_time

    if not os.path.exists(input_path):
        print(f"Error: Input file does not exist: {input_path}")
        sys.exit(1)

    print(f"Processing input file: {input_path}")
    temp_audio_path = None


    ext = os.path.splitext(input_path)[1].lower()
    is_video = ext in ['.mp4', '.mov', '.avi', '.mkv', '.m4v', '.webm']


    temp_dir = tempfile.gettempdir()
    temp_audio_path = os.path.join(temp_dir, f"normalized_audio_{os.getpid()}.wav")

    total_pad_start = 0.0
    real_preroll_start = 0.0

    if args.engine == "cloud":


        try:
            sys.stdout.reconfigure(line_buffering=True)
        except Exception:
            pass








        temp_audio_path = os.path.join(temp_dir, f"flex_cloud_audio_{os.getpid()}.m4a")
        total_pad_start = 0.0





        span = None
        if start_time is not None and end_time is not None:
            span = max(0.0, end_time - start_time)




        bitrate = 64
        if span and span > 0:
            fits = int((85.0 * 8 * 1024 * 1024) / span / 1000.0)
            bitrate = max(32, min(64, fits))



        os.environ["FLEX_UPLOAD_KBPS"] = str(bitrate)
        print(f"Extracting audio for upload ({bitrate} kbps mono)...")
        try:
            import subprocess
            cmd = ["ffmpeg", "-y", "-i", input_path]
            if start_time is not None and end_time is not None:

                cmd += ["-ss", f"{start_time:.3f}", "-to", f"{end_time:.3f}"]
            cmd += ["-vn", "-ac", "1", "-ar", "16000",
                    "-c:a", "aac", "-b:a", f"{bitrate}k", temp_audio_path]
            subprocess.run(cmd, check=True, capture_output=True)
            transcription_path = temp_audio_path
            print(f"Audio ready: {temp_audio_path}")
        except Exception as extract_error:


            print(f"ffmpeg unavailable ({extract_error}); trying moviepy...")
            try:
                from moviepy import VideoFileClip, AudioFileClip
                temp_audio_path = os.path.join(temp_dir, f"flex_cloud_audio_{os.getpid()}.wav")
                if is_video:
                    clip = VideoFileClip(input_path)
                    audio_clip = clip.audio
                else:
                    audio_clip = AudioFileClip(input_path)
                if start_time is not None and end_time is not None:
                    trim = getattr(audio_clip, "subclipped", None) or audio_clip.subclip
                    audio_clip = trim(start_time, end_time)
                audio_clip.write_audiofile(temp_audio_path, fps=16000, nbytes=2,
                                           codec="pcm_s16le", logger=None)
                transcription_path = temp_audio_path
                print(f"Audio ready via moviepy: {temp_audio_path}")
            except Exception as moviepy_error:



                if not is_video and start_time is None and end_time is None:
                    print(f"moviepy unavailable ({moviepy_error}); uploading the audio as-is.")
                    transcription_path = input_path
                    temp_audio_path = None
                else:
                    print(f"Error: could not extract audio for upload: {moviepy_error}")
                    print("The cloud engine needs ffmpeg to pull audio out of video. Press "
                          "Install / Fix Dependencies in the Auto Captions tab, or switch "
                          "the engine back to Local.")
                    sys.exit(1)
    else:
        print("Normalizing audio format (16kHz, mono)...")
        try:
            import subprocess

            if start_time is not None and end_time is not None:

                actual_crop_start = max(0.0, start_time - 1.0)
                pad_start = start_time - actual_crop_start
                silence_delay_ms = int((1.0 - pad_start) * 1000)
                total_pad_start = 1.0
                real_preroll_start = pad_start

                cmd = [
                    "ffmpeg", "-y",
                    "-i", input_path,
                    "-ss", f"{actual_crop_start:.3f}",
                    "-to", f"{end_time + 1.0:.3f}",
                    "-af", f"aformat=channel_layouts=mono,adelay={silence_delay_ms},apad=pad_dur=1",
                    "-ar", "16000",
                    "-c:a", "pcm_s16le",
                    temp_audio_path
                ]
            else:

                total_pad_start = 1.0
                cmd = [
                    "ffmpeg", "-y",
                    "-i", input_path,
                    "-af", "aformat=channel_layouts=mono,adelay=1000,apad=pad_dur=1",
                    "-ar", "16000",
                    "-c:a", "pcm_s16le",
                    temp_audio_path
                ]

            print(f"Running ffmpeg command: {' '.join(cmd)}")
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            transcription_path = temp_audio_path
            print(f"Audio normalized successfully to: {temp_audio_path}")
        except Exception as ffmpeg_e:
            print(f"FFmpeg normalization failed or not found: {str(ffmpeg_e)}")

            if is_video:
                print("Falling back to moviepy for video audio extraction...")
                try:
                    from moviepy import VideoFileClip
                    video = VideoFileClip(input_path)


                    if start_time is not None and end_time is not None:
                        actual_crop_start = max(0.0, start_time - 1.0)
                        pad_start = start_time - actual_crop_start
                        total_pad_start = pad_start
                        real_preroll_start = pad_start
                        print(f"Applying padded subclip from {actual_crop_start}s to {end_time + 1.0}s...")
                        if hasattr(video, "subclipped"):
                            video = video.subclipped(actual_crop_start, min(end_time + 1.0, video.duration))
                        else:
                            video = video.subclip(actual_crop_start, min(end_time + 1.0, video.duration))
                    else:
                        total_pad_start = 0.0

                    video.audio.write_audiofile(
                        temp_audio_path,
                        fps=16000,
                        nbytes=2,
                        codec='pcm_s16le',
                        ffmpeg_params=["-ac", "1"],
                        logger=None
                    )
                    transcription_path = temp_audio_path
                    print(f"Audio extracted successfully via moviepy to: {temp_audio_path}")
                except Exception as moviepy_e:
                    print(f"Error extracting audio via moviepy: {str(moviepy_e)}")
                    sys.exit(1)
            else:
                if start_time is not None or end_time is not None:
                    print("Warning: Selective range cropping requested, but ffmpeg is missing and input is audio.")
                    print("Using original audio file directly without cropping (all captions will be transcribed).")
                transcription_path = input_path
                temp_audio_path = None
                total_pad_start = 0.0










    if model_name == "flex-ai-high":
        cloud_tier = "high"
    else:
        cloud_tier = "standard"





    gemini_file = args.engine == "cloud" and (model_name or "").strip().lower() == "gemini-file"
    if model_name in ("flex-ai", "flex-ai-high"):
        model_name = _flex_fallback_model()
    elif (model_name or "").strip().lower() in ("gemini-file", "gemini-live"):
        gemini_label = "Gemini 3.5 Transcribe"
        model_name = _flex_fallback_model()
        if args.engine != "cloud":
            print("%s runs in Auto Captions only; this run uses Whisper %s on this computer."
                  % (gemini_label, _FLEX_MODEL_LABELS.get(model_name, model_name)))
    if model_name not in _FLEX_ENGINES:
        model_name = _flex_resolve_model(model_name)


    cache_key = None
    if not getattr(args, "no_cache", False) and transcription_path and os.path.exists(transcription_path):
        try:
            vocab = ""
            try:
                vocab = json.dumps(_flex_vocabulary(), sort_keys=True, ensure_ascii=True)
            except Exception:
                vocab = ""
            cache_key = _flex_cache_key(transcription_path, {
                "v": _FLEX_CACHE_VERSION,
                "engine": ("gemini-file" if gemini_file else ("cloud-" + cloud_tier if args.engine == "cloud" else model_name)),
                "language": (language or "").strip().lower(), "prompt": initial_prompt or "",
                "roman": bool(getattr(args, "roman", False)), "retakes": bool(getattr(args, "retakes", False)),
                "translate": getattr(args, "translate_to", None) or "", "vocabulary": vocab,
                "pad": total_pad_start, "preroll": real_preroll_start})
        except Exception as key_error:
            print("NOTE: transcript cache unavailable (%s)." % key_error)
            cache_key = None
        cached = _flex_cache_get(cache_key)
        if cached is not None:
            print("Reused the transcript from before - no credits used. (Tick Transcribe again for a fresh one.)")
            _flex_stage("polish", None, None, "Reused the transcript from before - no credits used")
            _flex_finish(args, cached["result"], output_path, max_words, fill_gaps, start_time, end_time,
                         total_pad_start, real_preroll_start, temp_audio_path)
            return

    model = None
    if gemini_file:
        print("Using Gemini 3.5 Transcribe through Flex AI: measured word timings and speakers.")
        model = _CloudModel(diarization=True, tier=cloud_tier, gemini=True)
    elif args.engine == "cloud":
        print("Using Flex AI Transcribe (cloud engine, %s tier)." % cloud_tier)
        model = _CloudModel(diarization=True, tier=cloud_tier)
    elif model_name in _FLEX_ENGINES:
        print("Using %s (it runs in its own Python environment in %s)." % (_FLEX_ENGINES[model_name]["label"], _flex_models_dir()))
        model = _EngineModel(model_name)
    else:
        print(f"Loading Whisper model '{model_name}'...")

    try:
        if model is None:
            import whisper
            model = _flex_load_model(whisper, model_name)
    except Exception as e:




        print(f"Error loading Whisper model: {str(e)}")
        print(f"  Interpreter: {sys.executable}")
        print(f"  Python version: {sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}")
        if sys.version_info < (3, 10):
            print(
                "  This Python is older than 3.10. Whisper's dependencies (numba, torch) "
                "target 3.10 and newer, so this will keep failing on one import after "
                "another. Install Python 3.11 or 3.12, then press Install / Fix "
                "Dependencies in the Auto Captions tab so Flex targets it."
            )
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
            except:
                pass
        sys.exit(1)

    cache_model = model
    print("Transcribing audio...")
    try:




        transcribe_args = {'word_timestamps': True}
        if language and language.strip() and language.lower() != "auto":
            transcribe_args['language'] = language
        if initial_prompt and initial_prompt.strip():
            if _flex_stock() and has_devanagari(initial_prompt):

                print("Stock models: the panel's built-in Hindi prompt is not used.")
            else:
                transcribe_args['initial_prompt'] = initial_prompt
        if not isinstance(model, (_CloudModel, _EngineModel)):
            transcribe_args.update(_flex_decode_args(model_name))
            if 'language' not in transcribe_args:
                _flex_stage("detect", None, None, "Listening to the opening to pick the language")
                detected = _flex_detect_language(model, transcription_path)
                if detected:
                    transcribe_args['language'] = detected
            if model_name == "hinglish" and transcribe_args.get("language") in (None, "hi", "ur"):
                transcribe_args["language"] = "hi"
            transcribe_args = _flex_hinglish_policy(transcribe_args, getattr(args, 'roman', False) or model_name == "hinglish")
            transcribe_args = _flex_apply_vocabulary(transcribe_args)
        elif isinstance(model, _EngineModel):
            transcribe_args = _flex_apply_vocabulary(transcribe_args)

        try:
            if not isinstance(model, _CloudModel):
                _FLEX_PROGRESS["main"] = True
                if not isinstance(model, _EngineModel):
                    _flex_stage("transcribe", 0, None, "Listening to your audio")
            result = _flex_run_transcribe(model, transcription_path, transcribe_args)
        except CloudCancelled:
            print("Cancelled.")
            if temp_audio_path and os.path.exists(temp_audio_path):
                try:
                    os.remove(temp_audio_path)
                except Exception:
                    pass
            sys.exit(130)
        except CloudError as cloud_error:



            if gemini_file:
                kind, message = _cloud_failure(cloud_error)
                print("ERROR: %s" % message)
                _cloud_offer(kind)
                if temp_audio_path and os.path.exists(temp_audio_path):
                    try:
                        os.remove(temp_audio_path)
                    except Exception:
                        pass
                sys.exit(1)









            preflight = cloud_error.code in (
                "INVALID_LICENSE", "AUTHENTICATION_REQUIRED", "INSUFFICIENT_CREDITS",
                "NETWORK", "BAD_INIT", "BAD_GATEWAY_BODY", "AUDIO_NOT_UPLOADED",
                "404", "401", "402", "403")
            if not preflight:
                raise

            print("")
            print("Flex AI could not start: %s" % cloud_error)
            print("Falling back to the local Whisper engine for this run.")
            print("")
            try:
                import whisper
                model = _flex_load_model(whisper, model_name)
            except Exception as whisper_error:
                print("The local engine is not available either: %s" % whisper_error)
                print("  Interpreter: %s" % sys.executable)
                print("Press Install / Fix Dependencies in the Auto Captions tab, or add "
                      "credits to use Flex AI Transcribe.")
                sys.exit(1)
            transcribe_args.update(_flex_decode_args(model_name))
            _FLEX_PROGRESS["main"] = True
            result = _flex_run_transcribe(model, transcription_path, transcribe_args)

        _FLEX_PROGRESS["main"] = False
        if not isinstance(model, _CloudModel):
            _flex_stage("polish", None, None, "Checking for missed words and fixing timings")



        if isinstance(model, _CloudModel) and result.get("engine") == GEMINI_ENGINE:



            cut = _flex_cloud_cut(result, float(_audio_duration(transcription_path) or 0.0))
            if cut is not None:
                print("NOTE: Gemini's words stop at %.1fs; nothing was added after that." % cut)
        elif isinstance(model, _CloudModel):
            result = _flex_cloud_complete(model, result, transcription_path, transcribe_args, model_name)

        if not isinstance(model, (_CloudModel, _EngineModel)):
            result = _flex_local_complete(model, result, transcription_path, transcribe_args)
            result = _flex_drop_prompt_echo(result, transcribe_args)
            result = _flex_gap_rescue(model, result, transcription_path, transcribe_args)
            result = _flex_fix_opening(model, result, transcription_path, total_pad_start, real_preroll_start,
                                       start_time, end_time, transcribe_args)


        if getattr(args, "retakes", False) and not isinstance(model, _CloudModel):
            result = _flex_retake_refine(None if isinstance(model, _EngineModel) else model,
                                         result, transcription_path, transcribe_args, total_pad_start)

        if getattr(args, 'translate_to', None):
            result = _flex_apply_translation(args.translate_to, result, model, model_name,
                                             transcription_path, transcribe_args, total_pad_start,
                                             real_preroll_start, start_time, end_time,
                                             not isinstance(model, (_CloudModel, _EngineModel)))







        if getattr(args, 'roman', False):
            converted = 0
            for segment in result.get('segments', []):
                if has_devanagari(segment.get('text', '')):
                    segment['text'] = to_roman(segment['text']); converted += 1
                for word in segment.get('words', []) or []:
                    key = 'word' if 'word' in word else ('text' if 'text' in word else None)
                    if key and has_devanagari(word.get(key, '')):
                        word[key] = to_roman(word[key])
            if 'text' in result and has_devanagari(result['text']):
                result['text'] = to_roman(result['text'])
            print("Converted %d segment(s) to Roman script." % converted)
    except CloudCancelled:
        print("Cancelled.")
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
            except Exception:
                pass
        sys.exit(130)
    except Exception as e:
        print(f"Error during transcription: {str(e)}")
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
            except:
                pass
        sys.exit(1)


    if cache_key and model is cache_model:
        try:
            import copy as _copy
            _flex_cache_put(cache_key, _copy.deepcopy(result), total_pad_start, real_preroll_start)
        except Exception:
            pass
    _flex_finish(args, result, output_path, max_words, fill_gaps, start_time, end_time,
                 total_pad_start, real_preroll_start, temp_audio_path)




















import copy as _flex_copy
import difflib
import unicodedata

_FLEX_SCRIPT_MIN_SHARE = 0.3
_FLEX_SCRIPT_PAIR_MIN = 0.5
_FLEX_SCRIPT_PAIR_MIN_BIG = 0.72
_FLEX_SCRIPT_CONTEXT_MIN = 0.6
_FLEX_SCRIPT_MAX_GROUP = 3
_FLEX_SCRIPT_MAX_GROUP_SPECIAL = 6
_FLEX_SCRIPT_GAP_PER_WORD = 0.16
_FLEX_SCRIPT_MAX_INSERT = 3
_FLEX_SCRIPT_MAX_BLOCK = 6000

_FLEX_NUM_ONES = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
                  "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
_FLEX_NUM_TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
_FLEX_ORD_LAST = {"one": "first", "two": "second", "three": "third", "five": "fifth", "eight": "eighth",
                  "nine": "ninth", "twelve": "twelfth"}
_FLEX_CURRENCY = {"$": "dollars", "€": "euros", "£": "pounds", "₹": "rupees", "¥": "yen"}
_FLEX_ANTONYMS = [("before", "after"), ("show", "hide"), ("first", "last"), ("increase", "decrease"), ("import", "export"),
                  ("inside", "outside"), ("enable", "disable"), ("include", "exclude"), ("left", "right"), ("on", "off"),
                  ("always", "never"), ("more", "less"), ("up", "down"), ("in", "out"), ("open", "close"), ("add", "remove"),
                  ("start", "stop"), ("start", "end"), ("yes", "no"), ("light", "dark"), ("lighter", "darker"),
                  ("top", "bottom"), ("high", "low"), ("higher", "lower"), ("min", "max"), ("minimum", "maximum"),
                  ("true", "false"), ("all", "none"), ("with", "without"), ("push", "pull"), ("can", "cant"),
                  ("will", "wont"), ("do", "dont"), ("does", "doesnt"), ("is", "isnt"), ("should", "shouldnt"),
                  ("big", "small"), ("bigger", "smaller"), ("fast", "slow"), ("faster", "slower"), ("in", "on"),
                  ("this", "that"), ("these", "those"), ("here", "there"), ("now", "then"), ("next", "previous"),
                  ("forward", "backward"), ("front", "back"), ("black", "white"), ("hot", "cold"), ("good", "bad"),
                  ("best", "worst"), ("better", "worse"), ("win", "lose"), ("buy", "sell"), ("new", "old")]
_FLEX_ANTONYM_SET = set()
for _a, _b in _FLEX_ANTONYMS:
    _FLEX_ANTONYM_SET.add((_a, _b)); _FLEX_ANTONYM_SET.add((_b, _a))
_FLEX_NEG_PREFIX = ("un", "dis", "in", "im", "ir", "il", "non", "de", "anti")
_FLEX_NUM_VALUE = {}
_FLEX_CONTRACTIONS = {"im": "iam", "ive": "ihave", "ill": "iwill", "id": "iwould", "youre": "youare", "youve": "youhave",
                      "youll": "youwill", "youd": "youwould", "were": "weare", "weve": "wehave", "well": "wewill",
                      "wed": "wewould", "theyre": "theyare", "theyve": "theyhave", "theyll": "theywill", "theyd": "theywould",
                      "hes": "heis", "hell": "hewill", "shes": "sheis", "shell": "shewill", "its": "itis", "itll": "itwill",
                      "thats": "thatis", "thatll": "thatwill", "theres": "thereis", "whats": "whatis", "whos": "whois",
                      "lets": "letus", "dont": "donot", "doesnt": "doesnot", "didnt": "didnot", "cant": "cannot",
                      "wont": "willnot", "isnt": "isnot", "arent": "arenot", "wasnt": "wasnot", "werent": "werenot",
                      "havent": "havenot", "hasnt": "hasnot", "couldnt": "couldnot", "shouldnt": "shouldnot",
                      "wouldnt": "wouldnot", "gonna": "goingto", "wanna": "wantto", "gotta": "gotto"}


def _flex_num_parts(n, use_and=False):

    if n < 20:
        return [_FLEX_NUM_ONES[n]]
    if n < 100:
        return [_FLEX_NUM_TENS[n // 10]] + ([] if n % 10 == 0 else [_FLEX_NUM_ONES[n % 10]])
    if n < 1000:
        return [_FLEX_NUM_ONES[n // 100], "hundred"] + ([] if n % 100 == 0 else (["and"] if use_and else []) + _flex_num_parts(n % 100))
    if n < 1000000:
        rest = n % 1000
        tail = []
        if rest:
            tail = (["and"] if (use_and and rest < 100) else []) + _flex_num_parts(rest, use_and)
        return _flex_num_parts(n // 1000, use_and) + ["thousand"] + tail
    return [str(n)]


def _flex_num_words(n, use_and=False):
    return "".join(_flex_num_parts(n, use_and))


def _flex_ordinal_words(n):
    parts = _flex_num_parts(n)
    last = parts[-1]
    if last in _FLEX_ORD_LAST:
        last = _FLEX_ORD_LAST[last]
    elif last.endswith("y"):
        last = last[:-1] + "ieth"
    else:
        last = last + "th"
    return "".join(parts[:-1] + [last])


def _flex_num_keys(digits):


    out = []
    try:
        n = int(digits)
    except (TypeError, ValueError):
        return out
    if len(digits) > 1 and digits.startswith("0"):
        return out
    if n >= 1000000:
        return out
    for v in (_flex_num_words(n), _flex_num_words(n, True)):
        if v not in out:
            out.append(v)
    if 1100 <= n <= 9999 and n % 100 != 0 and not (2000 <= n <= 2009):
        out.append(_flex_num_words(n // 100) + ("oh" + _FLEX_NUM_ONES[n % 100] if n % 100 < 10 else _flex_num_words(n % 100)))
    if 1000 <= n <= 9999 and n % 100 == 0 and n % 1000 != 0:
        out.append(_flex_num_words(n // 100) + "hundred")
    return out


def _flex_num_value(key):

    if not key:
        return None
    if key.isdigit():
        try:
            return int(key)
        except ValueError:
            return None
    m = re.match(r"^(\d+)(st|nd|rd|th)$", key)
    if m:
        return int(m.group(1))
    if not _FLEX_NUM_VALUE:
        for i in range(0, 10001):
            for k in _flex_num_keys(str(i)):
                _FLEX_NUM_VALUE.setdefault(k, i)
            _FLEX_NUM_VALUE.setdefault(_flex_ordinal_words(i), i)
    return _FLEX_NUM_VALUE.get(key)


_FLEX_CJK_RE = re.compile(u"[぀-ヿ㐀-䶿一-鿿豈-﫿฀-๿]")
_FLEX_SENT_END = re.compile(u"[.!?。！？]['\"”’)]*$")


def _flex_script_key(token):

    s = str(token or "")
    try:
        if has_devanagari(s):
            s = to_roman(s)
    except Exception:
        pass
    low = s.lower().strip()
    if low == "&":
        return ["and"]
    if low == "+":
        return ["plus"]
    extra = "percent" if "%" in low else ""
    money = ""
    for sym, word in _FLEX_CURRENCY.items():
        if sym in low:
            money = word
    norm = unicodedata.normalize("NFKD", low)
    base = "".join(ch for ch in norm if not unicodedata.combining(ch))
    key = "".join(ch for ch in base if ch.isalnum())
    if not key:
        return []
    keys = [key + extra + money]
    if ("'" in low or "\u2019" in low) and key in _FLEX_CONTRACTIONS:
        keys.append(_FLEX_CONTRACTIONS[key])
    m = re.match(r"^(\d+)(st|nd|rd|th)$", key)
    if m:
        try:
            keys.append(_flex_ordinal_words(int(m.group(1))))
        except Exception:
            pass
    dec = re.match(r"^[^\d]*(\d+)\.(\d{1,2})[^\d]*$", low)
    if dec:
        for k in _flex_num_keys(dec.group(1)):
            keys.append(k + "point" + "".join(_FLEX_NUM_ONES[int(c)] for c in dec.group(2)) + extra + money)
    elif key.isdigit():
        for k in _flex_num_keys(key):
            keys.append(k + extra + money)
    return keys


def _flex_sound_key(key):

    s = key.lower()
    for a, b in (("ph", "f"), ("ck", "k"), ("qu", "kw"), ("q", "k"), ("x", "ks"), ("z", "s"), ("wh", "w"),
                 ("gh", "g"), ("kn", "n"), ("dg", "j"), ("tch", "ch"), ("ee", "i"), ("ea", "i"), ("oo", "u"),
                 ("ou", "u"), ("ie", "i"), ("ey", "i"), ("y", "i"), ("c", "k")):
        s = s.replace(a, b)
    if not s:
        return s
    out = s[0]
    for ch in s[1:]:
        if ch in "aeiou":
            continue
        if ch != out[-1]:
            out += ch
    return out


_FLEX_SIM_CACHE = {}


def _flex_script_sim(a, b):

    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    hit = _FLEX_SIM_CACHE.get((a, b))
    if hit is not None:
        return hit
    if len(_FLEX_SIM_CACHE) > 200000:
        _FLEX_SIM_CACHE.clear()
    v = _flex_script_sim_raw(a, b)
    _FLEX_SIM_CACHE[(a, b)] = v
    return v


def _flex_script_sim_raw(a, b):
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()
    if min(len(a), len(b)) <= 2:
        return sm * 0.8
    sa, sb = _flex_sound_key(a), _flex_sound_key(b)
    snd = difflib.SequenceMatcher(None, sa, sb, autojunk=False).ratio() if sa and sb else 0.0
    if sa == sb and len(sa) >= 2:
        snd = 0.95
    return max(sm, snd * 0.92)


_FLEX_UNITS = ("percent", "dollars", "dollar", "euros", "euro", "pounds", "pound", "rupees", "rupee", "yen", "fps",
               "px", "pixels", "ms", "seconds", "second", "sec", "s", "k", "p", "x", "mb", "gb", "kb", "hz", "khz", "db",
               "mm", "cm", "m", "km", "kg", "g")


def _flex_num_unit(key):

    if not key:
        return None
    m = re.match(r"^(\d+)([a-z]*)$", key)
    if m:
        unit = m.group(2)
        if unit in ("st", "nd", "rd", "th"):
            unit = ""
        return (int(m.group(1)), unit)
    v = _flex_num_value(key)
    if v is not None:
        return (v, "")
    for u in _FLEX_UNITS:
        if key.endswith(u) and len(key) > len(u):
            v = _flex_num_value(key[:-len(u)])
            if v is not None:
                return (v, u)
    return None


def _flex_unit_norm(u):
    u = u or ""
    for a, b in (("pixels", "px"), ("seconds", "s"), ("second", "s"), ("sec", "s"), ("dollars", "dollar"),
                 ("euros", "euro"), ("pounds", "pound"), ("rupees", "rupee")):
        if u == a:
            return b
    return u


def _flex_num_clash(a, b):

    na, nb = _flex_num_unit(a), _flex_num_unit(b)
    if na is None or nb is None:
        return False
    ua, ub = _flex_unit_norm(na[1]), _flex_unit_norm(nb[1])
    return na[0] != nb[0] and (ua == ub or not ua or not ub)


_FLEX_PRONOUN_CONTRACT = {"i": ("m", "d", "ll", "ve"), "you": ("re", "ll", "ve", "d"), "we": ("re", "ll", "ve", "d"),
                          "they": ("re", "ll", "ve", "d"), "he": ("s", "ll", "d"), "she": ("s", "ll", "d"),
                          "it": ("s", "ll", "d"), "that": ("s", "ll", "d"), "there": ("s", "re", "ll", "d"),
                          "what": ("s", "re", "ll", "d"), "who": ("s", "re", "ll", "d"), "let": ("s",)}


def _flex_script_denied(a, b):


    if a == b:
        return False
    if _flex_num_clash(a, b):
        return True
    for x, y in ((a, b), (b, a)):
        tails = _FLEX_PRONOUN_CONTRACT.get(x)
        if tails and y.startswith(x) and y[len(x):] in tails:
            return True
    va, vb = _flex_num_value(a), _flex_num_value(b)
    if va is not None and vb is not None and va != vb:
        return True
    if (va is None) != (vb is None):

        other = b if va is not None else a
        num = a if va is not None else b
        if not num.isdigit() and other.isalpha() and len(other) <= 6:
            return True
    if (a, b) in _FLEX_ANTONYM_SET:
        return True
    for p in _FLEX_NEG_PREFIX:
        if a == p + b or b == p + a:
            return True
    if a + "nt" == b or b + "nt" == a or a + "not" == b or b + "not" == a:
        return True
    return False


def _flex_group_variants(keys_list):

    combos = [""]
    for keys in keys_list:
        nxt = []
        for c in combos:
            for k in (keys or [""])[:4]:
                nxt.append(c + k)
        combos = nxt[:12]
    return combos


def _flex_group_sim(keys_a, keys_b):


    if len(keys_a) == 1 and len(keys_b) == 1 and _flex_script_denied(keys_a[0][0], keys_b[0][0]):
        return 0.0
    na = [x for x in (_flex_num_unit(v) for v in _flex_group_variants(keys_a)) if x is not None]
    nb = [x for x in (_flex_num_unit(v) for v in _flex_group_variants(keys_b)) if x is not None]
    if na and nb and not any(x[0] == y[0] for x in na for y in nb):
        return 0.0
    best = 0.0
    for a in _flex_group_variants(keys_a):
        for b in _flex_group_variants(keys_b):
            v = _flex_script_sim(a, b)
            if v > best:
                best = v
                if best >= 1.0:
                    return best
    return best


def _flex_script_clean(text):


    text = str(text or "").replace("﻿", "").replace("\x00", "").replace("�", "").replace(" ", " ")
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    kept = []
    for line in lines:
        s = line.strip()
        if (not s or s.upper() == "WEBVTT" or s.upper().startswith("NOTE ") or "-->" in s or re.match(r"^\d+$", s)
                or re.match(r"^#{1,6}\s", s)):
            kept.append("")
            continue
        s = s.replace("**", "").replace("__", "")
        s = re.sub(r"\[[^\]]*\]|\{[^}]*\}|<[^>]*>|\([^)]*\)|(?<!\w)\*[^*\n]{1,60}\*(?!\w)", " ", s)
        s = re.sub(r"^\s*([-*+>]|\d+[.)])\s+", "", s).strip()
        kept.append(s)


    time_re = r"\(?\d{1,2}(?::\d{2}){1,2}\)?"
    for k, s in enumerate(kept):
        if not s:
            continue
        words = s.split()
        if (re.match(r"^" + time_re + r"$", s)
                or re.match(r"^[A-Za-z][\w .'\-]{0,30}\s+" + time_re + r":?$", s)
                or re.match(r"(?i)^speaker\s*\d+\s*(\(.*\))?:?$", s)
                or (s.endswith(":") and len(words) <= 4)
                or re.match(r"(?i)^(sfx|music|b-?roll|on[- ]screen|text on screen|graphics?|gfx|cut to|transition|lower third|title card|visual|scene)\b[^:]{0,30}:", s)
                or (len(words) <= 4 and any(c.isupper() for c in s) and not any(c.islower() for c in s) and not _FLEX_SENT_END.search(s))):
            kept[k] = ""
    label_re = re.compile(r"^([A-Za-z][A-Za-z0-9 .'\-]{0,24}):\s+\S")
    nonempty = [s for s in kept if s]
    labelled = [s for s in nonempty if label_re.match(s)]
    strip_labels = len(labelled) >= 2 and len(labelled) >= 0.3 * max(1, len(nonempty))
    out = []
    for s in kept:
        if not s:
            continue
        m = label_re.match(s)
        if m and (strip_labels or m.group(1).upper() == m.group(1) or len(m.group(1).split()) <= 2):
            s = s[len(m.group(1)) + 1:].lstrip()
        s = re.sub(r"(?<!\S)" + time_re + r"(?!\S)", " ", s)
        out.append(s)
    return "\n".join(out)


def _flex_is_cjk(text):
    letters = [c for c in str(text or "") if c.isalpha()]
    return bool(letters) and sum(1 for c in letters if _FLEX_CJK_RE.match(c)) >= 0.3 * len(letters)


def _flex_script_tokens(text, cjk=False):


    toks = []
    for line in _flex_script_clean(text).split("\n"):
        before = len(toks)
        _flex_script_line_tokens(line, cjk, toks)
        if len(toks) > before:
            toks[-1]["end"] = True
    return toks


def _flex_script_line_tokens(line, cjk, toks):
    for raw in re.split(r"\s+", line):
        if not raw:
            continue
        parts = []
        for part in re.split(r"(?<=[—–])(?=\w)|(?<=\.\.\.)(?=\w)|(?<=…)(?=\w)", raw):
            if not part:
                continue
            if cjk and _FLEX_CJK_RE.search(part):
                buf = ""
                for ch in part:
                    if _FLEX_CJK_RE.match(ch):
                        if buf:
                            parts.append(buf)
                        buf = ch
                    else:
                        buf += ch
                if buf:
                    parts.append(buf)
            else:
                parts.append(part)
        for part in parts:
            keys = _flex_script_key(part)
            if not keys:
                if toks and (part in ("—", "–", "...", "…") or cjk):
                    toks[-1]["t"] += part
                continue
            toks.append({"t": part, "k": keys})


def _flex_script_words(result, cjk=False):

    out = []
    for si, seg in enumerate(result.get("segments", []) or []):
        for wi, w in enumerate(seg.get("words", []) or []):
            text = w.get("word", w.get("text", ""))
            try:
                a = float(w.get("start")); b = float(w.get("end"))
            except (TypeError, ValueError):
                continue
            text = str(text or "")
            if cjk and _FLEX_CJK_RE.search(text):
                lead = text[:len(text) - len(text.lstrip())]
                chars = []
                for ch in text.strip():
                    if _FLEX_CJK_RE.match(ch) or not chars:
                        chars.append(ch)
                    else:
                        chars[-1] += ch
                n = len(chars)
                for k, ch in enumerate(chars):
                    keys = _flex_script_key(ch)
                    if not keys:
                        continue
                    ca = a + (max(a, b) - a) * k / float(n)
                    cb = a + (max(a, b) - a) * (k + 1) / float(n)
                    out.append({"seg": si, "idx": wi, "w": w, "start": ca, "end": cb, "k": keys,
                                "text": (lead if k == 0 else "") + ch})
                continue
            keys = _flex_script_key(text)
            if not keys:
                continue
            out.append({"seg": si, "idx": wi, "w": w, "start": a, "end": max(a, b), "k": keys, "text": text})
    return out


def _flex_special(tok):

    t = tok["t"]
    return bool(re.search(r"\d", t) or "-" in t.strip("-") or any(c in t for c in _FLEX_CURRENCY))


def _flex_script_dp(S, T, context):


    n, m = len(S), len(T)
    INF = float("inf")
    cost = [[INF] * (m + 1) for _ in range(n + 1)]
    back = [[None] * (m + 1) for _ in range(n + 1)]
    cost[0][0] = 0.0
    small = n <= 3 and m <= 3
    memo = {}

    def is_num(t):
        return _flex_num_unit(t["k"][0]) is not None

    def num_cut(i0, a0, j0, b0):


        if not any(is_num(x) for x in S[i0:i0 + a0]):
            return False
        nxt = j0 + b0
        if nxt < m and (is_num(T[nxt]) or (T[nxt]["k"][0] == "and" and nxt + 1 < m and is_num(T[nxt + 1]))):
            return True
        if j0 > 0 and is_num(T[j0 - 1]) and is_num(T[j0]):
            return True
        return False

    def gsim(i0, a0, j0, b0):
        k = (i0, a0, j0, b0)
        if k not in memo:
            memo[k] = _flex_group_sim([x["k"] for x in S[i0:i0 + a0]], [x["k"] for x in T[j0:j0 + b0]])
        return memo[k]
    for i in range(n + 1):
        for j in range(m + 1):
            c = cost[i][j]
            if c == INF:
                continue
            if i < n and c + 1.0 < cost[i + 1][j]:
                cost[i + 1][j] = c + 1.0; back[i + 1][j] = ("s", i, j, 1, 0, 0.0)
            if j < m and c + 1.0 < cost[i][j + 1]:
                cost[i][j + 1] = c + 1.0; back[i][j + 1] = ("t", i, j, 0, 1, 0.0)
            for a in range(1, _FLEX_SCRIPT_MAX_GROUP + 1):
                if i + a > n:
                    break
                gt = _FLEX_SCRIPT_MAX_GROUP_SPECIAL if (a == 1 and _flex_special(S[i])) else _FLEX_SCRIPT_MAX_GROUP
                for b in range(1, gt + 1):
                    if j + b > m:
                        break
                    if a > 1 and b > 1:
                        continue
                    sim = gsim(i, a, j, b)


                    if b > 1 and sim < max(gsim(i, a, j, b - 1), gsim(i, a, j + 1, b - 1)) + 0.02:
                        continue
                    if a > 1 and sim < max(gsim(i, a - 1, j, b), gsim(i + 1, a - 1, j, b)) + 0.02:
                        continue
                    if context and n == 1 and m == 1:
                        need = _FLEX_SCRIPT_CONTEXT_MIN
                    else:
                        need = _FLEX_SCRIPT_PAIR_MIN if small else _FLEX_SCRIPT_PAIR_MIN_BIG
                    if a == 1 and b == 1:
                        ka, kb = S[i]["k"][0], T[j]["k"][0]
                        if min(len(ka), len(kb)) <= 4 and not (len(ka) >= 2 and _flex_sound_key(ka) == _flex_sound_key(kb)):
                            need = max(need, 0.75)
                    if (a > 1 or b > 1) and sim < 0.8:
                        continue
                    if sim < need:
                        continue
                    if num_cut(i, a, j, b):
                        continue
                    nc = c + (a + b) * (1.0 - sim) + 0.05 * (a + b - 2)
                    if nc < cost[i + a][j + b]:
                        cost[i + a][j + b] = nc; back[i + a][j + b] = ("pair", i, j, a, b, sim)
    ops = []
    i, j = n, m
    while i > 0 or j > 0:
        bk = back[i][j]
        if bk is None:
            break
        kind, pi, pj, a, b, sim = bk
        if kind == "pair":
            ops.append(("pair", list(range(pi, pi + a)), list(range(pj, pj + b)), sim))
        elif kind == "s":
            ops.append(("s", pi))
        else:
            ops.append(("t", pj))
        i, j = pi, pj
    ops.reverse()
    return ops


def _flex_strong_runs(exact_t, T):


    strong, run = [], []
    for x in sorted(exact_t) + [None]:
        if run and (x is None or x != run[-1] + 1):
            longest = max(len(T[y]["k"][0]) for y in run)
            if len(run) >= 3 or (len(run) == 2 and longest >= 4) or (len(run) == 1 and longest >= 5):
                strong.extend(run)
            run = []
        if x is not None:
            run.append(x)
    return strong


def _flex_script_align(S, T, sm_ops):



    pairs, unheard = [], {}
    for tag, i1, i2, j1, j2 in sm_ops:
        if tag == "equal":
            for d in range(i2 - i1):
                pairs.append(([i1 + d], [j1 + d], 1.0, True))
            continue
        if tag == "delete":
            unheard.setdefault(j1, []).extend(range(i1, i2))
            continue
        if tag == "insert":
            continue
        if (i2 - i1) * (j2 - j1) > _FLEX_SCRIPT_MAX_BLOCK:
            continue
        context = (i1 > 0 and j1 > 0) and (i2 < len(S) and j2 < len(T))
        ops = _flex_script_dp(S[i1:i2], T[j1:j2], context)


        s_pend, t_pend = [], []
        for op in ops + [("end",)]:
            if op[0] in ("pair", "end"):
                if s_pend and not t_pend:
                    pos = (j1 + op[2][0]) if op[0] == "pair" else j2
                    unheard.setdefault(pos, []).extend(s_pend)
                s_pend, t_pend = [], []
                if op[0] == "pair":
                    pairs.append(([i1 + x for x in op[1]], [j1 + x for x in op[2]], op[3], False))
            elif op[0] == "s":
                s_pend.append(i1 + op[1])
            else:
                t_pend.append(j1 + op[1])
    for k in unheard:
        unheard[k] = sorted(set(unheard[k]))
    pairs.sort(key=lambda p: p[1][0])
    return pairs, unheard


def _flex_script_text(token, lead, roman):

    t = token
    if roman:
        try:
            if has_devanagari(t):
                t = to_roman(t)
        except Exception:
            pass
    return lead + t


def _flex_lead(text):
    text = str(text or "")
    return text[:len(text) - len(text.lstrip())]




def _flex_ends(tok):

    return bool(tok.get("end")) or bool(_FLEX_SENT_END.search(tok["t"]))


def _flex_script_apply(result, script_text, roman=False):


    report = {"applied": False, "heard": 0, "script": 0, "matched": 0, "fixed": 0, "added": 0,
              "kept": 0, "skipped": 0, "share": 0.0, "reason": ""}
    work = _flex_copy.deepcopy(result)
    cjk = _flex_is_cjk(script_text)
    S = _flex_script_tokens(script_text, cjk)
    T = _flex_script_words(work, cjk)
    report["script"], report["heard"] = len(S), len(T)
    if len(S) < 3:
        report["reason"] = "the script has fewer than 3 words"
        return report
    if not T:
        report["reason"] = "the transcript has no timed words"
        return report
    sm_ops = difflib.SequenceMatcher(None, [s["k"][0] for s in S], [t["k"][0] for t in T], autojunk=False).get_opcodes()
    exact_t = []
    for tag, i1, i2, j1, j2 in sm_ops:
        if tag == "equal":
            exact_t.extend(range(j1, j2))
    strong = _flex_strong_runs(exact_t, T)
    share = len(strong) / float(len(T))
    pairs = unheard = None
    script_roman = not any(has_devanagari(s["t"]) for s in S)
    heard_dev = sum(1 for t in T if has_devanagari(t["text"])) >= len(T) / 2.0
    if share < _FLEX_SCRIPT_MIN_SHARE and script_roman and heard_dev:


        pairs, unheard = _flex_script_align(S, T, sm_ops)
        close = set()
        for p in pairs:
            if p[3] or p[2] >= _FLEX_SCRIPT_PAIR_MIN_BIG:
                close.update(p[1])
        strong = _flex_strong_runs(sorted(close), T)
        share = len(strong) / float(len(T))
    report["share"] = round(share, 3)
    if share < _FLEX_SCRIPT_MIN_SHARE:
        report["reason"] = "only %d%% of what was said matches the script" % int(round(share * 100))
        return report
    span_a, span_b = min(strong), max(strong)
    if pairs is None:
        pairs, unheard = _flex_script_align(S, T, sm_ops)


    import bisect as _bisect
    strong_sorted = sorted(strong)

    def near_strong(i0, i1):
        k = _bisect.bisect_left(strong_sorted, i0)
        best = 10 ** 9
        if k < len(strong_sorted):
            best = min(best, abs(strong_sorted[k] - i1), abs(strong_sorted[k] - i0))
        if k > 0:
            best = min(best, abs(i0 - strong_sorted[k - 1]))
        return best <= 6
    pairs = [p for p in pairs if p[3] or near_strong(p[1][0], p[1][-1])]

    segs_all = work.get("segments", []) or []
    untimed_at = set()
    pos_of = [(t["seg"], t["idx"]) for t in T]
    for k in range(1, len(T)):
        a_si, a_wi = pos_of[k - 1]
        b_si, b_wi = pos_of[k]
        for si in range(a_si, b_si + 1):
            ws = segs_all[si].get("words", []) or []
            lo = a_wi + 1 if si == a_si else 0
            hi = b_wi if si == b_si else len(ws)
            for wi in range(lo, hi):
                w = ws[wi]
                if not (isinstance(w.get("start"), (int, float)) and isinstance(w.get("end"), (int, float))):
                    untimed_at.add(k)

    segs = work.get("segments", []) or []
    lead_space = sum(1 for t in T if t["text"].startswith(" ")) >= len(T) / 2.0
    romanize_kept = (not roman) and script_roman and heard_dev

    blind = []
    for seg in segs:
        has_timed = any(isinstance(w.get("start"), (int, float)) for w in (seg.get("words") or []))
        if str(seg.get("text", "")).strip() and not has_timed:
            try:
                blind.append((float(seg.get("start")), float(seg.get("end"))))
            except (TypeError, ValueError):
                pass

    def kept_text(text):
        if romanize_kept:
            try:
                if has_devanagari(text):
                    return _flex_lead(text) + to_roman(text.strip())
            except Exception:
                pass
        return text

    def put_unheard(pos, sidx_list):
        if not sidx_list or not (span_a < pos <= span_b):
            return
        prev, nxt = T[pos - 1], T[pos]
        n = len(sidx_list)
        toks = [S[s]["t"] for s in sidx_list]
        before_end = sidx_list[0] == 0 or _flex_ends(S[sidx_list[0] - 1])
        whole_sentence = before_end and _flex_ends(S[sidx_list[-1]])
        crosses = any(_flex_ends(S[s]) for s in sidx_list[:-1])
        gap = nxt["start"] - prev["end"]
        if n > _FLEX_SCRIPT_MAX_INSERT or whole_sentence or crosses:
            report["skipped"] += n
            return
        if pos in untimed_at or any(not (b0 <= prev["end"] or a0 >= nxt["start"]) for a0, b0 in blind):
            report["skipped"] += n
            return
        lens = [max(1, len(S[s]["k"][0])) for s in sidx_list]
        lead = " " if lead_space else ""

        side = "before" if (before_end and prev["seg"] != nxt["seg"]) else "after"
        host = nxt if side == "before" else prev
        if _FLEX_SCRIPT_GAP_PER_WORD * n <= gap <= 0.75 * n + 0.5:
            a = prev["end"] + min(0.02, gap * 0.05)
            b = nxt["start"] - min(0.02, gap * 0.05)
            span = max(0.0, b - a)
            total = min(span, sum(min(0.45, 0.07 * L + 0.08) for L in lens))
            t0 = (b - total) if side == "before" else a
            words = []
            for s, L in zip(sidx_list, lens):
                d = total * L / float(sum(lens))
                words.append({"text": _flex_script_text(S[s]["t"], lead, roman), "start": t0, "end": t0 + d, "added": True})
                t0 += d
            host.setdefault("ins_" + side, []).extend(words)
            report["added"] += n
            return
        short = all(len(S[s]["k"][0]) <= 4 for s in sidx_list)
        if n <= 2 and short and gap < _FLEX_SCRIPT_GAP_PER_WORD * n:

            if before_end and prev["seg"] != nxt["seg"]:
                h = nxt
            else:
                h = prev if (prev["end"] - prev["start"]) >= (nxt["end"] - nxt["start"]) else nxt
            if h["end"] - h["start"] >= 0.25:
                h.setdefault("share_after" if h is prev else "share_before", []).extend(sidx_list)
                report["added"] += n
                return
        report["skipped"] += n

    by_first_t = {}
    for p in pairs:
        by_first_t[p[1][0]] = p
    j = 0
    while j < len(T):
        if j in unheard:
            put_unheard(j, unheard[j])
        t = T[j]
        p = by_first_t.get(j)
        if p is None:
            report["kept"] += 1
            t["out"] = [{"text": kept_text(t["text"]), "start": t["start"], "end": t["end"]}]
            j += 1
            continue
        sidx, tidx, sim, exact = p
        a0, b0 = T[tidx[0]]["start"], T[tidx[-1]]["end"]
        lead = _flex_lead(t["text"])
        report["matched"] += len(tidx)
        if len(sidx) == 1:
            out = [{"text": _flex_script_text(S[sidx[0]]["t"], lead, roman), "start": a0, "end": b0}]
        else:
            lens = [max(1, len(S[s]["k"][0])) for s in sidx]
            out, a = [], a0
            for k, (s, L) in enumerate(zip(sidx, lens)):
                d = (b0 - a0) * L / float(sum(lens))
                out.append({"text": _flex_script_text(S[s]["t"], lead if k == 0 else (" " if lead_space else ""), roman),
                            "start": a, "end": a + d})
                a += d
        heard = "".join(T[x]["text"] for x in tidx).strip()
        said = (" " if lead_space else "").join(o["text"].strip() for o in out)
        if heard != said:
            report["fixed"] += 1
        t["out"] = out
        for x in tidx[1:]:
            T[x]["out"] = []
            T[x]["owner"] = j
        j = tidx[-1] + 1
    if len(T) in unheard:
        put_unheard(len(T), unheard[len(T)])


    for t in T:
        if "owner" in t:
            own = T[t["owner"]]
            for key in ("share_after", "ins_after"):
                if t.get(key):
                    own[key] = (own.get(key) or []) + t.pop(key)
            for key in ("share_before", "ins_before"):
                if t.get(key):
                    own[key] = t.pop(key) + (own.get(key) or [])

    for t in T:
        outs = t.get("out")
        before, after = t.get("share_before") or [], t.get("share_after") or []
        if not outs or (not before and not after):
            continue
        a, b = outs[0]["start"], outs[-1]["end"]
        lead = _flex_lead(outs[0]["text"])
        lens = [max(1, len(S[s]["k"][0])) for s in before] + [max(1, sum(len(o["text"].strip()) for o in outs))] + \
               [max(1, len(S[s]["k"][0])) for s in after]
        total, at, res = float(sum(lens)), a, []
        for i, s in enumerate(before):
            d = (b - a) * lens[i] / total
            res.append({"text": _flex_script_text(S[s]["t"], lead if i == 0 else (" " if lead_space else ""), roman),
                        "start": at, "end": at + d, "added": True})
            at += d
        d_main = (b - a) * lens[len(before)] / total
        inner = sum(max(0.0, o["end"] - o["start"]) for o in outs) or 1.0
        for k, o in enumerate(outs):
            dd = d_main * max(0.0, o["end"] - o["start"]) / inner
            text = o["text"] if (k or not before) else ((" " if lead_space else "") + o["text"].lstrip())
            res.append({"text": text, "start": at, "end": at + dd})
            at += dd
        for k, s in enumerate(after):
            d = (b - a) * lens[len(before) + 1 + k] / total
            res.append({"text": _flex_script_text(S[s]["t"], " " if lead_space else "", roman), "start": at, "end": at + d, "added": True})
            at += d
        t["out"] = res


    by_word = {}
    for t in T:
        by_word.setdefault((t["seg"], t["idx"]), []).append(t)
    for si, seg in enumerate(segs):
        words = seg.get("words", []) or []
        if not words:
            continue
        lst, changed = [], False
        for wi, w in enumerate(words):
            parts = by_word.get((si, wi))
            if not parts:
                lst.append(w)
                continue
            outs = []
            for t in parts:
                outs.extend(t.get("ins_before") or [])
                outs.extend(t.get("out") or [])
                outs.extend(t.get("ins_after") or [])
            for k, o in enumerate(outs):
                if k == 0 and not o.get("added"):
                    nw = dict(w)
                else:
                    nw = {kk: vv for kk, vv in w.items() if kk in ("speaker",)}
                nw["word"] = o["text"]
                if "text" in nw:
                    nw["text"] = o["text"]
                nw["start"] = round(o["start"], 4)
                nw["end"] = round(max(o["start"], o["end"]), 4)
                if o.get("added"):
                    nw["flex_script"] = "added"
                lst.append(nw)
            if len(outs) != 1 or outs[0]["text"] != str(w.get("word", w.get("text", ""))):
                changed = True
        seg["words"] = lst
        timed = [w for w in lst if isinstance(w.get("start"), (int, float)) and isinstance(w.get("end"), (int, float))]
        seg["text"] = "".join(str(w.get("word", w.get("text", "")) or "") for w in lst)
        if changed and timed:
            seg["start"] = timed[0]["start"]
            seg["end"] = max(w["end"] for w in timed)

    for k in range(1, len(segs)):
        try:
            if segs[k].get("words") and float(segs[k - 1].get("end", 0)) > float(segs[k].get("start", 0)):
                segs[k - 1]["end"] = max(float(segs[k - 1].get("start", 0)), float(segs[k]["start"]))
        except (TypeError, ValueError):
            pass
    if "text" in work:
        work["text"] = "".join(str(s.get("text", "")) for s in segs)
    result.clear()
    result.update(work)
    report["applied"] = True
    return report


def _flex_script_read(path):

    try:
        if not path or not os.path.exists(path):
            return ""
        with open(path, "rb") as fh:
            raw = fh.read()
    except Exception as read_error:
        print("NOTE: your script file could not be read (%s)." % read_error)
        return None
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        try:
            return raw.decode("utf-16")
        except Exception:
            pass
    for enc in ("utf-8-sig", "cp1252"):
        try:
            return raw.decode(enc)
        except Exception:
            continue
    return raw.decode("utf-8", "replace")


def _flex_script_run(args, result, when):


    path = getattr(args, "script", None)
    if not path or getattr(args, "_flex_script_done", False):
        return result
    args._flex_script_done = True
    rep = None
    try:
        text = _flex_script_read(path)
        if text is None:
            rep = {"applied": False, "heard": 0, "script": 0, "matched": 0, "fixed": 0, "added": 0, "kept": 0,
                   "skipped": 0, "share": 0.0, "reason": "the script file could not be read"}
        elif not text.strip():
            return result
        elif result.get("translated_to"):
            rep = {"applied": False, "heard": 0, "script": 0, "matched": 0, "fixed": 0, "added": 0, "kept": 0,
                   "skipped": 0, "share": 0.0,
                   "reason": "the captions were translated; your script is for the words as spoken"}
        else:
            rep = _flex_script_apply(result, text, roman=bool(getattr(args, "roman", False)))
    except Exception as script_error:
        print("NOTE: your script could not be used (%s); the captions are as transcribed." % script_error)
        return result
    if rep["applied"]:
        print("Script: %d of %d spoken words follow your script (%d corrected, %d added, %d kept as spoken%s)."
              % (rep["matched"], rep["heard"], rep["fixed"], rep["added"], rep["kept"],
                 (", %d unheard script words left out" % rep["skipped"]) if rep["skipped"] else ""))
        _flex_stage("polish", None, None, "Matched your script: %d corrected, %d added" % (rep["fixed"], rep["added"]))
    else:
        print("NOTE: your script was not used: %s. The captions are as transcribed." % rep["reason"])
    try:
        print("FLEX_SCRIPT:" + json.dumps(rep, ensure_ascii=True))
        sys.stdout.flush()
    except Exception:
        pass
    return result


def _flex_finish(args, result, output_path, max_words, fill_gaps, start_time, end_time,
                 total_pad_start, real_preroll_start, temp_audio_path):




    result = _flex_script_run(args, result, "finish")

    print("Formatting subtitles...")
    srt_content = generate_srt(
        result,
        max_words=max_words,
        fill_gaps=fill_gaps,
        start_time=start_time,
        end_time=end_time,
        pad_start=total_pad_start,
        real_preroll=real_preroll_start
    )



    if getattr(args, "emit_json", None):
        try:
            os.makedirs(os.path.dirname(os.path.abspath(args.emit_json)), exist_ok=True)
            with open(args.emit_json, "w", encoding="utf-8") as jf:
                json.dump(_flex_unpadded(result, total_pad_start), jf, ensure_ascii=False)
            print("SUCCESS: Transcript JSON written to %s" % args.emit_json)
        except Exception as emit_error:
            print("NOTE: could not write the transcript JSON: %s" % emit_error)


    try:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(srt_content)
        print(f"SUCCESS: Subtitles written to {output_path}")




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





                    w_start -= total_pad_start
                    w_end -= total_pad_start
                    if w_end <= 0.0:
                        continue
                    if w_start < 0.0:
                        w_start = 0.0
                    words.append({
                        "word": text,
                        "start": round(w_start, 4),
                        "end": round(w_end, 4),
                    })
            if words:
                words_path = re.sub(r"\.srt$", "", output_path, flags=re.IGNORECASE) + ".words.json"
                with open(words_path, "w", encoding="utf-8") as wf:
                    json.dump({"words": words, "count": len(words)}, wf, ensure_ascii=False)
                print(f"SUCCESS: Word timings written to {words_path}")
            else:
                print("NOTE: no word-level timings available (update openai-whisper for Animated Captions).")
        except Exception as word_error:
            print(f"NOTE: could not write word timings: {word_error}")
    except Exception as e:
        print(f"Error writing SRT file: {str(e)}")
    finally:

        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
                print("Temporary files cleaned up.")
            except Exception as e:
                print(f"Warning: Failed to remove temporary audio file: {str(e)}")

if __name__ == "__main__":
    main()
