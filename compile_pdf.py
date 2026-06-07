"""
Facebook Messenger Chat Timeline — Print-Optimized PDF Exhibit Engine
Standalone companion to core/parse_calls.py. Reads the same data sources and emits a
text-only, court-binder-ready PDF (EXHIBITS/timeline_exhibit.pdf) via ReportLab.

Glyph strategy: built-in Helvetica + ASCII directional markers (>> outbound,
<< inbound, [CALL]). No font embedding, so output renders cleanly in one pass.
"""

import csv
import json
import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
    EASTERN = ZoneInfo("America/New_York")
    _PYTZ = False
except ImportError:
    import pytz as _pytz
    EASTERN = _pytz.timezone("America/New_York")
    _PYTZ = True

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, LongTable, TableStyle,
    Paragraph, Spacer, Flowable,
)
from reportlab.pdfgen import canvas

class KeepTogether(Flowable):
    def __init__(self, flowables):
        self.flowables = flowables
        self.width = 0
        self.height = 0

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        self.height = 0
        for f in self.flowables:
            w, h = f.wrap(availWidth, availHeight)
            f._wrapped_height = h
            self.height += h
        return self.width, self.height

    def drawOn(self, canvas, x, y, _sW=0):
        curr_y = y + self.height
        for f in self.flowables:
            h = getattr(f, '_wrapped_height', 0)
            curr_y -= h
            f.drawOn(canvas, x, curr_y, _sW)

# ── Paths ─────────────────────────────────────────────────────────────────────

SCRIPT_DIR       = Path(__file__).parent
IMPORT_DIR       = SCRIPT_DIR / "Messenger_Import"
EXHIBITS_DIR     = SCRIPT_DIR / "EXHIBITS"

ANNOTATIONS_FILE = IMPORT_DIR / "call_annotations.csv"
RENAME_MAP_FILE  = EXHIBITS_DIR / "media" / "rename_map.json"

EXCLUDED_JSON_NAMES = {"rename_map.json"}


def resolve_input_file(file_arg: str | None) -> Path | None:
    if not file_arg:
        print("[ERROR] No input file specified.")
        return None
    p = Path(file_arg)
    target = p if p.is_absolute() else IMPORT_DIR / p
    if target.exists() and target.is_file():
        return target
    print(f"[ERROR] Specified file does not exist or is not a file: '{file_arg}'")
    return None

# ── Identity & layout constants ─────────────────────────────────────────────

COL_LEFT   = 202
COL_CENTER = 100
COL_RIGHT  = 202
PAGE_W, PAGE_H = letter                       # 612 x 792 pt
SIDE_MARGIN = (PAGE_W - (COL_LEFT + COL_CENTER + COL_RIGHT)) / 2   # 54 pt

BLUE  = colors.HexColor("#0084ff")            # outbound accent
SLATE = colors.HexColor("#65676b")            # inbound accent
AMBER = colors.HexColor("#FEF3C7")            # late-night / unanswered priority
CALL_TINT = colors.HexColor("#E2E8F0")        # standard video-call log rows
DARK  = colors.HexColor("#1c1e21")
GREY  = colors.HexColor("#999999")

LATE_NIGHT_HOUR = 21                          # 9:00 PM local threshold

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
    return raw_sender.casefold() == left_name.casefold()


def localize_naive(naive_dt: datetime) -> datetime:
    if _PYTZ:
        return EASTERN.localize(naive_dt)         # type: ignore[attr-defined]
    return naive_dt.replace(tzinfo=EASTERN)


def minute_key(dt: datetime) -> tuple:
    """(year, month, day, hour, minute) in Eastern local time."""
    return (dt.year, dt.month, dt.day, dt.hour, dt.minute)


def normalize_uri(uri: str) -> str:
    if "media/" in uri:
        return "media/" + uri.split("media/")[-1]
    return uri.lstrip("./").lstrip("/").lstrip("\\")

