# Technical Specifications & Legal Audit Framework: compile_pdf.py

## 1. Executive Architecture Overview

`compile_pdf.py` is the print-matrix generator for the Messenger forensic exhibit suite. It ingests unified data layers—raw Meta export JSON (resolved at runtime inside `Messenger_Import`), the media rename manifest, and the call annotation override CSV—and compiles them into a multi-page, text-only PDF artifact (`EXHIBITS/timeline_exhibit.pdf` or `EXHIBITS/timeline_exhibit_chalk_line.pdf`) optimized for legal binders, hole-punch margins, and courtroom handoff.

The script performs five sequential operations on each execution under the layout and metrics specification:

1. **Resolve** the target JSON export via explicit path or automatic directory discovery inside `Messenger_Import`.
2. **Normalize** all record timestamps to Eastern wall-clock time (`America/New_York`).
3. **Apply** the 5-part minute-tuple override engine for unanswered call milestones with parameterized identity routing.
4. **Filter** optionally via `--date-from` CLI boundary before table assembly.
5. **Render** a programmatic ReportLab layout into `EXHIBITS/timeline_exhibit.pdf` (or `EXHIBITS/timeline_exhibit_chalk_line.pdf`) with parameter-driven identity headers and executive metrics.

### Algorithmic Isolation from `core/parse_calls.py`

| Property | `core/parse_calls.py` | `compile_pdf.py` |
|---|---|---|
| Import dependency | None (does not import sibling script) | None |
| Output artifact | `EXHIBITS/timeline_report.html` | `EXHIBITS/timeline_exhibit.pdf` |
| Media disk mutation | Renames UUID files; optional cleanup sweep | **No** file renames or isolation sweeps |
| Thumbnail generation | Optional OpenCV | Not used |
| Shared logic | Parallel reimplementation of ingestion, timezone, override matching, path resolution, identity routing | Same forensic rules, independent code path |

This decoupling ensures PDF compilation failures, layout experiments, or print-queue regressions cannot alter HTML generation behavior or on-disk media state managed by the primary parser.

### Foundational Tech Stack

| Layer | Components | Role |
|---|---|---|
| Core ingestion | Python 3.9+ stdlib: `json`, `csv`, `datetime`, `argparse`, `pathlib` | Record parsing, CLI filtering, path resolution, identity routing |
| Timezone engine | `zoneinfo.ZoneInfo` (stdlib) | Primary `America/New_York` localization with automatic DST |
| Timezone fallback | `pytz` (optional, if `zoneinfo` unavailable) | Legacy interpreter compatibility via `localize_naive()` |
| PDF engine | **ReportLab 4.5.1+** (`reportlab`) | `BaseDocTemplate`, `LongTable`, `Paragraph`, `TableStyle`, custom `Canvas` |

**Dependency posture:** All forensic parsing and filtering logic executes on stdlib modules. ReportLab is required exclusively for PDF vector layout and pagination; it does not participate in timestamp normalization or override resolution.

---

## 2. Page Geometry & Layout Architecture

### 2.1 Page Constraints

| Parameter | Value | Derivation |
|---|---|---|
| Page size | US Letter | `letter` = 612 × 792 pt |
| Left margin | 54 pt (0.75 in) | `SIDE_MARGIN` |
| Right margin | 54 pt (0.75 in) | `SIDE_MARGIN` |
| Top margin | 54 pt | `BaseDocTemplate(topMargin=54)` |
| Bottom margin | 54 pt | Reserved for footer band (`NumberedCanvas` draws at y=30–40) |
| Content frame width | 504 pt | `612 − (2 × 54)` |
| Content frame height | 684 pt | `792 − (2 × 54)` |

Margins are hard-coded to preserve binding clearance and standard three-hole punch zones on physical exhibits.

### 2.2 The 3-Column Grid

Column widths and geometry are determined dynamically at runtime based on the compilation mode:

#### Standard Layout Matrix
- **Left (Col 0)**: **198 pt** (outbound records; 2 pt `LINEBEFORE` blue `#0084ff`).
- **Center (Col 1)**: **108 pt** (date string only; deduplicated inline).
- **Right (Col 2)**: **198 pt** (inbound records; 2 pt `LINEAFTER` slate `#65676b`).

