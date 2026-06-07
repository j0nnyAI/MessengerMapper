# Technical Specifications & Legal Audit Framework: core/parse_calls.py (v3)

## 1. Executive Architecture Overview

`core/parse_calls.py` is a generalized forensic ingestion engine for standardized Meta/Facebook Messenger JSON export payloads. Under **version v3**, it transforms platform-native message objects into a normalized, reverse-chronological communication timeline suitable for technical peer review, cross-examination preparation, and judicial presentation.

Unlike a single-case hardcoded utility, the interactive HTML exhibit engine wrapper `compile_html.py` (which runs the core ingestion engine under the hood) accepts **runtime CLI parameters** that substitute the input export file, temporal filter boundary, and left/right party identity labels without modifying core parsing algorithms. Any compliant Messenger export that exposes a top-level `messages[]` array, millisecond `timestamp` fields, and `senderName` attribution strings can be processed by supplying the appropriate `-f`, `--left-party`, and `--right-party` values at execution time under the v3 specification.

The script performs four deterministic operations on each execution:

1. **Resolve** the target JSON export via explicit path or automatic directory discovery inside `Messenger_Import`.
2. **Parse** messages and emit a typed record list (text, media, call/link events) with parameterized column identity.
3. **Normalize** all timestamps to Eastern wall-clock time (`America/New_York`) and overlay independent call-status annotations from a headerless CSV manifest inside `Messenger_Import`.
4. **Render** an isolated HTML exhibit (`EXHIBITS/timeline_report.html`) without mutating any files in `Messenger_Import`.

A companion script, `compile_pdf.py`, consumes the same source layers to produce a print-optimized PDF exhibit (`timeline_exhibit.pdf`). That pipeline is documented in [README_compile_pdf.md](README_compile_pdf.md); this specification covers `core/parse_calls.py` and the `compile_html.py` wrapper.

### Foundational Tech Stack

| Layer | Components | Role |
|---|---|---|
| Core parsing | Python 3.9+ stdlib: `json`, `csv`, `datetime`, `argparse`, `pathlib`, `html`, `shutil`, `webbrowser` | Message traversal, annotation loading, CLI filtering, path resolution, HTML emission |
| Timezone engine | `zoneinfo.ZoneInfo` (stdlib, Python 3.9+) | Primary `America/New_York` localization with automatic DST handling |
| Timezone fallback | `pytz` (optional, only if `zoneinfo` unavailable) | Legacy interpreter compatibility |
| Thumbnail generation | `opencv-python` (optional) | First-frame video capture into `EXHIBITS/media/thumbnails/`; parsing proceeds without it |

**Dependency posture:** All record parsing, sorting, override matching, identity routing, and HTML assembly logic executes exclusively on stdlib modules. Optional packages (`pytz`, `opencv-python`) affect timezone bootstrap or thumbnail enrichment only; they do not alter record counts, sort order, or override resolution when absent.

---

## 2. Ingestion & Data Layer Mapping

### 2.1 Primary Source: Messenger JSON Export

The target export is resolved at runtime (see Section 4) and opened read-only (`encoding="utf-8"`) via `json.load()`. The parser traverses the top-level `messages` array sequentially.

| JSON Field | Parser Usage | Notes |
|---|---|---|
| `messages[]` | Iteration root | Non-dict entries are skipped with a warning |
| `timestamp` | `int(msg["timestamp"])` | Unix epoch **milliseconds**; invalid/missing values skip the message |
| `senderName` | Identity attribution | Passed through `fix_encoding()`; routed to left or right column via `is_left_sender(raw_sender, left_name)` |
| `type` | Record classifier | `"text"`, `"media"`, `"link"`, or fallback unknown handler |
| `text` | Message body | Passed through `fix_encoding()` before storage |
| `media[]` | Attachment list | One output record per attachment object; empty list -> single "missing attachment" record |
| `media[].uri` | File reference | Normalized to relative `media/<filename>` via `normalize_uri()` |
| `isUnsent` | Retraction flag | Preserved on record as `unsent: bool`; rendered in HTML as `[RECORD RETRACTED BY SENDER]` |

**Encoding correction:** All string fields (`senderName`, `text`, attachment URIs) pass through `fix_encoding()`, which reverses Meta's common latin-1/utf-8 double-encoding (`s.encode("latin-1").decode("utf-8")`). On failure, the original string is retained unchanged—no silent truncation or field dropping occurs.

**Record emission schema** (internal, frozen):

