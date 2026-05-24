# More pip-skill Examples

Real packages, one command each. Each entry shows what your AI assistant generates when given the skill.

---

### `google-cloud-bigquery`: Query BigQuery from a prompt

```bash
pip install google-cloud-bigquery && pip-skill convert google-cloud-bigquery
```

Run SQL, load results into DataFrames, create tables, export to GCS, all without touching the console.

> *"show me the top 10 users by revenue in our analytics table today"*

```python
from google.cloud import bigquery

client = bigquery.Client(project='my-project')
rows = client.query("""
    SELECT user_id, COUNT(*) AS events, ROUND(SUM(revenue), 2) AS total
    FROM `my-project.analytics.events`
    WHERE DATE(timestamp) = CURRENT_DATE()
    GROUP BY user_id ORDER BY total DESC LIMIT 10
""")
for row in rows:
    print(f"{row.user_id:<12} {row.events:>5} events   ${row.total:>8.2f}")
```

```
u_4291           847 events   $1,204.50
u_1033           412 events   $  891.20
u_7718           203 events   $  650.00
```

<img src="demos/google-cloud-bigquery.gif" alt="pip-skill convert google-cloud-bigquery" width="640">

---

### `databricks-sdk`: Manage Databricks workspaces

```bash
pip install databricks-sdk && pip-skill convert databricks-sdk
```

List clusters, submit jobs, read Delta tables, manage secrets, browse the Unity Catalog, all from conversation.

> *"which clusters are running and burning money right now?"*

```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
for c in w.clusters.list():
    if str(c.state.value) == 'RUNNING':
        dbu = c.cluster_memory_mb / 1024 * c.num_workers
        print(f"{c.cluster_name:<28} {c.num_workers} workers   ~{dbu:.0f} DBU/hr")
```

```
ml-training-cluster          8 workers   ~64 DBU/hr
data-eng-shared              4 workers   ~32 DBU/hr
analytics-dev                2 workers   ~16 DBU/hr
```

<img src="demos/databricks-sdk.gif" alt="pip-skill convert databricks-sdk" width="640">

---

### `anthropic`: Use the Claude API from Claude Code

```bash
pip install anthropic && pip-skill convert anthropic
```

177 functions, 1115 classes, 100% annotated, the entire Anthropic SDK available as a skill. Build Claude-powered workflows directly from the chat.

> *"batch summarize these 50 support tickets into one-line descriptions"*

```python
import anthropic, json

client = anthropic.Anthropic()
tickets = json.load(open("tickets.json"))

for ticket in tickets:
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=60,
        messages=[{"role": "user", "content": f"One line summary: {ticket['body']}"}]
    )
    print(f"[{ticket['id']}] {msg.content[0].text}")
```

```
[T-1042] Login fails on Safari 17 when 2FA is enabled
[T-1043] Export button missing from billing page for enterprise accounts
[T-1044] Webhook retry logic not respecting exponential backoff config
```

<img src="demos/anthropic.gif" alt="pip-skill convert anthropic" width="640">

---

### `cryptography`: Real encryption, not base64

```bash
pip install cryptography && pip-skill convert cryptography --select
```

74 functions, 406 classes. Fernet symmetric encryption, RSA keys, X.509 cert parsing, HMAC signing, PBKDF2 password hashing.

> *"encrypt all .env files in this repo with a passphrase"*

```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
import base64, os, pathlib

password = b"my-secret-passphrase"
salt = os.urandom(16)
kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=480000)
key = base64.urlsafe_b64encode(kdf.derive(password))
f = Fernet(key)

for env_file in pathlib.Path(".").rglob(".env"):
    encrypted = f.encrypt(env_file.read_bytes())
    env_file.with_suffix(".env.enc").write_bytes(salt + encrypted)
    env_file.unlink()
    print(f"encrypted: {env_file}")
```

```
encrypted: .env
encrypted: services/api/.env
encrypted: services/worker/.env
```

<img src="demos/cryptography.gif" alt="pip-skill convert cryptography" width="640">

---

### `paramiko`: SSH and SFTP without leaving the chat

```bash
pip install paramiko && pip-skill convert paramiko
```

Connect to remote servers, run commands, transfer files, manage keys. Claude becomes a remote ops assistant.

> *"check disk usage on these 5 servers and flag anything above 80%"*