#### Chalk Line Presentation Layout Matrix
- **Left (Col 0)**: **222 pt** (outbound left entries; right-aligned to push cleanly toward the center axis; features a 2 pt `#0052CC` right-side cell highlight accent).
- **Center (Col 1)**: **60 pt** (empty space forming a tight vertical axis track; no vertical center divider lines are drawn to preserve a clean white space division).
- **Right (Col 2)**: **222 pt** (inbound right entries; left-aligned to pull cleanly away from the center axis; features a 2 pt `#DC2626` left-side cell highlight accent).

**Width invariant (both modes):**
```text
Standard:    198 + 108 + 198 = 504 pt
Chalk Line:  222 +  60 + 222 = 504 pt
SIDE_MARGIN = (PAGE_W − 504) / 2 = 54 pt
```

Each record occupies exactly one data row. Column boundaries separate outbound and inbound event states without ambiguous labels.

---

### 2.3 Repeating Identity Headers

The timeline body is a ReportLab `LongTable` with `repeatRows=1`. Row 0 is a persistent identity header reprinted at the top of every page after a page break. Header labels are **not hardwired**; they are injected at build time from CLI identity parameters.

```python
rows = [[
    Paragraph(esc(left_name), STYLE_HDR_L),
    Paragraph("DATE", STYLE_HDR_C),
    Paragraph(esc(right_name), STYLE_HDR_R),
]]
```

| Header Cell | Content Source | Style | Alignment |
|---|---|---|---|
| Col 0 | `--left-party` value (required) | `STYLE_HDR_L` (Helvetica-Bold 9pt, blue) | Left |
| Col 1 | Static `"DATE"` | `STYLE_HDR_C` (Helvetica-Bold 9pt) | Center |
| Col 2 | `--right-party` value (required) | `STYLE_HDR_R` (Helvetica-Bold 9pt, slate) | Right |

`build_table(records, left_name=..., right_name=...)` receives the resolved identity strings from `build_pdf()` and passes them directly into Row 0. Changing `--left-party` or `--right-party` at the CLI updates every repeated header on every page without altering column widths or date deduplication logic.

**Header separator:** `LINEBELOW` on row 0 at **1.5 pt** solid dark (`#1c1e21`), distinct from the 0.25 pt data-row dividers below.

Data rows begin at index `r = idx + 1` in `TableStyle` commands to account for the header offset.

---

## 3. Typographic Hierarchy & Visual Priority Drivers

### 3.1 Timestamp Priority Layer

Execution time is the primary judicial focal point. Timestamps lead every populated left/right cell, formatted as bold inline HTML within a single `Paragraph`:

```python
html = f'<b>{ts}</b> \u2014 {esc(rec["content"])}'
# ts = rec["dt"].strftime("%I:%M %p")  -> zero-padded, e.g. "07:22 PM"
```

| Element | Font | Size | Weight | Example |
|---|---|---|---|---|
| Timestamp prefix | Helvetica (via `<b>`) | 8.5 pt | Bold | `07:22 PM` |
| Em-dash separator | Helvetica | 8.5 pt | Regular | `—` (U+2014, WinAnsi-safe) |
| Body content | Helvetica | 8.5 pt | Regular | `Video Call Log Entry (Platform Metadata Trace)` |
| Override footnote | Helvetica-Oblique | 6.5 pt | Italic | `*Status verified via cross-referenced local history logs*` |

The timestamp and body share the same paragraph style container (`STYLE_OUT` / `STYLE_IN`, 8.5 pt, leading 11 pt) with left alignment for outbound and right alignment for inbound. Bold markup on the timestamp alone establishes visual hierarchy without a separate column or iconography.

### 3.2 Center-Column Date Deduplication

The table builder maintains a running state variable independent of identity configuration:

```python
last_date_str = None
date_str = rec["dt"].strftime("%b %d, %Y")   # e.g. "May 30, 2026"
if date_str == last_date_str:
    center = ""
else:
    center = Paragraph(esc(date_str), STYLE_DATE)
    last_date_str = date_str
```