| Key | Type | Description |
|---|---|---|
| `ts_ms` | `int` | Raw epoch milliseconds from JSON |
| `local_dt` | `datetime` | Eastern-localized wall clock |
| `itype` | `str` | Interaction type label (e.g., `Text Message`, `Facebook Video Call Log`) |
| `is_jon` | `bool` | Left-column flag (outbound relative to `--left` identity) |
| `sender` | `str` | Display label (`left_name` or `right_name` from CLI) |
| `content` | `str` | Rendered body or call label |
| `footnote` | `str` | Optional legal annotation (override records only) |
| `uri` | `str` | Renamed media path (media records only) |
| `unsent` | `bool` | Retraction state |
| `thumb_uri` | `str` | Thumbnail path (video records, when OpenCV available) |

### 2.2 Override Manifest: `call_annotations.csv`

Loaded by `load_annotations()` as a **positional, headerless** CSV. No column headers are assumed or required.

| Column Index | Field | Example | Required |
|---|---|---|---|
| 0 | Date | `2026-05-25` | Yes |
| 1 | Time | `7:22 PM` | Yes |
| 2 | Override type | `unanswered` | Yes |
| 3 | Notes | `Verified via local device history logs` | No |

**Accepted time formats** (parsed in order):

- `%Y-%m-%d %I:%M %p` — e.g., `2026-05-25 7:22 PM`
- `%Y-%m-%d %I:%M%p` — e.g., `2026-05-257:22PM`
- `%Y-%m-%d %H:%M` — e.g., `2026-05-25 19:22`

Each valid row is localized to Eastern time via `_localize_naive()` and stored in memory as:

```python
{_local_minute_key(local_dt): {"override_type": str, "notes": str}}
```

**Critical constraint:** The CSV can only **modify** existing JSON `link`-type records. It cannot inject new timeline rows. Malformed rows are skipped with a console `[WARN]` and do not halt execution.

### 2.3 Media Asset Registry: `EXHIBITS/media/rename_map.json`

Persistent JSON object mapping original Meta UUID filenames to deterministic forensic signatures.

| Key | Value | Example |
|---|---|---|
| Original basename | Renamed relative URI | `"344f3fa4-5e94-47d4-833b-e107b289dc9d.mp4"` -> `"media/2025-06-01_19-53-25.mp4"` |

**Mirroring & Rename algorithm** (`_rename_media()`):

1. If the original basename exists in the map -> return the stored path (idempotent re-run).
2. If the source file is absent in `Messenger_Import/` -> return the original URI unchanged.
3. Otherwise, copy to `EXHIBITS/media/YYYY-MM-DD_HH-MM-SS.ext` (Eastern local time of the message) using `shutil.copy2`.
4. On same-second collision, append `_1`, `_2`, … until a free filename is found.
5. Persist the mapping to `EXHIBITS/media/rename_map.json` at end of parse.

The map serves as the authoritative provenance chain between platform UUIDs and human-readable exhibit filenames.

---

## 3. Computational Logic & Chronological Normalization

### 3.1 Timezone Normalization Vector

All temporal operations follow a single pipeline:

```
timestamp (ms) -> UTC datetime -> astimezone(America/New_York) -> local_dt
```

Implementation (`ts_to_eastern()`):

```python
datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc).astimezone(EASTERN)
```

| Property | Behavior |
|---|---|
| Input unit | Milliseconds since Unix epoch (JSON `timestamp` field) |
| Intermediate | UTC-aware `datetime` |
| Output | Eastern wall-clock `datetime` with correct DST offset |
| DST handling | Delegated to `zoneinfo`/`pytz` IANA rules for `America/New_York` |

Annotation dates and `--date-from` cutoff dates are localized through the same `_localize_naive()` helper, ensuring annotation matching and CLI filtering operate in the identical timezone domain as message timestamps.

### 3.2 Sorting Invariant

After all records are assembled, a single sort is applied:

```python
records.sort(key=lambda r: r["ts_ms"], reverse=True)
```

| Property | Guarantee |
|---|---|
| Sort key | Raw epoch milliseconds (`ts_ms`), not localized display strings |
| Order | Strict reverse-chronological (newest first) |
| Stability | Python's sort is stable; equal timestamps retain insertion order |
| Scope | Applies to the full returned list after any `--date-from` filtering |

### 3.3 The 5-Part Minute Tuple Override Engine

For `type == "link"` messages (Facebook video call metadata traces), the parser constructs an immutable local-time integer tuple:

```python
(year, month, day, hour, minute) = _local_minute_key(local_dt)
```

This tuple is used as a dictionary key into the annotation manifest loaded from `call_annotations.csv`.

**Matching flow:**

```
link message -> compute local_dt -> _local_minute_key(local_dt)
    -> lookup in annotations dict
        -> hit + override_type == "unanswered":
            itype  = "Facebook Video Call (Unanswered Attempt)"
            content = "📞 Video Call Attempt — Unanswered"
            footnote = "*Status verified via cross-referenced local history logs*"
        -> miss or other override_type:
            itype  = "Facebook Video Call Log"
            content = "Video Call Log Entry (Platform Metadata Trace)"
```

| Match criterion | Scope |
|---|---|
| Granularity | Minute-exact in Eastern local time |
| Direction | CSV -> existing JSON record only (no injection) |
| Collision | Last CSV row wins if duplicate keys are loaded |

The override alters the **rendered payload** (`itype`, `content`, `footnote`) of an existing record. It does not modify the source JSON, the CSV, or the underlying `ts_ms` value.

### 3.4 Parameterized Identity Routing

Column placement and display labels are driven by CLI identity parameters passed into `parse_messages()` and `build_html()`:

```python
is_left = is_left_sender(raw_sender, left_name)
# ...
"sender": left_name if is_left else right_name,
```

Implementation (`is_left_sender()`):

```python
def is_left_sender(raw_sender: str, left_name: str) -> bool:
    if raw_sender.casefold() == left_name.casefold():
        return True
    # Meta export alias for the default left-column identity label.
    if left_name.upper() == DEFAULT_LEFT_NAME and raw_sender == LEFT_RAW:
        return True
    return False
```

| Constant | Value | Role |
|---|---|---|
| `DEFAULT_LEFT_NAME` | `"JOHN DOE"` | Default `--left` (internally in `core/parse_calls.py`) value and HTML left-column header |
| `DEFAULT_RIGHT_NAME` | `"JANE DOE"` | Default `--right` (internally in `core/parse_calls.py`) value and HTML right-column header |
| `LEFT_RAW` | `"John Doe"` | Meta export `senderName` alias; matched to left column only when using default name matching |

All non-left senders route to the right column. HTML title, parties line, sticky column bar, and bubble metadata labels consume `left_name` / `right_name` dynamically.

### 3.5 Forensic Ingestion & Accounting Matrix

The logic engine uses distinct rules to credit communication metrics based on the type and response state of each interaction:

* **Sender-Based Ingestion (Initiator Focus)**:
  * **Text Messages**: Credited strictly to the sender/initiator.
  * **Media Attachments**: Credited strictly to the sender/initiator.
  * **Connected Voice/Video Calls**: Tallied and credited to the party who initiated/sent the record (standard platform log logic).
* **Recipient-Based Ingestion (Missed-Call Focus)**:
  * **Unanswered, Missed, or Declined Video/Voice Calls**: Tallied and credited strictly to the **recipient party** (destination) instead of the initiator. If the Left Party initiates an unanswered call, the Right Party's counter increments; if the Right Party initiates, the Left Party's counter increments. This prevents missed calls from inflating the sender's activity counters and ensures correct personal logging.
* **Dynamic Date Bounds Extraction**:
  * During the document assembly process, the HTML generation engine dynamically evaluates the sorted array indices of the normalized records.
  * It extracts the datetime of the absolute first record (earliest chronological index) and the absolute last record (latest chronological index).
  * These limits are formatted and embedded as a dedicated `"Timeline: [Start Date] to [End Date]"` metadata string in the subheader under the main title.

### 3.6 HTML Layout System & Interface Specifications

The interactive HTML timeline output (`EXHIBITS/timeline_report.html`) relies on a robust grid-based layout structure:

* **Strict 45% | 10% | 45% Three-Column Grid**:
  * Both the sticky header column bar (`.col-bar`) and individual message rows (`.row`) enforce a strict layout divided as `45fr 10fr 45fr` (45% for the Left Column, 10% for the Center Column, and 45% for the Right Column).
  * This structure guarantees that outbound messages stay aligned to the left and inbound messages to the right, separated by a distinct timeline track.
* **Transparent Center Timeline Axis**:
  * The center column (`.row .c-center` and `.cb-center`) is styled to be **entirely transparent** and clean of any background shading, gray box artifacts, border lines, or container bounding blocks around the blue directional icons (`➡️` and `⬅️`).
  * The directional icons float freely within a transparent container, preserving a clean visual spine.