# ── Ingestion ─────────────────────────────────────────────────────────────────

def load_rename_map() -> dict:
    if RENAME_MAP_FILE.exists():
        try:
            with open(RENAME_MAP_FILE, encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, json.JSONDecodeError):
            pass
    return {}


def load_annotations() -> dict[tuple, str]:
    """Read positional CSV (no header) -> {minute_tuple: override_type}."""
    result: dict[tuple, str] = {}
    if not ANNOTATIONS_FILE.exists():
        return result
    try:
        with open(ANNOTATIONS_FILE, encoding="utf-8", newline="") as fh:
            for row in csv.reader(fh):
                if len(row) < 3 or not row[0].strip() or not row[1].strip():
                    continue
                combined = f"{row[0].strip()} {row[1].strip()}"
                naive = None
                for fmt in ("%Y-%m-%d %I:%M %p", "%Y-%m-%d %I:%M%p", "%Y-%m-%d %H:%M"):
                    try:
                        naive = datetime.strptime(combined, fmt)
                        break
                    except ValueError:
                        continue
                if naive is None:
                    continue
                result[minute_key(localize_naive(naive))] = row[2].strip().lower()
    except OSError:
        pass
    return result


def exhibit_filename(uri: str, dt: datetime, rmap: dict) -> str:
    """Resolve the clean, renamed filename for a media attachment."""
    basename = Path(normalize_uri(uri)).name
    if basename in rmap:
        return Path(rmap[basename]).name
    return f"{dt.strftime('%Y-%m-%d_%H-%M-%S')}{Path(basename).suffix.lower()}"


def parse_records(path: Path, annotations: dict[tuple, str], rmap: dict,
                  left_name: str,
                  right_name: str) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)

    records: list[dict] = []
    for msg in data.get("messages", []):
        if not isinstance(msg, dict):
            continue
        try:
            ts_ms = int(msg["timestamp"])
            dt = ts_to_eastern(ts_ms)
        except (KeyError, TypeError, ValueError):
            continue

        raw_sender = fix_encoding(msg.get("senderName", ""))
        is_jon     = is_left_sender(raw_sender, left_name)
        msg_type = msg.get("type", "")
        text     = fix_encoding((msg.get("text") or "").strip())
        media    = msg.get("media") or []

        def make(content: str, footnote: str = "",
                 is_call: bool = False, is_override: bool = False,
                 mtype: str = "", txt: str = "",
                 filename: str = "", uri: str = "") -> dict:
            return {"ts_ms": ts_ms, "dt": dt, "is_jon": is_jon,
                    "content": content, "footnote": footnote,
                    "is_call": is_call, "is_override": is_override,
                    "msg_type": mtype, "text": txt,
                    "filename": filename, "uri": uri}

        if msg_type == "text":
            records.append(make(text or "(no text captured)", mtype="text", txt=text))

        elif msg_type == "media":
            if media:
                for att in media:
                    if isinstance(att, dict) and (att.get("uri") or "").strip():
                        uri = att["uri"].strip()
                        fname = exhibit_filename(uri, dt, rmap)
                        records.append(make(f"[MEDIA EXHIBIT: {fname}]", mtype="media", filename=fname, uri=uri))
            else:
                records.append(make("[MEDIA EXHIBIT: attachment missing from export]", mtype="media"))

        elif msg_type == "link":
            if annotations.get(minute_key(dt)) == "unanswered":
                records.append(make(
                    "[CALL] Facebook Video Call \u2014 Unanswered",
                    footnote="*Status verified via cross-referenced local history logs*",
                    is_call=True, is_override=True, mtype="link",
                ))
            else:
                records.append(make(
                    "Video Call Log Entry (Platform Metadata Trace)", is_call=True, mtype="link"))

        else:
            records.append(make(text or "Unknown record", mtype=msg_type, txt=text))
    records.sort(key=lambda r: r["ts_ms"], reverse=True)
    return records

