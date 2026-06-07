"""
Facebook Messenger Chat Timeline — Forensic Evidence Report
Parses input_export.json with optional call_annotations.csv overlay.

call_annotations.csv — NO header row required, positional columns:
  Col 0 = date_string   e.g.  2026-05-28
  Col 1 = time_string   e.g.  6:24 PM
  Col 2 = override_type e.g.  unanswered
  Col 3 = notes         e.g.  Verified via local device history logs

Matching is local-time minute-exact: "6:24 PM" matches any JSON record
whose Eastern-time display falls in that minute.  The CSV can ONLY modify
existing records — it can never inject new rows into the timeline.
"""

import json
import csv
import argparse
import html as html_lib
import shutil
import webbrowser
from datetime import datetime, timezone

try:
    import cv2 as _cv2
    _CV2 = True
except ImportError:
    _cv2  = None
    _CV2  = False
    print("Note: pip install opencv-python  (enables automatic video thumbnails)")
from pathlib import Path

# ── Timezone ──────────────────────────────────────────────────────────────────

try:
    from zoneinfo import ZoneInfo
    EASTERN = ZoneInfo("America/New_York")
    _PYTZ   = False
except ImportError:
    try:
        import pytz as _pytz
        EASTERN = _pytz.timezone("America/New_York")
        _PYTZ   = True
    except ImportError:
        raise ImportError("Run: pip install pytz  (or upgrade to Python 3.9+)")

# ── Paths ─────────────────────────────────────────────────────────────────────

SCRIPT_DIR       = Path(__file__).parent.parent
IMPORT_DIR       = SCRIPT_DIR / "Messenger_Import"
EXHIBITS_DIR     = SCRIPT_DIR / "EXHIBITS"

ANNOTATIONS_FILE = IMPORT_DIR / "call_annotations.csv"
HTML_OUTPUT      = EXHIBITS_DIR / "timeline_report.html"
RENAME_MAP_FILE  = EXHIBITS_DIR / "media" / "rename_map.json"

EXCLUDED_JSON_NAMES = {"rename_map.json"}


def resolve_input_file(file_arg: str | None) -> Path | None:
    if file_arg:
        p = Path(file_arg)
        target = p if p.is_absolute() else IMPORT_DIR / p
        if target.exists() and target.is_file():
            return target
        print(f"[ERROR] Specified file does not exist or is not a file: '{file_arg}'")
        return None

    # Auto-discovery routine inside the import directory
    json_files = sorted([f for f in IMPORT_DIR.glob("*.json") if f.name not in EXCLUDED_JSON_NAMES])

    if not json_files:
        print("[ERROR] No Messenger JSON export found in the import directory.")
        return None

    if len(json_files) == 1:
        print(f"No input file specified. Defaulting to discovered file: {json_files[0].name}")
        return json_files[0]

    # Handle multiple files deterministically
    print(f"[WARN] Multiple JSON files found. Defaulting to: {json_files[0].name}")
    print("Alternatives available:")
    for alt in json_files[1:]:
        print(f"  - {alt.name}")
    return json_files[0]

# ── Identity ──────────────────────────────────────────────────────────────────

LEFT_RAW = "John Doe"

DEFAULT_LEFT_NAME  = "JOHN DOE"
DEFAULT_RIGHT_NAME = "JANE DOE"

# ── Media sets ────────────────────────────────────────────────────────────────

VIDEO_EXT = {".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm", ".m4v"}
PHOTO_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".bmp", ".tiff", ".tif"}

# ── Call label constants ──────────────────────────────────────────────────────

CALL_DEFAULT_ITYPE   = "Facebook Video Call Log"
CALL_DEFAULT_CONTENT = "Video Call Log Entry"

CALL_UNANSWERED_ITYPE    = "Facebook Video Call (Unanswered Attempt)"
CALL_UNANSWERED_CONTENT  = "\U0001f4de Video Call Attempt — Unanswered"
CALL_UNANSWERED_FOOTNOTE = "*Status verified via cross-referenced local history logs*"

# ── Centre column plain-text labels (non-call types) ─────────────────────────

CENTER_LABELS = {
    "Text Message"         : "Text",
    "Media Sent (Video)"   : "Video",
    "Media Sent (Photo)"   : "Photo",
    "Media Sent (Unknown)" : "Media",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def fix_encoding(s: str) -> str:
    """Correct Facebook's latin-1/utf-8 double-encoding mangling."""
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s

def ts_to_eastern(ts_ms: int) -> datetime:
    return datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc).astimezone(EASTERN)

def is_left_sender(raw_sender: str, left_name: str) -> bool:
    """Return True when raw_sender belongs in the left column."""
    if raw_sender.strip().upper() == left_name.strip().upper():
        return True
    # Meta export alias for the default left-column identity label.
    if left_name.strip().upper() == DEFAULT_LEFT_NAME and raw_sender.strip().upper() == LEFT_RAW.strip().upper():
        return True
    return False

def esc(text: str) -> str:
    return html_lib.escape(str(text), quote=True)

def normalize_uri(uri: str) -> str:
    """Force a strictly relative href by anchoring to the 'media/' segment.
    Everything before 'media/' is discarded — drive letters, absolute roots,
    Meta's './' prefix — so the output is always 'media/<filename>'.
    """
    if "media/" in uri:
        return "media/" + uri.split("media/")[-1]
    # Fallback for any URI that somehow lacks 'media/': strip leading separators only.
    uri = uri.lstrip("./").lstrip("/").lstrip("\\")
    return uri