* **Native Inline SVG Iconography**:
  * Video call log entries feature high-contrast headers containing custom native **inline SVG icons** (`<svg width="14" height="14" viewBox="0 0 24 24" ...>`) directly embedded into the HTML markup.
  * This ensures sharp visual presentation of video call events without external asset dependencies.

### 3.7 Split Dashboard Metrics Design

The top of the generated HTML report includes a prominent statistics panel (`.metrics-panel`) styled for readability and visual comparison:

* **50/50 Dual-Column Grid**:
  * The statistics dashboard is divided into exactly two columns split 50/50 down the center spine (`display: grid; grid-template-columns: 1fr 1fr;` with `gap: 0;`).
* **High-Visibility Uniform Typography**:
  * All text labels and numeric values inside the dashboard are rendered in high-contrast white (`#FFFFFF`) against the dark (`#1c1e21`) header background.
  * Quantitative values are enlarged significantly using a bold, large scaling font size of **`1.75rem`** (`.metric-val`) to allow auditors to instantly read the totals.
* **Mirrored Layout Alignment Rules**:
  * Left Party metrics rows are right-aligned (`[Label] [Number] |`) with a right padding of `24px` and a right border of `1px solid #334155`.
  * Right Party metrics rows are left-aligned (`| [Number] [Label]`) with a left padding of `24px`.
  * This mirrored structure forces the data labels to align inward flush against the center vertical line, enabling direct, side-by-side metric comparison.

---

## 4. CLI Configuration Vector & Path Resolution Engine

All runtime configuration is registered via `argparse` in the `compile_html.py` entry point (or directly in `core/parse_calls.py` if run as a module) and passed into `main(date_from, file_path, left_name, right_name)`.

### 4.1 Comprehensive Argument Interface

| Flag | Type | Default | Description |
|---|---|---|---|
| `-f` / `--file` | `str` | `None` (Required) | Path to target Messenger JSON export |
| `--date-from` | `str` | `None` | Include records on/after this date (`YYYY-MM-DD`, midnight ET) |
| `--left-party` | `str` | `None` (Required) | Left-column / outbound identity label |
| `--right-party` | `str` | `None` (Required) | Right-column / inbound identity label |

```powershell
python .\compile_html.py --help
```

### 4.2 `-f` / `--file`: Dynamic Path Resolution

When `--file` is supplied, `resolve_input_file()` resolves the path:

```python
p = Path(file_arg)
target = p if p.is_absolute() else IMPORT_DIR / p
```

Relative paths anchor to `IMPORT_DIR` (`Messenger_Import`). The target must exist and be a regular file; otherwise a clean `[ERROR]` is printed and execution returns without traceback.

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
| **Zero files** | Print `[ERROR] No Messenger JSON export found in the import directory.`; graceful exit (`return`) |
| **Exactly one file** | Auto-select; print `No input file specified. Defaulting to discovered file: [Filename]` |
| **Multiple files** | Deterministic `sorted()` order; select index 0; print `[WARN]` with filename and list alternatives |

The scan is **shallow** (`IMPORT_DIR.glob("*.json")` only). Files in subdirectories (e.g., `media/rename_map.json` inside the output space) are excluded.

Resolved path flows into:

```python
records = parse_messages(input_file, annotations, cutoff_dt,
                         left_name=left_name, right_name=right_name)
html_content = build_html(records, input_file.name, generated_at, ann_applied,
                          left_name=left_name, right_name=right_name)
```

### 4.3 `--date-from`: Temporal Filter Vector

```powershell
python .\compile_html.py -f input_export.json --left-party "John Doe" --right-party "Jane Doe" --date-from 2026-05-01
```

**Cutoff resolution** (in `main()`):

```python
cutoff_dt = _localize_naive(datetime.strptime(date_from, "%Y-%m-%d"))
# Midnight (00:00:00) Eastern on the specified calendar date
```

**Early bypass** (in `parse_messages()`, immediately after `local_dt` computation):

```python
if cutoff_dt is not None and local_dt < cutoff_dt:
    continue
```

| Execution point | Effect |
|---|---|
| Position | After timestamp conversion, **before** `make()`, media rename, or record append |
| Comparison | Strict less-than against midnight Eastern of `--date-from` |
| Records on cutoff date | **Included** (`local_dt >= cutoff_dt`) |
| Omitted flag | Full history parsed |