```python
import paramiko

servers = ["web-01", "web-02", "db-01", "worker-01", "worker-02"]
client = paramiko.SSHClient()
client.load_system_host_keys()

for host in servers:
    client.connect(host, username="ubuntu", key_filename="~/.ssh/id_ed25519")
    _, stdout, _ = client.exec_command("df -h / | awk 'NR==2{print $5, $6}'")
    usage, mount = stdout.read().decode().split()
    flag = " ALERT" if int(usage.rstrip("%")) > 80 else ""
    print(f"{host:<14} {usage}{flag}")

client.close()
```

```
web-01         43%
web-02         71%
db-01          89%  ALERT
worker-01      34%
worker-02      55%
```

<img src="demos/paramiko.gif" alt="pip-skill convert paramiko" width="640">

---

### `Pillow`: Image processing at scale

```bash
pip install Pillow && pip-skill convert Pillow
```

Resize, crop, rotate, watermark, convert formats, apply filters, composite, any image operation from a single prompt.

> *"resize all JPEGs to 1200px wide, convert to WebP, stamp CONFIDENTIAL"*

```python
from PIL import Image, ImageDraw, ImageFont
import pathlib

for src in pathlib.Path(".").glob("*.jpg"):
    img = Image.open(src)
    ratio = 1200 / img.width
    img = img.resize((1200, int(img.height * ratio)), Image.LANCZOS)

    draw = ImageDraw.Draw(img)
    draw.text((20, img.height - 40), "CONFIDENTIAL", fill=(255, 0, 0, 180))

    out = src.with_suffix(".webp")
    img.save(out, "WEBP", quality=85)
    print(f"{src.name} -> {out.name}")
```

```
photo_001.jpg -> photo_001.webp
photo_002.jpg -> photo_002.webp
photo_003.jpg -> photo_003.webp
12 files processed
```

<img src="demos/Pillow.gif" alt="pip-skill convert Pillow" width="640">

---

### `openpyxl`: Real Excel, not CSV

```bash
pip install openpyxl && pip-skill convert openpyxl
```

Formulas, merged cells, charts, conditional formatting, named ranges, actual `.xlsx` files, not flat exports.

> *"build a sales report with a summary sheet and SUM formulas in the totals row"*

```python
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font
from openpyxl.utils import get_column_letter

wb = Workbook()
ws = wb.active
ws.title = "Sales"
headers = ["Region", "Q1", "Q2", "Q3", "Q4", "Total"]
ws.append(headers)
for cell in ws[1]:
    cell.font = Font(bold=True)
    cell.fill = PatternFill("solid", fgColor="4472C4")

for i, row in enumerate(sales_data, start=2):
    ws.append(row)
    ws.cell(i, 6).value = f"=SUM(B{i}:E{i})"
    if i % 2 == 0:
        for cell in ws[i]:
            cell.fill = PatternFill("solid", fgColor="D9E1F2")

wb.save("sales_report.xlsx")
print("saved sales_report.xlsx")
```

```
saved sales_report.xlsx -- 4 regions, 16 rows, formulas applied
```

<img src="demos/openpyxl.gif" alt="pip-skill convert openpyxl" width="640">

---

### `pytesseract`: Read text from images

```bash
pip install pytesseract && pip-skill convert pytesseract
```

OCR screenshots, scanned documents, photos of whiteboards, receipts, and business cards.

> *"extract all line items and totals from these receipt photos"*

```python
import pytesseract, csv
from PIL import Image
import pathlib, re

with open("receipts.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["file", "item", "amount"])
    for img_path in pathlib.Path(".").glob("receipt_*.jpg"):
        text = pytesseract.image_to_string(Image.open(img_path))
        for line in text.splitlines():
            match = re.match(r"(.+?)\s+\$?([\d.]+)$", line.strip())
            if match:
                writer.writerow([img_path.name, match.group(1), match.group(2)])
```

```
receipts.csv written -- 6 files, 43 line items extracted
```

<img src="demos/pytesseract.gif" alt="pip-skill convert pytesseract" width="640">

---

### `pydub`: Audio processing

```bash
pip install pydub && pip-skill convert pydub
```

Slice, normalize, convert formats, strip silence, overlay tracks. Works on anything ffmpeg can read.

> *"split this podcast on 2-second silences, normalize to -14 LUFS, export as MP3s"*