def classify_media(uri: str) -> tuple[str, str]:
    """Return (interaction_type, link_label) for a media URI."""
    ext = Path(uri).suffix.lower()
    if ext in VIDEO_EXT:
        return "Media Sent (Video)", "\U0001f3a5 View Attached Video"
    if ext in PHOTO_EXT:
        return "Media Sent (Photo)", "\U0001f5bc️ View Attached Photo"
    return "Media Sent (Unknown)", "\U0001f4ce View Attached File"

def _ensure_thumbnail(video_rel_uri: str) -> str:
    """Extract the first valid frame of a local video file and cache it as a JPG.
    Returns the relative thumbnail URI (media/thumbnails/<stem>.jpg) on success,
    or an empty string if cv2 is unavailable, the video file is missing, or
    extraction fails for any reason.

    Note on Filename Convention:
    The output thumbnail is stored under 'media/thumbnails/' using the original
    raw Facebook UUID stem (e.g., '0a8d5149-6c2e-4edc-a423-b73ec6f0b36a.jpg') rather
    than a renamed timestamp. It cleanly appends '.jpg' to the stem without stacking
    extensions (e.g. it is NOT 'video.mp4.jpg').
    """
    if not _CV2:
        return ""
    video_path = IMPORT_DIR / video_rel_uri
    if not video_path.exists():
        return ""
    stem      = Path(video_rel_uri).stem
    thumb_rel = f"media/thumbnails/{stem}.jpg"
    thumb_abs = EXHIBITS_DIR / thumb_rel
    if thumb_abs.exists():
        return thumb_rel
    try:
        thumb_abs.parent.mkdir(parents=True, exist_ok=True)
        cap = _cv2.VideoCapture(str(video_path))
        ok, frame = cap.read()
        cap.release()
        if ok and frame is not None:
            _cv2.imwrite(str(thumb_abs), frame, [_cv2.IMWRITE_JPEG_QUALITY, 90])
            return thumb_rel
    except Exception as exc:
        print(f"  [WARN] Thumbnail extraction failed ({video_path.name}): {exc}")
    return ""


def _load_rename_map() -> dict:
    """Load the persistent original→renamed URI mapping from disk."""
    if RENAME_MAP_FILE.exists():
        try:
            with open(RENAME_MAP_FILE, encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            pass
    return {}

def _save_rename_map(rmap: dict) -> None:
    """Persist the rename map so re-runs are idempotent."""
    if not rmap:
        return
    try:
        RENAME_MAP_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(RENAME_MAP_FILE, "w", encoding="utf-8") as fh:
            json.dump(rmap, fh, indent=2, ensure_ascii=False)
    except Exception as exc:
        print(f"  [WARN] Could not save rename map: {exc}")

def _rename_media(original_rel: str, local_dt: datetime, rmap: dict) -> str:
    """
    Mirror a media file to a human-readable timestamp name in EXHIBITS and record the mapping.

    Algorithm
    ---------
    1. If the original filename is already in rmap, return the recorded path
       (idempotent on re-runs — the file was already mirrored on a previous run).
    2. If the file doesn't exist in the import directory, return the original path unchanged.
    3. Build a target name: YYYY-MM-DD_HH-MM-SS[_N].ext, incrementing N until
       the target path is free (handles multiple files from the same timestamp).
    4. Copy to EXHIBITS/media/, add to rmap, return the new relative path.
    """
    original_name = Path(original_rel).name

    # Already renamed in a previous run?
    if original_name in rmap:
        return rmap[original_name]

    source_abs = IMPORT_DIR / original_rel
    if not source_abs.exists():
        return original_rel     # file not present locally; skip silently

    suffix = Path(original_rel).suffix.lower()
    ts_str = local_dt.strftime("%Y-%m-%d_%H-%M-%S")

    # Resolve collisions: same-second files get _1, _2, … suffixes
    counter = 0
    while True:
        new_name = f"{ts_str}{suffix}" if counter == 0 else f"{ts_str}_{counter}{suffix}"
        new_abs  = EXHIBITS_DIR / "media" / new_name
        if not new_abs.exists():
            break
        counter += 1

    new_rel = f"media/{new_name}"
    try:
        new_abs.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_abs, new_abs)
        print(f"  [MIRROR] {original_name}  ->  {new_name}")
        rmap[original_name] = new_rel
    except OSError as exc:
        print(f"  [WARN] Mirror failed ({original_name}): {exc}")
        return original_rel

    return new_rel


def _localize_naive(naive_dt: datetime) -> datetime:
    """Attach Eastern timezone to a naive datetime (handles both pytz and zoneinfo)."""
    if _PYTZ:
        return EASTERN.localize(naive_dt)       # type: ignore[attr-defined]
    return naive_dt.replace(tzinfo=EASTERN)

def _local_minute_key(local_dt: datetime) -> tuple:
    """(year, month, day, hour, minute) in Eastern local time.
    Matching operates entirely in the local time domain so a CSV entry for
    '6:24 PM' aligns 1-to-1 with a record displayed as '6:24 PM'.
    """
    return (local_dt.year, local_dt.month, local_dt.day,
            local_dt.hour, local_dt.minute)