| Compilation Mode | First Row of Day Behavior | Subsequent Rows Behavior | Row Structure |
|---|---|---|---|
| **Standard Layout** | Center cell (Col 1) renders formatted date (Helvetica 7.5 pt, centered) | Center cell is empty string `""` | Deduplicated inline within the first message row of that calendar day. |
| **Chalk Line Layout** | Appends a dedicated chronological date row spanning all three columns: `('SPAN', (0, r), (2, r))` | No date row is appended | Horizon-breaker row that interrupts the vertical centerline spine. |

This suppresses repetitive date labels within single-day activity clusters and structures dates as clean chronological separators.

### 3.3 Global Video Call Highlighting Matrix

Background fills are applied per data row via dynamic `TableStyle` commands during the build loop. Precedence is evaluated in strict order:

```
if late_inbound OR is_override:
    -> AMBER (#FEF3C7)          [priority tier]
elif is_call:
    -> CALL_TINT (#E2E8F0)      [standard call tier]
else:
    -> no background fill
```

| Condition | Flag / Rule | Fill Color | Hex |
|---|---|---|---|
| Verified unanswered override | `rec["is_override"] == True` | Priority amber | `#FEF3C7` |
| Inbound late-night (>= 21:00 ET) | `not is_jon` and `dt.hour >= 21` | Priority amber | `#FEF3C7` |
| Standard video call log | `rec["is_call"] == True` (and not amber tier) | Professional grey/blue | `#E2E8F0` |
| Text / media / other | Default | None (white) | — |

**Precedence rule:** Amber always wins. An unanswered override milestone (`is_override`) receives amber even if it would otherwise qualify for the call tint. A late-night inbound call receives amber over the standard call tint.

Side accent lines (blue left / slate right) apply independently of background fill and are unaffected by highlight tier.

### 3.4 Media Payload Format

Images and video binaries are stripped from the PDF. Media records render as wrapped text only:

```
07:30 PM — [MEDIA EXHIBIT: 2026-05-25_19-30-20.jpeg]
```

Filenames resolve through `media/rename_map.json` with a timestamp-derived fallback when a UUID key is absent from the map.

### 3.5 Call Payload Markers

| Record class | Content string | Marker |
|---|---|---|
| Standard call log | `Video Call Log Entry (Platform Metadata Trace)` | None |
| Unanswered override | `[CALL] Facebook Video Call — Unanswered` | ASCII `[CALL]` prefix |

Directional ASCII arrows (`>>`, `<<`) are not rendered in the current layout; column placement conveys authorship. The `[CALL]` prefix identifies CSV-verified unanswered milestones in print.

### 3.6 Chalk Line Presentation Mode Matrix

When the `--chalk-line` command-line flag is set, it dynamically intercepts the paragraph compilation engine within `make_cell()`. This mode overrides the standard visual output format to present a high-contrast centerline layout utilizing simplified, high-density file names and direct referencing without visual clutter.

The engine processes and reformats raw record content deterministically according to the following layout-driven routing rules:

| Original Record Class / Context | Dynamic Text Refactoring Format | Formatting Rules & Transformation Behavior |
| :--- | :--- | :--- |
| **Regular Text Message** | `<b>[TEXT]</b>` | Completely strips the message body text and outputs a static, content-free label to collapse cells and maximize vertical timeline density. |
| **Image / Photo Payload** | `<b>IMAGE: filename.ext</b>` followed by inline thumbnail | Discards generic placeholder text. Extracts the physical filename and appends a defensively scaled (Max: 120x80pt) inline image, matching the column cell alignment (right-aligned for Left, left-aligned for Right) to stack vertically inside the cell. |
| **Video Payload** | `<b>VIDEO: filename.mp4</b>` | Extracts the explicit resolved file name (typically `.mp4` or other video formats) and outputs the specific filename directly as bold labeled text (no angle brackets). |
| **Video Call (Connected)** | `<b>[VIDEO CALL]</b>` | Replaces the metadata/log details and outputs strictly as bold brackets. |
| **Unanswered Video Call** | `<b>[UNANSWERED CALL]</b>` | Output is strictly bold brackets. Any corresponding multi-line footnotes and status trace blocks are stripped completely. |

---

## 4. Ingestion, Filtering, & Dynamic Aggregation

All runtime configuration is registered via `argparse` in the `__main__` block and passed into `build_pdf(date_from, file_path, left_name, right_name)`.