```python
from pydub import AudioSegment
from pydub.silence import split_on_silence
import pathlib

audio = AudioSegment.from_file("podcast.mp4")
chunks = split_on_silence(audio, min_silence_len=2000, silence_thresh=-40)

out = pathlib.Path("segments")
out.mkdir(exist_ok=True)
for i, chunk in enumerate(chunks):
    normalized = chunk.apply_gain(-14 - chunk.dBFS)
    normalized.export(out / f"segment_{i+1:03d}.mp3", format="mp3", bitrate="192k")
    print(f"segment_{i+1:03d}.mp3  {len(chunk)/1000:.1f}s")
```

```
segment_001.mp3  142.3s
segment_002.mp3   38.7s
segment_003.mp3   91.2s
8 segments exported
```

<img src="demos/pydub.gif" alt="pip-skill convert pydub" width="640">

---

### `twilio`: SMS and WhatsApp from a prompt

```bash
pip install twilio && pip-skill convert twilio --select
```

Outbound SMS, WhatsApp, voice calls, number lookup, the whole Twilio API without reading any docs.

> *"text everyone on this list that their appointment is confirmed for tomorrow 10am"*

```python
from twilio.rest import Client
import csv

client = Client(os.environ["TWILIO_SID"], os.environ["TWILIO_TOKEN"])

with open("appointments.csv") as f:
    for row in csv.DictReader(f):
        try:
            msg = client.messages.create(
                body=f"Hi {row['name']}, your appointment is confirmed for tomorrow at 10am.",
                from_="+15005550006",
                to=row["phone"]
            )
            print(f"sent: {row['name']} ({msg.sid})")
        except Exception as e:
            print(f"failed: {row['name']} -- {e}")
```

```
sent: Maria Santos (SM9a3b...)
sent: James Wu (SMc4d5...)
failed: Alex Rivera -- Invalid phone number
24 sent, 1 failed
```

<img src="demos/twilio.gif" alt="pip-skill convert twilio" width="640">

---

### `reportlab`: Generate PDFs from scratch

```bash
pip install reportlab && pip-skill convert reportlab --select
```

Tables, charts, headers, footers, embedded images, custom fonts, contracts, invoices, and reports fully generated.

> *"produce a professional invoice PDF from this JSON data"*

```python
from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

doc = SimpleDocTemplate("invoice.pdf", pagesize=LETTER)
styles = getSampleStyleSheet()
items = [["Description", "Qty", "Unit Price", "Total"]]
for line in invoice["line_items"]:
    items.append([line["desc"], line["qty"], f"${line['price']:.2f}", f"${line['qty']*line['price']:.2f}"])
items.append(["", "", "TOTAL", f"${invoice['total']:.2f}"])

table = Table(items, colWidths=[260, 50, 90, 90])
table.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
    ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
    ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
    ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#EEF2FA")]),
    ("FONTNAME",   (0, -1), (-1, -1), "Helvetica-Bold"),
]))
doc.build([Paragraph(f"Invoice #{invoice['id']}", styles["Title"]), table])
print("invoice.pdf written")
```

```
invoice.pdf written -- 1 page, 8 line items, $4,320.00 total
```

<img src="demos/reportlab.gif" alt="pip-skill convert reportlab" width="640">

---

### `pyarrow`: Work with datasets too big for pandas

```bash
pip install pyarrow && pip-skill convert pyarrow --select
```

Read Parquet files, filter and transform columnar data, convert between Arrow/Pandas/CSV, handles datasets that don't fit in memory.

> *"filter this 4GB Parquet file for APAC revenue > 10000 and export the top 20 rows"*

```python
import pyarrow.parquet as pq
import pyarrow.compute as pc

table = pq.read_table(
    "transactions.parquet",
    filters=[("region", "=", "APAC"), ("revenue", ">", 10000)]
)
top20 = table.sort_by([("revenue", "descending")]).slice(0, 20)
pq.write_table(top20, "apac_top20.parquet")

print(f"filtered: {len(table):,} rows matched out of {pq.read_metadata('transactions.parquet').num_rows:,}")
print(f"top 20 written to apac_top20.parquet")
```

```
filtered: 4,821 rows matched out of 18,432,901
top 20 written to apac_top20.parquet
```

<img src="demos/pyarrow.gif" alt="pip-skill convert pyarrow" width="640">

---

> **Tip:** For large surfaces (`boto3`, `stripe`, `databricks-sdk`), use `--select` to let Claude curate the most relevant functions for your use case instead of selecting by score alone.