# ── Annotation loader ─────────────────────────────────────────────────────────

def load_annotations(csv_path: Path) -> dict[tuple, dict]:
    """
    Reads call_annotations.csv by column position (no header row assumed).
    Returns {_local_minute_key: {override_type, notes}}.
    Any unreadable or malformed row is skipped with a console warning.
    """
    if not csv_path.exists():
        return {}

    result: dict[tuple, dict] = {}

    try:
        with open(csv_path, encoding="utf-8", newline="") as fh:
            for row_num, row in enumerate(csv.reader(fh), start=1):
                # Skip completely empty lines
                if not any(cell.strip() for cell in row):
                    continue

                if len(row) < 3:
                    print(f"  [WARN] annotations row {row_num}: "
                          f"expected at least 3 columns, got {len(row)} — skipped")
                    continue

                date_str      = row[0].strip()
                time_str      = row[1].strip()
                override_type = row[2].strip().lower()
                notes         = row[3].strip() if len(row) > 3 else ""

                if not date_str or not time_str:
                    print(f"  [WARN] annotations row {row_num}: "
                          f"empty date or time — skipped")
                    continue

                combined = f"{date_str} {time_str}"
                naive_dt = None

                for fmt in (
                    "%Y-%m-%d %I:%M %p",   # "2026-05-28 6:24 PM"
                    "%Y-%m-%d %I:%M%p",    # "2026-05-28 6:24PM"  (no space)
                    "%Y-%m-%d %H:%M",      # "2026-05-28 18:24"   (24-hour)
                ):
                    try:
                        naive_dt = datetime.strptime(combined, fmt)
                        break
                    except ValueError:
                        continue

                if naive_dt is None:
                    print(f"  [WARN] annotations row {row_num}: "
                          f"cannot parse '{combined}' — skipped")
                    continue

                local_dt = _localize_naive(naive_dt)
                key      = _local_minute_key(local_dt)

                result[key] = {"override_type": override_type, "notes": notes}
                print(f"  [ANN]  row {row_num}: loaded '{combined}' ET "
                      f"-> key {key} ({override_type})")

    except OSError as exc:
        print(f"  [WARN] Could not read {csv_path.name}: {exc}")

    return result

# ── Parser ────────────────────────────────────────────────────────────────────

def parse_messages(path: Path, annotations: dict[tuple, dict],
                   cutoff_dt: datetime | None = None,
                   left_name: str = DEFAULT_LEFT_NAME,
                   right_name: str = DEFAULT_RIGHT_NAME) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)

    messages  = data.get("messages", [])
    records:  list[dict] = []
    rename_map = _load_rename_map()   # persistent map: original_name → new_rel_uri

    for idx, msg in enumerate(messages):
        if not isinstance(msg, dict):
            continue

        try:
            ts_ms    = int(msg["timestamp"])
            local_dt = ts_to_eastern(ts_ms)
        except (KeyError, TypeError, ValueError):
            print(f"  [WARN] Skipping index {idx}: missing/invalid timestamp")
            continue

        if cutoff_dt is not None and local_dt < cutoff_dt:
            continue

        raw_sender  = fix_encoding(msg.get("senderName", "Unknown"))
        is_left     = is_left_sender(raw_sender, left_name)
        is_unsent   = bool(msg.get("isUnsent", False))
        msg_type    = msg.get("type", "")
        text        = fix_encoding((msg.get("text") or "").strip())
        media_list  = msg.get("media") or []

        def make(itype: str, content: str,
                 footnote: str = "", uri: str = "") -> dict:
            return {
                "ts_ms"    : ts_ms,
                "local_dt" : local_dt,
                "itype"    : itype,
                "is_jon"   : is_left,
                "sender"   : left_name if is_left else right_name,
                "content"  : content,
                "footnote" : footnote,
                "uri"      : uri,
                "unsent"   : is_unsent,
            }

        if msg_type == "text":
            records.append(make("Text Message", text))

        elif msg_type == "media":
            if media_list:
                for att in media_list:
                    if isinstance(att, dict):
                        raw_uri = normalize_uri(fix_encoding((att.get("uri") or "").strip()))
                        if raw_uri:
                            itype, label = classify_media(raw_uri)
                            # Rename on disk to timestamp-based filename
                            final_uri = _rename_media(raw_uri, local_dt, rename_map)
                            rec = make(itype, label, uri=final_uri)
                            if itype == "Media Sent (Video)":
                                rec["thumb_uri"] = _ensure_thumbnail(raw_uri)
                            records.append(rec)
            else:
                records.append(make(
                    "Media Sent (Unknown)",
                    "\U0001f4ce Media attachment missing from export",
                ))

        elif msg_type == "link":
            # Lookup by local Eastern minute — matches only existing JSON records.
            ann = annotations.get(_local_minute_key(local_dt))
            if ann and ann["override_type"] == "unanswered":
                records.append(make(
                    CALL_UNANSWERED_ITYPE,
                    CALL_UNANSWERED_CONTENT,
                    footnote=CALL_UNANSWERED_FOOTNOTE,
                ))
            else:
                records.append(make(CALL_DEFAULT_ITYPE, CALL_DEFAULT_CONTENT))

        else:
            label = f"Unknown ({msg_type})" if msg_type else "Unknown"
            records.append(make(label, text or "No content captured"))

    _save_rename_map(rename_map)
    records.sort(key=lambda r: r["ts_ms"], reverse=True)
    return records