### 4.1 Comprehensive CLI Argument Interface

| Flag | Type | Default | Description |
|---|---|---|---|
| `-f` / `--file` | `str` | `None` | Path to target Messenger JSON export |
| `--date-from` | `str` | `None` | Include records on/after this date (`YYYY-MM-DD`, midnight ET) |
| `--left-party` | `str` | `None` (Required) | Left-column header label and outbound identity string |
| `--right-party` | `str` | `None` (Required) | Right-column header label and inbound identity string |
| `--chalk-line` | `bool` (flag) | `False` | A boolean presentation toggle that converts standard message body payloads into a high-density, text-annotated forensic timeline. It shifts text rows into explicit bracket blocks, extracts exact filenames for image/video assets, and prepends visual warning markers (🚨) to call executions. |

```powershell
python .\compile_pdf.py --help
```

### 4.2 Input Resolution: `resolve_input_file()`

The PDF engine mirrors the path resolution architecture implemented in `core/parse_calls.py`. When `--file` is supplied:

```python
p = Path(file_arg)
target = p if p.is_absolute() else IMPORT_DIR / p
if target.exists() and target.is_file():
    return target
print(f"[ERROR] Specified file does not exist or is not a file: '{file_arg}'")
return None
```

**Auto-discovery fallback** (when `--file` is omitted):

```python
EXCLUDED_JSON_NAMES = {"rename_map.json"}
json_files = sorted([
    f for f in IMPORT_DIR.glob("*.json")
    if f.name not in EXCLUDED_JSON_NAMES
])
```

| Discovery outcome | Behavior |
|---|---|
| **Zero files** | Print `[ERROR] No Messenger JSON export found in the import directory.`; graceful exit |
| **Exactly one file** | Auto-select; print `No input file specified. Defaulting to discovered file: [Filename]` |
| **Multiple files** | Deterministic `sorted()` order; select index 0; print `[WARN]` with filename and enumerate alternatives |

The scan is **shallow** (`IMPORT_DIR.glob("*.json")` only). Subdirectory manifests such as `media/rename_map.json` are excluded by depth and by the name filter.

Resolved path flows into `parse_records(input_file, annotations, rmap, left_name=..., right_name=...)`.

### 4.3 Unified Data Layer Ingestion

| Source File | Access Mode | Function |
|---|---|---|
| Messenger JSON export (`Messenger_Import/*.json`) | Read-only UTF-8 | `parse_records()` — message traversal, identity routing, sort |
| `Messenger_Import/call_annotations.csv` | Read-only UTF-8 | `load_annotations()` — minute-tuple override map |
| `EXHIBITS/media/rename_map.json` | Read-only UTF-8 | `load_rename_map()` — exhibit filename resolution |

**Internal record schema** (post-parse):

| Key | Type | Description |
|---|---|---|
| `ts_ms` | `int` | Raw epoch milliseconds |
| `dt` | `datetime` | Eastern-localized wall clock |
| `is_jon` | `bool` | Left-column flag (outbound relative to `--left`) |
| `content` | `str` | Rendered cell body (after timestamp prefix) |
| `footnote` | `str` | Override legal note (optional) |
| `is_call` | `bool` | Video call log row |
| `is_override` | `bool` | CSV-verified unanswered milestone |

**Identity routing** in `parse_records()`:

```python
raw_sender = fix_encoding(msg.get("senderName", ""))
is_jon     = is_left_sender(raw_sender, left_name)
```

`is_left_sender()` applies case-insensitive matching against `--left-party`.

Records sort reverse-chronologically: `records.sort(key=lambda r: r["ts_ms"], reverse=True)`.

### 4.4 Temporal Filter Layer

**Cutoff resolution** (at top of `build_pdf()`, before path resolution completes ingestion):

```python
cutoff_dt = localize_naive(datetime.strptime(date_from, "%Y-%m-%d"))
# Midnight (00:00:00) Eastern on the specified calendar date
```

**List comprehension filter** (after `parse_records()` returns the sorted list, before table generation):

```python
if cutoff_dt is not None:
    records = [r for r in records if r["dt"] >= cutoff_dt]
```

