"""
Chalk Line Timeline Exhibit Engine — Programmatic Courtroom Presentation Builder
Standalone zero-grid companion tool that compiles high-density chat logs and
messaging metadata into a high-contrast centerline timeline exhibit.
"""

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, Flowable
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

from compile_pdf import parse_records

# ── ZoneInfo & Timing ──────────────────────────────────────────────────────────

try:
    from zoneinfo import ZoneInfo
    EASTERN = ZoneInfo("America/New_York")
    _PYTZ = False
except ImportError:
    import pytz as _pytz
    EASTERN = _pytz.timezone("America/New_York")
    _PYTZ = True


def localize_naive(naive_dt: datetime) -> datetime:
    if _PYTZ:
        return EASTERN.localize(naive_dt)         # type: ignore[attr-defined]
    return naive_dt.replace(tzinfo=EASTERN)


def esc(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def minute_key(dt: datetime) -> tuple:
    return (dt.year, dt.month, dt.day, dt.hour, dt.minute)


# ── Paths ─────────────────────────────────────────────────────────────────────

SCRIPT_DIR   = Path(__file__).parent
IMPORT_DIR   = SCRIPT_DIR / "Messenger_Import"
EXHIBITS_DIR = SCRIPT_DIR / "EXHIBITS"


# ── Ingestion Helpers ─────────────────────────────────────────────────────────

def load_rename_map() -> dict:
    rename_map_file = EXHIBITS_DIR / "media" / "rename_map.json"
    if rename_map_file.exists():
        try:
            with open(rename_map_file, encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, json.JSONDecodeError):
            pass
    return {}


def load_annotations() -> dict[tuple, str]:
    annotations_file = IMPORT_DIR / "call_annotations.csv"
    result: dict[tuple, str] = {}
    if not annotations_file.exists():
        return result
    try:
        with open(annotations_file, encoding="utf-8", newline="") as fh:
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


# ── Layout & Typography Constants ─────────────────────────────────────────────

PAGE_W, PAGE_H = letter
SIDE_MARGIN = 54
LATE_NIGHT_HOUR = 21

DARK = colors.HexColor("#1c1e21")
GREY = colors.HexColor("#999999")
SLATE = colors.HexColor("#65676b")

STYLE_CHALK_LEFT = ParagraphStyle("chalk_left", fontName="Helvetica", fontSize=8.5,
                                  leading=11, textColor=DARK, alignment=TA_RIGHT)
STYLE_CHALK_RIGHT = ParagraphStyle("chalk_right", fontName="Helvetica", fontSize=8.5,
                                   leading=11, textColor=DARK, alignment=TA_LEFT)
STYLE_CHALK_DATE = ParagraphStyle("chalk_date", fontName="Helvetica-Bold", fontSize=9,
                                  leading=11, textColor=DARK, alignment=TA_CENTER)
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


# ── Metrics Calculation ───────────────────────────────────────────────────────

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

        if rec["is_jon"]:
            if is_unanswered_call:
                metrics["right_unanswered"] += 1
            elif is_connected_call:
                metrics["left_connected"] += 1
            elif is_media:
                metrics["left_media"] += 1
            else:
                metrics["left_text"] += 1
        else:
            if is_unanswered_call:
                metrics["left_unanswered"] += 1
            elif is_connected_call:
                metrics["right_connected"] += 1
            elif is_media:
                metrics["right_media"] += 1
            else:
                metrics["right_text"] += 1
    return metrics


# ── Cell Creation & Media Embedding ───────────────────────────────────────────

def make_cell(rec: dict, is_left: bool = True) -> Paragraph | list:
    body_style = STYLE_CHALK_LEFT if is_left else STYLE_CHALK_RIGHT
    ts = rec["dt"].strftime("%I:%M %p")

    if rec.get("is_override"):
        html = f'<b>{ts}</b> \u2014 <font color="#D97706"><b>[UNANSWERED CALL]</b></font>'
        return Paragraph(html, body_style)
    elif rec.get("is_call"):
        color = "#0052CC" if is_left else "#DC2626"
        html = f'<b>{ts}</b> \u2014 <font color="{color}"><b>[VIDEO CALL]</b></font>'
        return Paragraph(html, body_style)
    # Expanded media check matching compile_pdf
    filename = rec.get("filename", "")
    ext = Path(filename).suffix.lower() if filename else ""
    is_video = ext in ('.mp4', '.mov', '.avi', '.mkv', '.3gp', '.wmv', '.webm', '.flv', '.m4v')
    is_photo = ext in ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.heic', '.bmp', '.tiff', '.tif')
    is_media_record = rec.get("msg_type") in ("media", "image") or is_video or is_photo

    if is_media_record:
        if filename:
            ts_prefix = f"{ts} \u2014 "
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
                
            if img_path.exists() and img_path.is_file():
                try:
                    img = Image(str(img_path))
                    orig_w = img.imageWidth
                    orig_h = img.imageHeight
                    
                    if orig_w > 0 and orig_h > 0:
                        max_w = 210.0
                        max_h = 140.0
                        scale = min(max_w / orig_w, max_h / orig_h)
                        if scale < 1.0:
                            img.drawWidth = orig_w * scale
                            img.drawHeight = orig_h * scale
                        else:
                            img.drawWidth = orig_w
                            img.drawHeight = orig_h
                        
                    img.hAlign = 'RIGHT' if is_left else 'LEFT'
                    
                    label_html = f"{ts_prefix}<b>{media_type_label}: {filename}</b>"
                    p_flowable = Paragraph(label_html, body_style)
                    
                    return KeepTogether([p_flowable, Spacer(1, 2), img, Spacer(1, 4)])
                except Exception:
                    pass
            else:
                print(f"[DIAGNOSTIC] Asset verification failed. Searched path: {img_path.resolve()}")
            
            # Fallback for missing asset
            label_html = f"{ts_prefix}<b>{media_type_label}: {filename}</b> <font color=\"#DC2626\"><b>[MISSING CACHE REFERENCE]</b></font>"
            return Paragraph(label_html, body_style)
        else:
            label_html = f"{ts} \u2014 <b>IMAGE: attachment missing from export</b>"
            return Paragraph(label_html, body_style)
            
    elif rec.get("msg_type") == "text":
        body_text = '<b>[TEXT]</b>'
        html = f'{ts} \u2014 {body_text}'
        return Paragraph(html, body_style)
    else:
        body_text = esc(rec["content"])
        html = f'{ts} \u2014 {body_text}'
        return Paragraph(html, body_style)


# ── Table Assembly ───────────────────────────────────────────────────────────

def build_table(records: list[dict],
                left_name: str,
                right_name: str) -> Table:
    # Row 0 is an identity header repeated on every page.
    rows: list[list] = [[
        Paragraph(esc(left_name), STYLE_CHALK_LEFT),
        Paragraph("DATE", STYLE_CHALK_DATE),
        Paragraph(esc(right_name), STYLE_CHALK_RIGHT),
    ]]

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

    last_date_str = None

    for idx, rec in enumerate(records):
        date_str = rec["dt"].strftime("%b %d, %Y")

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

        cell = make_cell(rec, is_left=is_left)
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

    table = Table(rows, colWidths=[222, 60, 222], repeatRows=1)
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

def build_pdf(date_from: str | None = None, date_to: str | None = None,
              file_path: str | None = None,
              left_party: str = None,
              right_party: str = None) -> None:
    if file_path is None or left_party is None or right_party is None:
        print("[ERROR] Missing mandatory runtime arguments.")
        sys.exit(1)

    cutoff_from = None
    if date_from:
        try:
            cutoff_from = localize_naive(datetime.strptime(date_from, "%Y-%m-%d"))
            print(f"PDF Filter Active: Compiling records on/after {date_from} (00:00 ET)\n")
        except ValueError:
            print(f"[ERROR] Invalid --date-from '{date_from}'; expected YYYY-MM-DD")
            sys.exit(1)

    cutoff_to = None
    if date_to:
        try:
            cutoff_to = localize_naive(datetime.strptime(date_to, "%Y-%m-%d").replace(hour=23, minute=59, second=59, microsecond=999999))
            print(f"PDF Filter Active: Compiling records on/before {date_to} (23:59 ET)\n")
        except ValueError:
            print(f"[ERROR] Invalid --date-to '{date_to}'; expected YYYY-MM-DD")
            sys.exit(1)

    input_file = resolve_input_file(file_path)
    if input_file is None:
        sys.exit(1)

    rmap        = load_rename_map()
    annotations = load_annotations()

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

    # For sender parsing, always match against the actual detected JSON participants.
    # The visual presentation, stats, and headers will use left_party and right_party.
    parse_left_name = detected_left or left_party
    parse_right_name = detected_right or right_party

    records = parse_records(input_file, annotations, rmap,
                            left_name=parse_left_name, right_name=parse_right_name)

    # Date interception: drop any record outside date boundaries
    if cutoff_from is not None:
        records = [r for r in records if r["dt"] >= cutoff_from]
    if cutoff_to is not None:
        records = [r for r in records if r["dt"] <= cutoff_to]

    late = sum(1 for r in records
               if not r["is_jon"] and r["dt"].hour >= LATE_NIGHT_HOUR)
    print(f"Compiling {len(records):,} records "
          f"({late} late-night inbound highlighted).")

    EXHIBITS_DIR.mkdir(parents=True, exist_ok=True)
    output_pdf_path = EXHIBITS_DIR / "timeline_exhibit_chalk_line.pdf"

    doc = SimpleDocTemplate(
        str(output_pdf_path), pagesize=letter,
        leftMargin=SIDE_MARGIN, rightMargin=SIDE_MARGIN,
        topMargin=54, bottomMargin=54,
        title="Facebook Messenger Timeline Exhibit",
    )

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
    stats_table = Table(stats_data, colWidths=[222, 60, 222])
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
        build_table(records, left_name=left_party, right_name=right_party),
    ]
    doc.build(elements, canvasmaker=NumberedCanvas)
    print(f"PDF saved: {output_pdf_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chalk Line Forensic PDF timeline exhibit builder")
    parser.add_argument("--date-from", type=str, default=None,
                        help="Filter records starting from this date in YYYY-MM-DD format")
    parser.add_argument("--date-to", type=str, default=None,
                        help="Filter records ending at this date in YYYY-MM-DD format")
    parser.add_argument("-f", "--file", type=str, required=True,
                        help="Path to the target raw Messenger JSON export file")
    parser.add_argument("--left-party", type=str, required=True,
                        help="Explicit name string of the outbound/left-column participant")
    parser.add_argument("--right-party", type=str, required=True,
                        help="Explicit name string of the inbound/right-column participant")
    args = parser.parse_args()
    build_pdf(date_from=args.date_from, date_to=args.date_to, file_path=args.file,
              left_party=args.left_party, right_party=args.right_party)