# ── CSS ───────────────────────────────────────────────────────────────────────

CSS = """
:root {
    --blue:      #0084ff;
    --blue-bg:   #e8f4ff;
    --blue-dim:  #b3d9ff;
    --grey:      #e4e6eb;
    --grey-dim:  #65676b;
    --dark:      #1c1e21;
    --page-bg:   #f0f2f5;
    --border:    #dddfe2;
    --red:       #cc0000;
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
    background: var(--page-bg);
    color: var(--dark);
    font-size: 14px;
    line-height: 1.4;
}
.wrap {
    max-width: 1140px;
    margin: 0 auto;
    background: #fff;
    box-shadow: 0 0 32px rgba(0,0,0,.14);
    min-height: 100vh;
}

/* ── Header ── */
.doc-header {
    background: var(--dark);
    color: #fff;
    padding: 22px 32px 18px;
}

/* ── Metrics Panel ── */
.metrics-panel {
    display: grid;
    grid-template-columns: 1fr 1fr; /* two equal halves */
    gap: 0; /* columns touch at center */
    padding: 24px 32px;
    background: var(--dark);
    border-bottom: 3px solid var(--blue);
}
.metrics-column {
    width: 100%;
}
.metrics-column.left {
    border-right: 1px solid #334155;
    padding-right: 24px;
    text-align: right;
}
.metrics-column.right {
    padding-left: 24px;
    text-align: left;
}
.metrics-column h2 {
    color: #FFFFFF;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 1.2px;
    margin-bottom: 16px;
    text-transform: uppercase;
}
.metrics-column.left h2 { color: #FFFFFF; }
.metrics-column.right h2 { color: #FFFFFF; }
.metric-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
}
.metric-row-item {
    display: flex;
    align-items: center;
    width: 100%;
    white-space: nowrap;
}
.metrics-column.left .metric-row-item {
    justify-content: flex-end;
    gap: 15px;
    text-align: right;
}
.metrics-column.right .metric-row-item {
    justify-content: flex-start;
    gap: 15px;
    text-align: left;
}
.metric-lbl {
    color: #FFFFFF;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.metric-val {
    color: #FFFFFF;
    font-size: 1.75rem;
    font-weight: bold;
    line-height: 1;
    width: 50px;
    text-align: center;
}

@media (max-width: 768px) {
    .metrics-panel {
        grid-template-columns: 1fr;
        gap: 24px;
    }
    .metrics-column.left {
        border-right: none;
        padding-right: 0;
        border-bottom: 1px solid #334155;
        padding-bottom: 24px;
        text-align: left;
    }
    .metrics-column.right {
        padding-left: 0;
        text-align: left;
    }
    .metrics-column.left .metric-row-item {
        justify-content: flex-start;
    }
    .metrics-column.right .metric-row-item {
        justify-content: flex-start;
    }
    .metrics-column.left .metric-val {
        padding-left: 0;
    }
    .metrics-column.right .metric-val {
        padding-right: 0;
        color: #ffffff;
    }
}
.doc-header h1 {
    font-size: 18px;
    font-weight: 800;
    letter-spacing: 1.4px;
    text-transform: uppercase;
    margin-bottom: 11px;
}
.meta-row {
    display: flex;
    flex-wrap: wrap;
    gap: 5px 26px;
    font-size: 11.5px;
    color: #999;
}
.meta-row strong { color: #ccc; font-weight: 600; }

/* ── Annotation banner ── */
.ann-notice {
    background: #fff8e1;
    border-left: 4px solid #f0c040;
    padding: 10px 24px;
    font-size: 11.5px;
    color: #5a4000;
}
.ann-notice code {
    font-family: 'Courier New', monospace;
    background: rgba(0,0,0,0.06);
    padding: 1px 5px;
    border-radius: 3px;
}

/* ── Sticky column bar ── */
.col-bar {
    position: sticky;
    top: 0;
    z-index: 200;
    display: grid;
    grid-template-columns: 45fr 10fr 45fr;
    border-bottom: 2px solid var(--border);
    box-shadow: 0 3px 10px rgba(0,0,0,.10);
    background: #fff;
}
.cb-left {
    padding: 9px 16px;
    background: var(--blue-bg);
    font-size: 11px;
    font-weight: 800;
    letter-spacing: .7px;
    text-transform: uppercase;
    color: var(--blue);
    border-right: 1px solid var(--border);
}
.cb-center {
    padding: 9px 4px;
    background: #fafafa;
    font-size: 9.5px;
    font-weight: 700;
    letter-spacing: .5px;
    text-align: center;
    text-transform: uppercase;
    color: #b0b0b0;
    border-right: 1px solid var(--border);
}
.cb-right {
    padding: 9px 16px;
    background: #f3f3f3;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: .7px;
    text-transform: uppercase;
    color: #444;
    text-align: right;
}

/* ── Timeline ── */
.tl {
    width: 100%;
}

/* ── Date divider ── */
.dd-row {
    width: 100%;
    padding: 22px 20px 10px;
}
.dd { display: flex; align-items: center; gap: 10px; }
.dd-line { flex: 1; height: 1px; background: #d0d3d8; }
.dd-label {
    font-size: 10.5px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #555;
    padding: 4px 13px;
    border: 1px solid #d0d3d8;
    border-radius: 14px;
    background: #fff;
    white-space: nowrap;
    user-select: none;
}

/* ── Message rows ── */
.row {
    display: grid;
    grid-template-columns: 45fr 10fr 45fr;
    width: 100%;
    align-items: center;
}
.row .c-left {
    padding: 6px 16px;
    text-align: right;
    box-sizing: border-box;
}
.row .c-center {
    padding: 6px 4px;
    text-align: center;
    align-self: stretch;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    box-sizing: border-box;
    background: transparent !important;
    box-shadow: none !important;
}
.row .c-right {
    padding: 6px 16px;
    text-align: left;
    box-sizing: border-box;
}

/* ── Bubbles (base) ── */
.bbl {
    display: inline-block;
    padding: 7px 12px 8px;
    border-radius: 18px;
    max-width: 97%;
    word-wrap: break-word;
    overflow-wrap: break-word;
    text-align: left;
}
.message-card {
    max-width: 97%;
    width: auto;
    margin: 0;
}
.bbl-l { background: var(--blue); color: #fff; border-bottom-left-radius: 4px; }
.bbl-r { background: var(--grey); color: #050505; border-bottom-right-radius: 4px; }

.bbl-meta { display: block; font-size: 10px; font-weight: 600; margin-bottom: 3px; }
.bbl-l .bbl-meta { color: var(--blue-dim); }
.bbl-r .bbl-meta { color: var(--grey-dim); }

.bbl-text { display: block; font-size: 13.5px; line-height: 1.45; white-space: pre-wrap; }
.bbl-text small { display: inline; font-size: 10px; opacity: 0.80; white-space: normal; }

/* ── Media hyperlinks ── */
a.media-link {
    display: inline-block;
    font-weight: 700;
    font-size: 13.5px;
    text-decoration: underline;
    text-underline-offset: 2px;
    border-radius: 5px;
    padding: 1px 2px;
}
a.media-link:hover { opacity: 0.75; }
.bbl-l a.media-link {
    color: #ffffff;
    text-decoration-color: rgba(255,255,255,0.55);
}
.bbl-r a.media-link {
    color: #0050a0;
    text-decoration-color: #0050a0;
}

/* ── Folder reveal button ── */
a.folder-btn {
    display: inline-block;
    margin-top: 7px;
    font-size: 11px;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 6px;
    text-decoration: none;
}
a.folder-btn:hover { opacity: 0.78; }
.bbl-l a.folder-btn {
    background: rgba(255,255,255,0.18);
    color: #ffffff;
    border: 1px solid rgba(255,255,255,0.35);
}
.bbl-r a.folder-btn {
    background: rgba(0,0,0,0.07);
    color: #333333;
    border: 1px solid rgba(0,0,0,0.15);
}

.retracted {
    display: block;
    background: var(--red);
    color: #fff;
    font-size: 9.5px;
    font-weight: 800;
    letter-spacing: .3px;
    padding: 3px 8px;
    border-radius: 4px;
    margin-bottom: 5px;
}

/* ── Call bubble overrides ── */
.bbl-l.bbl-call {
    background: #005fcc;
    border: 2px solid rgba(255,255,255,0.28);
    box-shadow: 0 2px 10px rgba(0,95,204,0.45);
}
.bbl-r.bbl-call {
    background: #d0d3db;
    border: 2px solid #9a9da8;
    box-shadow: 0 2px 10px rgba(0,0,0,0.14);
}

/* Call header strip inside bubble */
.call-header {
    display: block;
    font-size: 9.5px;
    font-weight: 800;
    letter-spacing: 1px;
    text-transform: uppercase;
    padding-bottom: 7px;
    margin-bottom: 7px;
    border-bottom: 1px solid rgba(255,255,255,0.22);
}
.bbl-l .call-header { color: #9ecfff; }
.bbl-r .call-header { color: #555555; border-bottom-color: #bbbec8; }

/* Bold enlarged timestamp for call rows */
.bbl-time-call { font-size: 13px; font-weight: 800; letter-spacing: .2px; }
.bbl-l .bbl-time-call { color: #ffffff; }
.bbl-r .bbl-time-call { color: #1c1e21; }

/* ── Centre column ── */
.dir-arrow {
    display: block;
    font-size: 20px;
    text-align: center;
    line-height: 1;
    user-select: none;
    background: transparent !important;
    box-shadow: none !important;
}
.neutral-label {
    display: block;
    font-size: 8px;
    font-weight: 600;
    color: #bbb;
    letter-spacing: .5px;
    text-transform: uppercase;
    text-align: center;
}

/* ── Summary footer ── */
.summary {
    padding: 24px 32px 36px;
    background: #f9f9f9;
    border-top: 2px solid var(--border);
}
.summary h3 {
    font-size: 10.5px;
    font-weight: 800;
    letter-spacing: .9px;
    text-transform: uppercase;
    color: #777;
    margin-bottom: 12px;
}
.s-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(270px, 1fr));
    gap: 8px;
}
.s-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 7px 12px;
    background: #fff;
    border: 1px solid var(--border);
    border-radius: 8px;
    font-size: 12px;
}
.s-lbl { color: #555; }
.s-cnt { font-weight: 800; color: var(--dark); }
"""