| Property | Behavior |
|---|---|
| Timezone engine | `localize_naive()` — identical to ingestion-side Eastern localization |
| Comparison | Strict `>=` against midnight Eastern |
| Records on cutoff date | Included |
| Execution point | After full parse and sort; before `compute_metrics()` and `build_table()` |
| Invalid `--date-from` | `[ERROR]` message; early return; no PDF write |

Unlike `core/parse_calls.py`, no media cleanup or disk mutation occurs regardless of filter state—the PDF engine never relocates binary assets.

Console output reflects the filtered set:

```
Compiling N records (X late-night inbound highlighted).
```

### 4.5 Page 1 Executive Metrics Summary & Forensic Ingestion Matrix

After filtering, `compute_metrics()` aggregates categorical counts from the final `records` list:

```python
def compute_metrics(records: list[dict]) -> dict[str, int]:
    # left_text, left_media, left_connected, left_unanswered
    # right_text, right_media, right_connected, right_unanswered
```

#### Ingestion Rules & Metric Crediting Matrix

Category derivation is performed under the following rules:

* **Sender-Based Ingestion (Initiator)**:
  * **Text Messages**: Credited strictly to the sending/initiating party (`is_jon` polarity; not `is_call`; content does not start with `[MEDIA EXHIBIT:`).
  * **Media Exhibits**: Credited strictly to the sending/initiating party (`content.startswith("[MEDIA EXHIBIT:")` by column polarity).
  * **Connected Video Calls**: Tallied and credited to the party who initiated/sent the record (`is_call == True` and `is_override == False` by column polarity).
* **Recipient-Based Ingestion (Recipient)**:
  * **Unanswered Video Calls**: Tallied and credited strictly to the **recipient party** (destination) to ensure correct personal missed-call counts (`is_call == True` and `is_override == True` with reversed polarity: if initiated by left, credited to right; if initiated by right, credited to left).

#### Top Statistics Panel Layout & Typographic Hierarchy

An executive stats table (`stats_table`) is drawn on Page 1 utilizing a dual-column split metrics grid:

* **Grid Geometry & Layout**:
  * Set as a `LongTable` with column widths `[222, 60, 222]`, splitting the page content width symmetrically.
* **Typography and Styling**:
  * All labels and counts are rendered in high-visibility dark text on the PDF canvas.
* **Mirrored Alignment Rules**:
  * Left Party cells (`STYLE_STATS_L`) are right-aligned to anchor inward flush against the center centerline division track.
  * Right Party cells (`STYLE_STATS_R`) are left-aligned to pull cleanly away from the track.
  * This matches the centerline visual spine division of the main timeline.

#### Dynamic Date Bounds Extraction

During compilation, the engine dynamically evaluates the sorted array boundaries (`records[-1]` and `records[0]`) to extract the absolute earliest and latest records:
* Emits a formatted date bounds string, e.g. `"Timeline Scope: [Start Date] to [End Date]"`, which is drawn as a dedicated metadata line inside the subheader on Page 1.

**Page 1 element stack** (all derived from filtered `records`):

| Block | Source | Filter-aware | Identity-aware |
|---|---|---|---|
| Document title | Static | — | — |
| Parties line | `{left_name} & {right_name}` | — | Yes |
| Source / Total / Generated | `input_file.name`, `len(records)`, runtime stamp | Yes (count) | — |
| Executive metrics summary | `stats_table` (ReportLab `LongTable`) | Yes | Yes |
| Timeline table | `build_table()` | Yes | Yes (Row 0 headers) |

---

## 5. Forensic Integrity & Layout Verification Checklist

### 5.1 Two-Pass Page Numbering

The custom `NumberedCanvas` subclass implements a deferred footer draw:

```
Pass 1 (build):  showPage() -> save canvas state to _saved_states[]
Pass 2 (save):   for each saved state -> restore -> draw footer -> emit page
```

| Footer Element | Position | Content |
|---|---|---|
| Rule line | y = 40 pt | 0.5 pt stroke `#dddfe2`, spanning content width |
| Confidentiality stamp | Left, y = 30 pt | `CONFIDENTIAL — Facebook Messenger Forensic Timeline Exhibit` |
| Page numbering | Right, y = 30 pt | `Page {n} of {total}` |