Console summary statistics (`len(records)`, per-`itype` counts) reflect only the filtered subset.

### 4.4 `--left-party` and `--right-party`: Identity Parameterization

```powershell
python .\compile_html.py -f input_export.json --left-party "John Doe" --right-party "Jane Doe"
python .\compile_html.py -f input_export.json --left-party "PARTY A" --right-party "PARTY B"
```

These flags override all hardcoded party display strings. They propagate through:

- `parse_messages()` — `is_left_sender()` column routing and `sender` field assignment
- `build_html()` — document title, parties metadata, sticky column bar labels, bubble sender metadata

**Matching rules:**

1. **Case-insensitive equality:** `raw_sender.casefold() == left_name.casefold()` -> left column.
2. **Default alias fallback:** When `--left-party` is the default `"JOHN DOE"`, the Meta export raw name `"John Doe"` (`LEFT_RAW`) also maps to the left column.
3. **Right column:** All records not matched to left route to right; display label is always `right_name`.

Custom identity strings that do not match any `senderName` value in the JSON will produce an exhibit with all records in the right column unless the export uses matching names.

### 4.5 Storage Protection Guard

When `--date-from` is active, `cleanup_unreferenced_media()` is **not executed**:

```python
if cutoff_dt is None:
    cleanup_unreferenced_media()
else:
    print("\nSkipping media cleanup (date filter active).")
```

**Rationale:** A partial parse processes only a subset of messages. Media files referenced by excluded (pre-cutoff) records would not be registered in `rename_map.json` during that run. Running the isolation sweep would falsely classify those valid historical assets as unreferenced and relocate them to `EXHIBITS/media/unrelated/`, breaking chain-of-custody for the full export.

The cleanup routine itself (full-parse mode only) moves files in `EXHIBITS/media/` whose basenames are absent from `rename_map.json` into `EXHIBITS/media/unrelated/`. It skips subdirectories, skips `rename_map.json`, and aborts entirely if the map is empty.

---

## 5. Forensic Integrity & Legal Audit Verification Checklist

### 5.1 Immutability of Source Data

| Asset | Read | Write | Notes |
|---|---|---|---|
| Messenger JSON export (`Messenger_Import/*.json`) | Yes | **No** | Resolved via `-f` or auto-discovery; opened read-only |
| `call_annotations.csv` (`Messenger_Import/call_annotations.csv`) | Yes | **No** | Loaded into memory; source file untouched |
| `timeline_report.html` (`EXHIBITS/timeline_report.html`) | — | Yes | Isolated output artifact |
| `rename_map.json` (`EXHIBITS/media/rename_map.json`) | Yes | Yes | Provenance manifest; append-only mapping on each full parse |
| `media/*` (`EXHIBITS/media/` binary files) | Yes | Yes | Copied/mirrored from `Messenger_Import/media/` once from UUID -> timestamp signature |
| `media/unrelated/` (`EXHIBITS/media/unrelated/`) | — | Yes (full parse only) | Isolation vault for unreferenced assets |

**Auditor action:** Compare SHA-256 hashes of the JSON export and `call_annotations.csv` before and after execution. Hashes must be identical.

### 5.2 Determinism Verification

Given **identical** source files, CLI arguments, an **unchanged** `rename_map.json`, and **no new media renames**, the following are deterministic:

- Record count and per-`itype` distribution
- Sort order (`ts_ms` descending)
- Override resolution (minute-tuple matching)
- Column placement (`is_jon`) for a fixed `--left` / `--right` pair
- Record field values (`content`, `footnote`, `itype`, `sender`)

**Non-deterministic elements** (document for disclosure):

| Element | Cause |
|---|---|
| `timeline_report.html` `Generated:` timestamp | `datetime.now(tz=EASTERN)` at render time |
| First-run media renames | Initial UUID -> timestamp copy/mirror mutates `EXHIBITS/media/` disk state and `EXHIBITS/media/rename_map.json` |
| Thumbnail cache | OpenCV may create new files in `EXHIBITS/media/thumbnails/` on first encounter |

**Auditor action (stable-state verification):**

```powershell
python .\parse_calls.py
Get-FileHash .\timeline_report.html -Algorithm SHA256
# Re-run with identical flags; compare record counts and itype breakdown
```

### 5.3 Handling String Encoding Quirks

Meta exports frequently double-encode UTF-8 text as latin-1. The `fix_encoding()` function applies a reversible transform:

```python
s.encode("latin-1").decode("utf-8")
```