# ── Renderers ─────────────────────────────────────────────────────────────────

def _is_call(itype: str) -> bool:
    return itype.startswith("Facebook Video Call")

def render_divider(label: str) -> str:
    return (
        f'<div class="dd-row">'
        f'<div class="dd">'
        f'<div class="dd-line"></div>'
        f'<span class="dd-label">{esc(label)}</span>'
        f'<div class="dd-line"></div>'
        f'</div></div>'
    )

def render_center(rec: dict) -> str:
    if _is_call(rec["itype"]):
        arrow = "➡️" if rec["is_jon"] else "⬅️"
        return f'<span class="dir-arrow">{arrow}</span>'
    return ""

def render_bubble(rec: dict) -> str:
    itype   = rec["itype"]
    is_call = _is_call(itype)
    is_left = rec["is_jon"]
    time    = rec["local_dt"].strftime("%I:%M %p").lstrip("0") or "12:00 AM"

    if is_call:
        cls       = "bbl bbl-l bbl-call message-card" if is_left else "bbl bbl-r bbl-call message-card"
        time_html = f'<strong class="bbl-time-call">{esc(time)}</strong>'
        if "Unanswered" in itype:
            call_hdr = (
                '<span class="call-header">'
                '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" style="vertical-align: middle; margin-right: 4px; display: inline-block;"><path d="M17 10.5V7c0-.55-.45-1-1-1H3c-.55 0-1 .45-1 1v10c0 .55.45 1 1 1h13c.55 0 1-.45 1-1v-3.5l4 4v-11l-4 4z"/></svg>'
                'Facebook Video Call — Unanswered'
                '</span>'
            )
        else:
            call_hdr = (
                '<span class="call-header">'
                '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" style="vertical-align: middle; margin-right: 4px; display: inline-block;"><path d="M17 10.5V7c0-.55-.45-1-1-1H3c-.55 0-1 .45-1 1v10c0 .55.45 1 1 1h13c.55 0 1-.45 1-1v-3.5l4 4v-11l-4 4z"/></svg>'
                'Facebook Video Call — Connected'
                '</span>'
            )
    else:
        cls       = "bbl bbl-l message-card" if is_left else "bbl bbl-r message-card"
        time_html = esc(time)
        call_hdr  = ""

    retracted_html = (
        '<span class="retracted">[RECORD RETRACTED BY SENDER]</span>'
        if rec["unsent"] else ""
    )
    footnote_html = (
        f'<br><small><em>{esc(rec["footnote"])}</em></small>'
        if rec.get("footnote") else ""
    )

    uri = rec.get("uri", "")
    folder_btn = '<a href="media/" class="folder-btn">&#128193; Reveal in Local Folder</a>'

    if uri and rec["itype"] == "Media Sent (Video)":
        thumb = rec.get("thumb_uri", "")
        if thumb:
            preview = (
                f'<img src="{esc(thumb)}" '
                f'style="max-width:100%;border-radius:8px;display:block;'
                f'margin-top:5px;border:1px solid #ccc;">'
            )
        else:
            preview = (
                f'<video src="{esc(uri)}" controls '
                f'style="width:100%;max-width:100%;border-radius:8px;'
                f'display:block;margin-top:5px;">'
                f'Your browser does not support local video playback.</video>'
            )
        content_html = preview + folder_btn

    elif uri and rec["itype"] == "Media Sent (Photo)":
        preview = (
            f'<img src="{esc(uri)}" '
            f'style="max-width:100%;border-radius:8px;display:block;margin-top:5px;">'
        )
        content_html = preview + folder_btn

    else:
        content_html = esc(rec["content"])

    return (
        f'<div class="{cls}">'
        f'{call_hdr}'
        f'<span class="bbl-meta">{esc(rec["sender"])} &bull; {time_html}</span>'
        f'{retracted_html}'
        f'<span class="bbl-text">{content_html}{footnote_html}</span>'
        f'</div>'
    )