# ── Paragraph styles ──────────────────────────────────────────────────────────

STYLE_OUT = ParagraphStyle("out", fontName="Helvetica", fontSize=8.5,
                           leading=11, textColor=DARK, alignment=TA_LEFT,
                           spaceBefore=0, spaceAfter=0)
STYLE_IN  = ParagraphStyle("in", fontName="Helvetica", fontSize=8.5,
                           leading=11, textColor=DARK, alignment=TA_RIGHT,
                           spaceBefore=0, spaceAfter=0)
STYLE_CHALK_LEFT = ParagraphStyle("chalk_left", fontName="Helvetica", fontSize=8.5,
                                  leading=11, textColor=DARK, alignment=TA_RIGHT)
STYLE_CHALK_RIGHT = ParagraphStyle("chalk_right", fontName="Helvetica", fontSize=8.5,
                                   leading=11, textColor=DARK, alignment=TA_LEFT)
STYLE_CHALK_DATE = ParagraphStyle("chalk_date", fontName="Helvetica-Bold", fontSize=9,
                                  leading=11, textColor=DARK, alignment=TA_CENTER)
STYLE_FOOT_OUT = ParagraphStyle("foot_out", fontName="Helvetica-Oblique",
                                fontSize=6.5, leading=8, textColor=GREY, alignment=TA_LEFT)
STYLE_FOOT_IN  = ParagraphStyle("foot_in", fontName="Helvetica-Oblique",
                                fontSize=6.5, leading=8, textColor=GREY, alignment=TA_RIGHT)
STYLE_DATE = ParagraphStyle("date", fontName="Helvetica", fontSize=7.5,
                            leading=9.5, textColor=DARK, alignment=TA_CENTER,
                            spaceBefore=0, spaceAfter=0)
STYLE_HDR_L = ParagraphStyle("hdr_l", fontName="Helvetica-Bold", fontSize=9,
                             leading=11, textColor=BLUE, alignment=TA_LEFT)
STYLE_HDR_C = ParagraphStyle("hdr_c", fontName="Helvetica-Bold", fontSize=9,
                             leading=11, textColor=DARK, alignment=TA_CENTER)
STYLE_HDR_R = ParagraphStyle("hdr_r", fontName="Helvetica-Bold", fontSize=9,
                             leading=11, textColor=SLATE, alignment=TA_RIGHT)
STYLE_TITLE = ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=14,
                             leading=17, textColor=DARK, alignment=TA_CENTER)
STYLE_SUB = ParagraphStyle("sub", fontName="Helvetica", fontSize=8,
                           leading=11, textColor=SLATE, alignment=TA_CENTER)
STYLE_STATS_L = ParagraphStyle("stats_l", fontName="Helvetica", fontSize=10,
                               leading=14, textColor=DARK, alignment=TA_RIGHT)
STYLE_STATS_C = ParagraphStyle("stats_c", fontName="Helvetica", fontSize=10,
                               leading=14, textColor=DARK, alignment=TA_CENTER)
STYLE_STATS_R = ParagraphStyle("stats_r", fontName="Helvetica", fontSize=10,
                               leading=14, textColor=DARK, alignment=TA_LEFT)