Total page count (`total = len(self._saved_states)`) is known only after the full document flow completes. The two-pass mechanism prevents under-counted or placeholder footers and ensures every sheet—including the last—carries an authoritative page denominator.

**Auditor action:** Open `EXHIBITS/timeline_exhibit.pdf` (or `EXHIBITS/timeline_exhibit_chalk_line.pdf`), verify sequential `Page X of Y` on every sheet, confirm `X` on the final page equals `Y`.

### 5.2 Text Wrapping & Overflow Prevention

All message payloads are encapsulated in ReportLab `Paragraph` objects placed inside fixed-width `LongTable` cells:

| Column | Width | Wrap behavior |
|---|---|---|
| Left / Right | 198 pt each | `Paragraph` auto-wraps within cell; `VALIGN=TOP` |
| Center | 108 pt | Date `Paragraph` or empty string |

Long strings (media exhibit paths, call log labels, override footnotes) wrap to additional lines within the cell boundary rather than clipping at column edges or overflowing into adjacent columns.

**Auditor action:** Inspect rows containing long `[MEDIA EXHIBIT: ...]` paths; confirm no horizontal truncation or column bleed in Adobe Acrobat, Chrome PDF viewer, and a commercial print proof.

### 5.3 Encoding & Font Safety

| Property | Implementation |
|---|---|
| Font family | Built-in PDF core fonts: Helvetica, Helvetica-Bold, Helvetica-Oblique |
| Font embedding | None required; standard 14 PDF fonts |
| Unicode strategy | WinAnsi-safe body text; em-dash (`—`) via `\u2014` |
| Markers | ASCII `[CALL]` prefix for unanswered overrides |
| Emoji / color glyphs | Not used in PDF output (prevents tofu boxes) |

Entity escaping (`esc()`) sanitizes `&`, `<`, `>` in all user-derived strings—including `--left` and `--right` values—before `Paragraph` rendering.

**Auditor action:** Search the PDF for empty rectangle (tofu) artifacts. Confirm all timestamps, call labels, and media exhibit strings render as readable text across at least two independent PDF viewers.

### 5.4 Structural Integrity: Layout Independence from Identity Vectors

Column geometry and date deduplication operate on **record timestamps and boolean column flags only**. They do not read or branch on `--left` / `--right` string values.

**Verification criteria:**

| Layout subsystem | Governing constants / state | Identity-dependent? |
|---|---|---|
| Column widths | `[COL_LEFT, COL_CENTER, COL_RIGHT] = [198, 108, 198]` | **No** — hard-coded in `LongTable(colWidths=...)` |
| Center date deduplication | `last_date_str` compared against `rec["dt"].strftime("%b %d, %Y")` | **No** — evaluates datetime only |
| Row highlight tiers | `is_jon`, `is_call`, `is_override`, `dt.hour` | **No** — boolean/time flags, not label strings |
| Side accent lines | `is_jon` -> blue `LINEBEFORE` or slate `LINEAFTER` | **No** |
| Header Row 0 labels | `left_name`, `right_name` | **Yes** — display only |
| Executive metrics labels | `left_name`, `right_name` in metrics stats table | **Yes** — display only |

**Auditor action:**

```powershell
# Baseline PDF with default identities (using auto-detection fallback or required flags)
python .\compile_pdf.py -f "input_export.json" --left-party "John Doe" --right-party "Jane Doe" --date-from 2026-05-01

# Same filter, custom identity labels — record count and row count must match
python .\compile_pdf.py -f "input_export.json" --date-from 2026-05-01 `
  --left-party "OUTBOUND PARTY" --right-party "INBOUND PARTY"