| Scenario | Behavior |
|---|---|
| Valid double-encoding | Corrected to proper Unicode |
| Already-valid UTF-8 / ASCII | `UnicodeEncodeError` or `UnicodeDecodeError` caught; original string returned |
| Console output on Windows | Non-ASCII log characters may fail under cp1252 terminals; does not affect HTML output (UTF-8) |

HTML emission uses `html.escape()` on all rendered text fields, preventing markup injection in the exhibit.

### 5.4 Audit Log Consistency

The console emits a complete, dynamic metric block derived directly from the returned `records` list:

```
Parsed N records:
    XXX  Facebook Video Call Log
    XXX  Facebook Video Call (Unanswered Attempt)
    XXX  Media Sent (Photo)
    XXX  Media Sent (Video)
    XXX  Text Message
```

| Metric | Source | Filter-aware | Identity-aware |
|---|---|---|---|
| Total record count | `len(records)` | Yes | No |
| Per-type breakdown | `counts[r["itype"]]` | Yes | No |
| Override count (HTML banner) | `sum(1 for r in records if r.get("footnote"))` | Yes | No |
| Column routing | `is_jon` flag | Yes | Yes — driven by `--left` matching |

**Auditor action:** Verify that the sum of all per-type counts equals the total record count printed.

### 5.5 Identity Parameterization Verification

This protocol confirms that `--left-party` and `--right-party` shift layout mapping and metadata without altering core parsing logic (timestamp normalization, override engine, record schema).

**Procedure:**

```powershell
# Baseline run with required arguments
python .\compile_html.py -f "input_export.json" --left-party "John Doe" --right-party "Jane Doe"
# Note total record count and per-itype breakdown

# Custom identity labels (same source file, same record count expected)
python .\compile_html.py -f "input_export.json" --left-party "OUTBOUND PARTY" --right-party "INBOUND PARTY"
```

**Verification criteria:**

| Check | Expected result |
|---|---|
| Record count | Identical to baseline (identity flags do not filter records) |
| Per-`itype` breakdown | Identical to baseline |
| HTML title / parties line | Displays `OUTBOUND PARTY & INBOUND PARTY` |
| Sticky column bar | Left header = `--left-party`; right header = `--right-party` |
| Bubble metadata | `sender` field matches configured identity per column |
| Left-column record count | Unchanged when default preserves `John Doe` alias matching |
| Source JSON hash | Unchanged before and after both runs |

**Negative test:**

```powershell
python .\compile_html.py -f "input_export.json" --left-party "NONEXISTENT SENDER" --right-party "INBOUND PARTY"
```

All records whose `senderName` does not case-match `"NONEXISTENT SENDER"` should appear in the right column. Record count remains unchanged; only column placement and display labels shift.

---

## Execution Reference

```powershell
# Build with required arguments (using auto-discovery or required flags)
python .\compile_html.py -f "input_export.json" --left-party "John Doe" --right-party "Jane Doe"

# Filtered history from a start date (midnight Eastern)
python .\compile_html.py -f "input_export.json" --left-party "John Doe" --right-party "Jane Doe" --date-from 2026-05-01

# Custom party identities
python .\compile_html.py -f "input_export.json" --left-party "John Doe" --right-party "Jane Doe"

# Combined configuration
python .\compile_html.py -f "input_export.json" --date-from 2026-05-01 --left-party "JOHN DOE" --right-party "JANE DOE"

# Full argument reference
python .\compile_html.py --help
```

**Outputs:**

| File | Producer | Description |
|---|---|---|
| `EXHIBITS/timeline_report.html` | `core/parse_calls.py` | Interactive forensic timeline exhibit |
| `EXHIBITS/media/rename_map.json` | `core/parse_calls.py` | UUID -> timestamp provenance manifest |
| `EXHIBITS/media/thumbnails/*.jpg` | `core/parse_calls.py` (optional) | Video first-frame captures |
| `EXHIBITS/timeline_exhibit.pdf` | `compile_pdf.py` | Print-optimized binder exhibit |

---

## Directory Layout

```text
messenger-logs/
├── core/
│   ├── __init__.py
│   └── parse_calls.py      # Core Ingestion Engine
├── documentation/
├── EXHIBITS/               # Generated workspace (PDFs, HTML, mirrored media cache)
│   └── media/
│       ├── thumbnails/
│       └── rename_map.json
└── Messenger_Import/       # Pristine, read-only forensic source
    └── media/
    └── input_export.json
```