def esc(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def compute_metrics(records: list[dict]) -> dict[str, int]:
    metrics = {
        "left_text": 0, "left_media": 0, "left_connected": 0, "left_unanswered": 0,
        "right_text": 0, "right_media": 0, "right_connected": 0, "right_unanswered": 0,
    }
    for rec in records:
        is_media = rec["content"].startswith("[MEDIA EXHIBIT:")
        is_override = rec.get("is_override", False)
        is_call = rec.get("is_call", False)
        
        is_unanswered_call = (is_call is True) and (is_override is True)
        is_connected_call = (is_call is True) and (is_override is False)

        if is_unanswered_call:
            if rec["is_jon"]:
                metrics["right_unanswered"] += 1
            else:
                metrics["left_unanswered"] += 1
        elif rec["is_jon"]:
            if is_connected_call:
                metrics["left_connected"] += 1
            elif is_media:
                metrics["left_media"] += 1
            else:
                metrics["left_text"] += 1
        else:
            if is_connected_call:
                metrics["right_connected"] += 1
            elif is_media:
                metrics["right_media"] += 1
            else:
                metrics["right_text"] += 1
    return metrics


def make_cell(rec: dict, chalk_line: bool = False, is_left: bool = True) -> Paragraph | list:
    if chalk_line:
        body_style = STYLE_CHALK_LEFT if is_left else STYLE_CHALK_RIGHT
    else:
        body_style = STYLE_OUT if rec["is_jon"] else STYLE_IN
    ts = rec["dt"].strftime("%I:%M %p")       # zero-padded, e.g. "07:22 PM"

    # Ensure filename is resolved using the rename registry mapping
    filename = rec.get("filename", "")
    if not filename and rec.get("uri"):
        rmap = load_rename_map()
        filename = exhibit_filename(rec["uri"], rec["dt"], rmap)

    # Expanded media interception check: handles type "media", "image", or image/video extensions
    ext = Path(filename).suffix.lower() if filename else ""
    is_video = ext in ('.mp4', '.mov', '.avi', '.mkv', '.3gp', '.wmv', '.webm', '.flv', '.m4v')
    is_photo = ext in ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.heic', '.bmp', '.tiff', '.tif')
    is_media_record = rec.get("msg_type") in ("media", "image") or is_video or is_photo

    if is_media_record:
        if filename:
            # Determine prefix and text labels based on chalk_line
            if chalk_line:
                ts_prefix = f"{ts} \u2014 "
            else:
                ts_prefix = f"<b>{ts}</b> \u2014 "
                
            media_type_label = "VIDEO" if is_video else "IMAGE"
            
            if is_video:
                # Look up original UUID stem from the registry mapping
                rmap = load_rename_map()
                orig_uuid_stem = None
                for k, v in rmap.items():
                    if Path(v).name == filename or v == filename:
                        orig_uuid_stem = Path(k).stem
                        break
                if not orig_uuid_stem and rec.get("uri"):
                    orig_uuid_stem = Path(rec["uri"]).stem
                if not orig_uuid_stem:
                    orig_uuid_stem = Path(filename).stem
                    
                img_path = EXHIBITS_DIR / "media" / "thumbnails" / f"{orig_uuid_stem}.jpg"
            else:
                img_path = EXHIBITS_DIR / "media" / filename
                
            # Programmatically verify asset existence on disk before instantiation
            if img_path.exists() and img_path.is_file():
                try:
                    from reportlab.platypus import Image
                    img = Image(str(img_path))
                    orig_w = img.imageWidth
                    orig_h = img.imageHeight
                    
                    if orig_w > 0:
                        max_w = 180.0
                        scale = max_w / orig_w
                        img.drawWidth = max_w
                        img.drawHeight = orig_h * scale
                        
                    # Alignment based on columns
                    if chalk_line:
                        img.hAlign = 'RIGHT' if is_left else 'LEFT'
                    else:
                        img.hAlign = 'LEFT' if is_left else 'RIGHT'
                        
                    label_html = f"{ts_prefix}<b>{media_type_label}: {filename}</b>"
                    p_flowable = Paragraph(label_html, body_style)
                    
                    return KeepTogether([p_flowable, Spacer(1, 4), img])
                except Exception:
                    pass
            else:
                print(f"[DIAGNOSTIC] Asset verification failed. Searched path: {img_path.resolve()}")
            
            # If asset is missing from disk or loading failed, fall back to high-visibility text placeholder
            label_html = f"{ts_prefix}<b>{media_type_label}: {filename}</b> <font color=\"#DC2626\"><b>[MISSING CACHE REFERENCE]</b></font>"
            return Paragraph(label_html, body_style)
        else:
            # Filename empty (missing from export)
            if chalk_line:
                label_html = f"{ts} \u2014 <b>IMAGE: attachment missing from export</b>"
            else:
                label_html = f"<b>{ts}</b> \u2014 <b>IMAGE: attachment missing from export</b>"
            return Paragraph(label_html, body_style)

    if chalk_line:
        if rec.get("is_override"):
            html = f'<b>{ts}</b> \u2014 <font color="#D97706"><b>[UNANSWERED CALL]</b></font>'
            return Paragraph(html, body_style)
        elif rec.get("is_call"):
            color = "#0052CC" if is_left else "#DC2626"
            html = f'<b>{ts}</b> \u2014 <font color="{color}"><b>[VIDEO CALL]</b></font>'
            return Paragraph(html, body_style)
        elif rec.get("msg_type") == "text":
            body_text = '<b>[TEXT]</b>'
            html = f'{ts} \u2014 {body_text}'
            return Paragraph(html, body_style)
        else:
            body_text = esc(rec["content"])
            html = f'{ts} \u2014 {body_text}'
            return Paragraph(html, body_style)
    else:
        if rec.get("is_override") or rec.get("is_call"):
            color = "#2563EB" if is_left else "#DC2626"
            label_text = "[UNANSWERED CALL]" if rec.get("is_override") else "[VIDEO CALL]"
            body_text = f'<font color="{color}"><b>{label_text}</b></font>'
        else:
            body_text = esc(rec["content"])
        html = f'<b>{ts}</b> \u2014 {body_text}'
        if rec["footnote"]:
            html += f'<br/><font size="6.5" color="#999999"><i>{esc(rec["footnote"])}</i></font>'
        return Paragraph(html, body_style)

# ── Table assembly ─────────────────────────────────────────────────────────────

def build_table(records: list[dict],
                left_name: str,
                right_name: str,
                chalk_line: bool = False) -> LongTable:
    # Row 0 is an identity header repeated on every page.
    rows: list[list] = [[
        Paragraph(esc(left_name), STYLE_HDR_L),
        Paragraph("DATE", STYLE_HDR_C),
        Paragraph(esc(right_name), STYLE_HDR_R),
    ]]

    if chalk_line:
        style_cmds: list = [
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            # Distinct header separator
            ("TOPPADDING", (0, 0), (-1, 0), 6),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ("LINEBELOW", (0, 0), (-1, 0), 1.5, DARK),
        ]
    else:
        style_cmds: list = [
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
            # Distinct header separator
            ("TOPPADDING", (0, 0), (-1, 0), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
            ("LINEBELOW", (0, 0), (-1, 0), 1.5, DARK),
        ]

    last_date_str = None

    for idx, rec in enumerate(records):
        date_str = rec["dt"].strftime("%b %d, %Y")

        if chalk_line:
            if date_str != last_date_str:
                last_date_str = date_str
                # Create a clean paragraph for the date
                date_p = Paragraph(f"<b>{esc(date_str)}</b>", STYLE_CHALK_DATE)
                # Append to the data list matrix
                rows.append(["", date_p, ""])
                row_idx = len(rows) - 1

                # Apply explicit alignment and padding overrides to this specific row index
                style_cmds.append(('ALIGN', (1, row_idx), (1, row_idx), 'CENTER'))
                style_cmds.append(('VALIGN', (1, row_idx), (1, row_idx), 'MIDDLE'))
                style_cmds.append(('BOTTOMPADDING', (1, row_idx), (1, row_idx), 12))
                style_cmds.append(('TOPPADDING', (1, row_idx), (1, row_idx), 12))

            is_left = rec["is_jon"]

            cell = make_cell(rec, chalk_line=chalk_line, is_left=is_left)
            left  = cell if is_left else ""
            right = "" if is_left else cell
            center = ""

            rows.append([left, center, right])
            r = len(rows) - 1

            # Accent line on the data-bearing cell side that touches the center axis
            if is_left:
                style_cmds.append(('LINEAFTER', (0, r), (0, r), 2, colors.HexColor('#0052CC')))
            else:
                style_cmds.append(('LINEBEFORE', (2, r), (2, r), 2, colors.HexColor('#DC2626')))
        else:
            is_jon = rec["is_jon"]
            cell = make_cell(rec, chalk_line=chalk_line, is_left=is_jon)
            left  = cell if is_jon else ""
            right = "" if is_jon else cell

            if date_str == last_date_str:
                center = ""
            else:
                center = Paragraph(esc(date_str), STYLE_DATE)
                last_date_str = date_str

            rows.append([left, center, right])
            r = len(rows) - 1

            # Outer Edge Channel Borders: 2.5pt left border for Outbound (Left Party), 2.5pt right border for Inbound (Right Party)
            if is_jon:
                style_cmds.append(("LINEBEFORE", (0, r), (0, r), 2.5, colors.HexColor("#2563EB")))
            else:
                style_cmds.append(("LINEAFTER", (2, r), (2, r), 2.5, colors.HexColor("#DC2626")))

    col_widths = [222, 60, 222] if chalk_line else [COL_LEFT, COL_CENTER, COL_RIGHT]
    table = LongTable(rows, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle(style_cmds))
    return table

# ── Two-pass "Page X of Y" canvas ──────────────────────────────────────────────

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_states = []

    def showPage(self):
        self._saved_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved_states)
        for state in self._saved_states:
            self.__dict__.update(state)
            self._draw_footer(total)
            super().showPage()
        super().save()

    def _draw_footer(self, total: int):
        self.setStrokeColor(colors.HexColor("#dddfe2"))
        self.setLineWidth(0.5)
        self.line(SIDE_MARGIN, 40, PAGE_W - SIDE_MARGIN, 40)
        self.setFont("Helvetica", 7)
        self.setFillColor(GREY)
        self.drawString(SIDE_MARGIN, 30,
                        "CONFIDENTIAL — Facebook Messenger Forensic Timeline Exhibit")
        self.drawRightString(PAGE_W - SIDE_MARGIN, 30,
                             f"Page {self._pageNumber} of {total}")

# ── Document build ──────────────────────────────────────────────────────────────

def build_pdf(date_from: str | None = None, file_path: str | None = None,
              left_party: str = None,
              right_party: str = None,
              chalk_line: bool = False) -> None:
    if file_path is None or left_party is None or right_party is None:
        print("[ERROR] Missing mandatory runtime arguments.")
        sys.exit(1)

    cutoff_dt = None
    if date_from:
        try:
            cutoff_dt = localize_naive(datetime.strptime(date_from, "%Y-%m-%d"))
            print(f"PDF Filter Active: Compiling records on/after {date_from} (00:00 ET)\n")
        except ValueError:
            print(f"[ERROR] Invalid --date-from '{date_from}'; expected YYYY-MM-DD")
            sys.exit(1)

    input_file = resolve_input_file(file_path)
    if input_file is None:
        sys.exit(1)

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

    parse_left_name = detected_left or left_party
    parse_right_name = detected_right or right_party

    rmap        = load_rename_map()
    annotations = load_annotations()
    records     = parse_records(input_file, annotations, rmap,
                                left_name=parse_left_name, right_name=parse_right_name)

    # Date interception: drop any record before midnight ET of the cutoff day.
    if cutoff_dt is not None:
        records = [r for r in records if r["dt"] >= cutoff_dt]

    late = sum(1 for r in records
               if not r["is_jon"] and r["dt"].hour >= LATE_NIGHT_HOUR)
    print(f"Compiling {len(records):,} records "
          f"({late} late-night inbound highlighted).")

    EXHIBITS_DIR.mkdir(parents=True, exist_ok=True)
    pdf_filename = "timeline_exhibit_chalk_line.pdf" if chalk_line else "timeline_exhibit.pdf"
    output_pdf_path = EXHIBITS_DIR / pdf_filename

    doc = BaseDocTemplate(
        str(output_pdf_path), pagesize=letter,
        leftMargin=SIDE_MARGIN, rightMargin=SIDE_MARGIN,
        topMargin=54, bottomMargin=54,
        title="Facebook Messenger Timeline Exhibit",
    )
    frame = Frame(SIDE_MARGIN, 54, PAGE_W - 2 * SIDE_MARGIN,
                  PAGE_H - 108, id="main")
    doc.addPageTemplates([PageTemplate(id="all", frames=[frame])])

    generated = datetime.now(tz=EASTERN).strftime("%B %d, %Y, %I:%M %p ET")
    m = compute_metrics(records)
    if records:
        earliest_dt = records[-1]["dt"]
        latest_dt = records[0]["dt"]
        earliest_str = earliest_dt.strftime("%B %d, %Y")
        latest_str = latest_dt.strftime("%B %d, %Y")
        scope_str = f"Timeline Scope: {earliest_str} to {latest_str}"
    else:
        scope_str = "Timeline Scope: No records parsed"

    stats_data = [[
        Paragraph(
            f"<b>{esc(left_party).upper()} TOTALS</b><br/>"
            f"Text Messages: {m['left_text']:,}<br/>"
            f"Media Exhibits: {m['left_media']:,}<br/>"
            f"Connected Video Calls: {m['left_connected']:,}<br/>"
            f"Unanswered Video Calls: {m['left_unanswered']:,}",
            STYLE_STATS_L
        ),
        "",
        Paragraph(
            f"<b>{esc(right_party).upper()} TOTALS</b><br/>"
            f"Text Messages: {m['right_text']:,}<br/>"
            f"Media Exhibits: {m['right_media']:,}<br/>"
            f"Connected Video Calls: {m['right_connected']:,}<br/>"
            f"Unanswered Video Calls: {m['right_unanswered']:,}",
            STYLE_STATS_R
        )
    ]]
    stats_table = LongTable(stats_data, colWidths=[222, 60, 222])
    stats_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 18),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))

    elements = [
        Paragraph("Facebook Messenger Chat Timeline", STYLE_TITLE),
        Paragraph(f"{esc(left_party)} &amp; {esc(right_party)}", STYLE_SUB),
        Paragraph(
            f"Source: {esc(input_file.name)} &nbsp;&bull;&nbsp; "
            f"Total Records: {len(records):,} &nbsp;&bull;&nbsp; "
            f"Generated: {esc(generated)}", STYLE_SUB),
        Paragraph(esc(scope_str), STYLE_SUB),
        Spacer(1, 12),
        stats_table,
        build_table(records, left_name=left_party, right_name=right_party, chalk_line=chalk_line),
    ]
    doc.build(elements, canvasmaker=NumberedCanvas)
    print(f"PDF saved: {output_pdf_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Forensic PDF timeline exhibit builder")
    parser.add_argument("--date-from", type=str, default=None,
                        help="Filter records starting from this date in YYYY-MM-DD format")
    parser.add_argument("-f", "--file", type=str, required=True,
                        help="Path to the target raw Messenger JSON export file")
    parser.add_argument("--left-party", type=str, required=True,
                        help="Explicit name string of the outbound/left-column participant")
    parser.add_argument("--right-party", type=str, required=True,
                        help="Explicit name string of the inbound/right-column participant")
    parser.add_argument("--chalk-line", action="store_true",
                        help="Toggle high-contrast centerline presentation mode with high-density file referencing")
    args = parser.parse_args()
    build_pdf(date_from=args.date_from, file_path=args.file,
              left_party=args.left_party, right_party=args.right_party,
              chalk_line=args.chalk_line)