```

Confirm: identical console record count; identical number of data rows; identical center-column date suppression pattern; only header text, parties line, and metrics labels change.

### 5.5 Source Immutability & Determinism

| Asset | Read | Write |
|---|---|---|
| Messenger JSON export (`Messenger_Import/*.json`) | Yes | **No** |
| `Messenger_Import/call_annotations.csv` | Yes | **No** |
| `EXHIBITS/media/rename_map.json` | Yes | **No** |
| `EXHIBITS/timeline_exhibit.pdf` (or `EXHIBITS/timeline_exhibit_chalk_line.pdf`) | — | Yes (output only) |
| `EXHIBITS/media/*` binary files | Yes (referenced for inline thumbnails) | **No** |

**Non-deterministic elements:**

| Element | Cause |
|---|---|
| `Generated:` timestamp on Page 1 | Runtime `datetime.now(tz=EASTERN)` |
| Page count | Varies with `--date-from` filter scope and content length |

**Deterministic elements** (given identical source files and CLI arguments):

- Record inclusion set and sort order
- Override resolution (minute-tuple matching)
- Column placement (`is_jon`) for a fixed `--left-party` matching configuration
- Row highlight tier assignment
- Date deduplication pattern
- Column width geometry

**Auditor action:** Compute SHA-256 of source JSON and CSV before and after PDF compilation; hashes must be identical. Re-run with identical CLI flags; verify identical record count in console output and identical row count in the PDF table body.

### 5.6 XML Safety and Column Constancy Verification

Auditing the layout integrity under high-density chalk-line presentation mode requires verifying that neither long raw filesystem filenames nor the escaped HTML entities break the PDF formatting.

**Audit Action Checklist:**
1. **XML Syntax Verification**: Execute the script with the `--chalk-line` option active. The absence of compilation errors confirms that all dynamic strings and escaped characters are safely parsed, preventing compiler exceptions.
2. **Column Constancy and Auto-Wrapping**: Open the generated `EXHIBITS/timeline_exhibit.pdf` (or `EXHIBITS/timeline_exhibit_chalk_line.pdf`) and locate records with long on-disk filenames (e.g., 36-character UUID filenames or long timestamp prefixes). Confirm that:
   - The cell contents wrap onto subsequent lines cleanly within the allocated column width boundary of **198 pt** (Col 0 and Col 2).
   - Column widths do not expand dynamically or shrink adjacent columns. The centerline column width remains strictly **108 pt**.
   - No text bleeds or overlaps across grid lines.
3. **Canvas Bounds Enforcement**: Ensure that multi-line wrapped text rows near the page break correctly flow onto the next page instead of overflowing the bottom margin boundary. Verify that the two-pass `NumberedCanvas` footer remains isolated and draws at exactly y = 30–40 pt without vertical collision.

---

## Execution Reference

```powershell
# Specifying mandatory arguments (using auto-discovery fallback or required flags)
python .\compile_pdf.py -f "input_export.json" --left-party "John Doe" --right-party "Jane Doe"

# Filtered compile from a start date (midnight Eastern)
python .\compile_pdf.py -f "input_export.json" --left-party "John Doe" --right-party "Jane Doe" --date-from 2026-05-01

# Custom party identities
python .\compile_pdf.py -f "input_export.json" --left-party "John Doe" --right-party "Jane Doe"

# Chalk-line presentation mode with custom bounds
python .\compile_pdf.py -f "input_export.json" --left-party "John Doe" --right-party "Jane Doe" --date-from 2026-05-01 --chalk-line

# Composite courtroom presentation layout command
python .\compile_pdf.py -f "input_export.json" --date-from 2026-05-25 --chalk-line --left-party "JOHN DOE" --right-party "JANE DOE"

# Combined configuration
python .\compile_pdf.py -f "input_export.json" --date-from 2026-05-01 `
  --left-party "JOHN DOE" --right-party "JANE DOE"

# Full argument reference
python .\compile_pdf.py --help
```

**Prerequisite:** `pip install reportlab` (4.5.1+ tested).

**Recommended pipeline:**

```powershell
# Step 1: Establish media rename map and HTML exhibit (using compile_html.py)
python .\compile_html.py -f "input_export.json" --left-party "John Doe" --right-party "Jane Doe" --date-from 2026-05-01

# Step 2: Compile print-ready PDF from the same source layers and matching CLI flags
python .\compile_pdf.py -f "input_export.json" --left-party "John Doe" --right-party "Jane Doe" --date-from 2026-05-01
```

---

## Directory Layout

```text
messenger-logs/
├── documentation/
├── EXHIBITS/               # Generated workspace (PDFs, HTML, mirrored media cache)
│   └── media/
│       ├── thumbnails/
│       └── rename_map.json
└── Messenger_Import/       # Pristine, read-only forensic source
    └── media/
    └── input_export.json
```