def render_row(rec: dict) -> str:
    bubble = render_bubble(rec)
    center = render_center(rec)
    if rec["is_jon"]:
        l_cell = bubble
        r_cell = "<div></div>"
    else:
        l_cell = "<div></div>"
        r_cell = bubble
    return (
        f'<div class="mr row">'
        f'<div class="c-left">{l_cell}</div>'
        f'<div class="c-center">{center}</div>'
        f'<div class="c-right">{r_cell}</div>'
        f'</div>'
    )

# ── Document assembly ─────────────────────────────────────────────────────────

def build_html(records: list[dict], source: str,
               generated_at: str, ann_count: int,
               left_name: str = DEFAULT_LEFT_NAME,
               right_name: str = DEFAULT_RIGHT_NAME) -> str:

    if records:
        start_dt = records[-1]["local_dt"]
        end_dt = records[0]["local_dt"]
        timeline_str = f"{start_dt.strftime('%B %d, %Y')} to {end_dt.strftime('%B %d, %Y')}"
    else:
        timeline_str = "No records"

    # Aggregate forensic statistics processing engine
    m = {
        "left_text": 0, "left_media": 0, "left_connected": 0, "left_unanswered": 0,
        "right_text": 0, "right_media": 0, "right_connected": 0, "right_unanswered": 0,
    }
    for rec in records:
        is_left = rec["is_jon"]
        itype = rec["itype"]
        is_unanswered_call = (itype == CALL_UNANSWERED_ITYPE)
        is_connected_call = (itype == CALL_DEFAULT_ITYPE) or (itype.startswith("Facebook Video Call") and not is_unanswered_call)
        is_media = itype.startswith("Media Sent")

        if is_unanswered_call:
            if is_left:
                m["right_unanswered"] += 1
            else:
                m["left_unanswered"] += 1
        elif is_left:
            if is_connected_call:
                m["left_connected"] += 1
            elif is_media:
                m["left_media"] += 1
            else:
                m["left_text"] += 1
        else:
            if is_connected_call:
                m["right_connected"] += 1
            elif is_media:
                m["right_media"] += 1
            else:
                m["right_text"] += 1

    left_total = m["left_text"] + m["left_media"] + m["left_connected"] + m["left_unanswered"]
    right_total = m["right_text"] + m["right_media"] + m["right_connected"] + m["right_unanswered"]
    connected_calls = m["left_connected"] + m["right_connected"]
    unanswered_calls = m["left_unanswered"] + m["right_unanswered"]
    total_calls = connected_calls + unanswered_calls
    total_media = m["left_media"] + m["right_media"]

    counts: dict[str, int] = {}
    for r in records:
        counts[r["itype"]] = counts.get(r["itype"], 0) + 1

    if ann_count > 0:
        noun       = "record" if ann_count == 1 else "records"
        ann_banner = (
            f'<div class="ann-notice">'
            f'&#9888;&nbsp; <strong>{ann_count} {noun}</strong> '
            f'carry device-log-verified status overrides applied from '
            f'<code>call_annotations.csv</code>.'
            f'</div>'
        )
    else:
        ann_banner = ""

    rows: list[str] = []
    current_day = None
    for rec in records:
        day = rec["local_dt"].date()
        if day != current_day:
            current_day = day
            rows.append(render_divider(rec["local_dt"].strftime("%A, %B %d, %Y")))
        rows.append(render_row(rec))

    summary_items = "".join(
        f'<div class="s-item">'
        f'<span class="s-lbl">{esc(k)}</span>'
        f'<span class="s-cnt">{v:,}</span>'
        f'</div>'
        for k, v in sorted(counts.items())
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Facebook Messenger Chat Timeline &mdash; {esc(left_name)} &amp; {esc(right_name)}</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">

  <div class="doc-header">
    <h1>Facebook Messenger Chat Timeline</h1>
    <div class="meta-row">
      <span><strong>Parties:</strong> {esc(left_name)} &amp; {esc(right_name)}</span>
      <span><strong>Source:</strong> {esc(source)}</span>
      <span style="color: #FFFFFF;"><strong style="color: #FFFFFF;">Timeline:</strong> {esc(timeline_str)}</span>
      <span><strong>Total Records:</strong> {len(records):,}</span>
      <span><strong>Generated:</strong> {esc(generated_at)}</span>
    </div>
  </div>

  <div class="metrics-panel">
    <div class="metrics-column left">
      <h2>{esc(left_name)} Metrics</h2>
      <div class="metric-list">
        <div class="metric-row-item">
          <span class="metric-lbl">Text Messages Sent</span>
          <span class="metric-val">{m['left_text']:,}</span>
        </div>
        <div class="metric-row-item">
          <span class="metric-lbl">Media Attachments Sent</span>
          <span class="metric-val">{m['left_media']:,}</span>
        </div>
        <div class="metric-row-item">
          <span class="metric-lbl">Video Calls (Connected)</span>
          <span class="metric-val">{m['left_connected']:,}</span>
        </div>
        <div class="metric-row-item">
          <span class="metric-lbl">Video Calls (Unanswered/Missed)</span>
          <span class="metric-val">{m['left_unanswered']:,}</span>
        </div>
      </div>
    </div>

    <div class="metrics-column right">
      <h2>{esc(right_name)} Metrics</h2>
      <div class="metric-list">
        <div class="metric-row-item">
          <span class="metric-val">{m['right_text']:,}</span>
          <span class="metric-lbl">Text Messages Sent</span>
        </div>
        <div class="metric-row-item">
          <span class="metric-val">{m['right_media']:,}</span>
          <span class="metric-lbl">Media Attachments Sent</span>
        </div>
        <div class="metric-row-item">
          <span class="metric-val">{m['right_connected']:,}</span>
          <span class="metric-lbl">Video Calls (Connected)</span>
        </div>
        <div class="metric-row-item">
          <span class="metric-val">{m['right_unanswered']:,}</span>
          <span class="metric-lbl">Video Calls (Unanswered/Missed)</span>
        </div>
      </div>
    </div>
  </div>

  {ann_banner}

  <div class="col-bar">
    <div class="cb-left">&#9679;&nbsp; {esc(left_name)}</div>
    <div class="cb-center"></div>
    <div class="cb-right">{esc(right_name)} &nbsp;&#9679;</div>
  </div>

  <div class="tl">
{"".join(rows)}
  </div>

  <div class="summary">
    <h3>Record Summary &mdash; {len(records):,} Total</h3>
    <div class="s-grid">{summary_items}</div>
  </div>

</div>
</body>
</html>"""

# ── Post-processing cleanup ───────────────────────────────────────────────────

def cleanup_unreferenced_media() -> None:
    """Move files in media/ whose names are not in rename_map.json to media/unrelated/.

    Safety guardrails (never violated):
      • Subdirectories (thumbnails/, unrelated/, etc.) are always skipped.
      • rename_map.json itself is always skipped.
      • If the map is empty the entire routine is aborted to prevent
        accidental mass-moves when no renames have been recorded yet.
    """
    media_dir    = EXHIBITS_DIR / "media"
    isolated_dir = media_dir / "unrelated"

    if not media_dir.exists():
        print("  [ISOLATION] media/ directory not found — nothing to process.")
        return

    rmap = _load_rename_map()
    if not rmap:
        print("  [ISOLATION] rename_map.json is empty — routine skipped to avoid "
              "accidental mass-move.")
        return

    isolated_dir.mkdir(parents=True, exist_ok=True)

    # Valid basenames = the filenames of every successfully renamed asset
    valid_names: set[str] = {Path(v).name for v in rmap.values()}

    moved = 0
    for item in sorted(media_dir.iterdir()):
        if item.is_dir():
            continue                       # skip thumbnails/, unrelated/, any subfolder
        if item.name == "rename_map.json":
            continue                       # never touch the provenance map
        if item.name not in valid_names:
            dest = isolated_dir / item.name
            try:
                shutil.move(str(item), str(dest))
                print(f"  [ISOLATION] Moved unreferenced asset to "
                      f"media/unrelated/{item.name}")
                moved += 1
            except OSError as exc:
                print(f"  [WARN]      Could not move media/{item.name}: {exc}")

    if moved == 0:
        print("  [ISOLATION] No unreferenced assets found.")
    else:
        print(f"  [ISOLATION] {moved} file(s) moved to media/unrelated/")


# ── Entry point ───────────────────────────────────────────────────────────────

def main(date_from: str | None = None, file_path: str | None = None,
         left_name: str = DEFAULT_LEFT_NAME,
         right_name: str = DEFAULT_RIGHT_NAME) -> None:
    input_file = resolve_input_file(file_path)
    if input_file is None:
        return

    cutoff_dt = None
    if date_from:
        try:
            cutoff_dt = _localize_naive(datetime.strptime(date_from, "%Y-%m-%d"))
            print(f"Date filter active: records on/after {date_from} (00:00 ET)\n")
        except ValueError:
            print(f"[ERROR] Invalid --date-from '{date_from}'; expected YYYY-MM-DD")
            return

    annotations = load_annotations(ANNOTATIONS_FILE)
    if annotations:
        print(f"\nAnnotations loaded: {len(annotations)} override(s) from "
              f"{ANNOTATIONS_FILE.name}\n")
    else:
        print("No annotations file — all calls use forensic-neutral default labels.\n")

    # Dynamic auto-detection of parties from participants
    detected_left = None
    detected_right = None
    try:
        with open(input_file, encoding="utf-8") as fh:
            data = json.load(fh)
            parts = data.get("participants", [])
            if len(parts) >= 2:
                detected_left = parts[0]
                detected_right = parts[1]
    except Exception:
        pass

    parse_left_name = detected_left or left_name
    parse_right_name = detected_right or right_name

    print(f"Parsing: {input_file.name}")
    records = parse_messages(input_file, annotations, cutoff_dt,
                             left_name=parse_left_name, right_name=parse_right_name)

    counts: dict[str, int] = {}
    for r in records:
        counts[r["itype"]] = counts.get(r["itype"], 0) + 1
    print(f"Parsed {len(records):,} records:")
    for label, n in sorted(counts.items()):
        print(f"  {n:>5}  {label}")
    print()

    ann_applied  = sum(1 for r in records if r.get("footnote"))
    generated_at = datetime.now(tz=EASTERN).strftime("%B %d, %Y, %I:%M %p ET")
    html_content = build_html(records, input_file.name, generated_at, ann_applied,
                              left_name=left_name, right_name=right_name)

    HTML_OUTPUT.write_text(html_content, encoding="utf-8")
    print(f"HTML saved: {HTML_OUTPUT}")

    if cutoff_dt is None:
        print("\nRunning media cleanup...")
        cleanup_unreferenced_media()
    else:
        print("\nSkipping media cleanup (date filter active).")

    print("\nOpening in browser...")
    webbrowser.open(HTML_OUTPUT.as_uri())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Facebook Messenger forensic timeline parser")
    parser.add_argument("--date-from", type=str, default=None,
                        help="Filter parsed records starting from this date in YYYY-MM-DD format")
    parser.add_argument("-f", "--file", type=str, default=None,
                        help="Path to the target raw Messenger JSON export file")
    parser.add_argument("--left", type=str, default=DEFAULT_LEFT_NAME,
                        help="Identity string for the left column/sender")
    parser.add_argument("--right", type=str, default=DEFAULT_RIGHT_NAME,
                        help="Identity string for the right column/sender")
    args = parser.parse_args()
    main(date_from=args.date_from, file_path=args.file,
         left_name=args.left, right_name=args.right)
