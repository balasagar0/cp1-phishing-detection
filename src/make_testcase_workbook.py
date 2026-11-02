"""Writes testcases/review2_testcase_workbook.xlsx (data-entry workbook) and testcases/example_testcases.csv."""
from pathlib import Path
import csv
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from testcases import COLS, CHANNELS, LABELS, SOURCES

OUT = Path(__file__).resolve().parents[1] / "testcases"; OUT.mkdir(exist_ok=True)
N = 1001                                                    # data rows 2..1001
F = lambda **k: Font(name="Arial", size=k.pop("size", 10), **k)
HEAD = PatternFill("solid", fgColor="7A1F2B"); BLUE = PatternFill("solid", fgColor="DDEBF7"); GREY = PatternFill("solid", fgColor="F2F2F2")
thin = Side(style="thin", color="D0D0D0"); BOX = Border(left=thin, right=thin, top=thin, bottom=thin)
EX = [  # illustrative example rows (not real incidents)
 ["EX-1", "EX-1-1", "sms", "2026-11-03T10:02:00+05:30", "+91 90000 22222", "", "Dear customer, your account will be blocked today. Update KYC at hxxp://kyc-update-bank[.]top/verify", "malicious", "EX-C1", "example", "", "attack bundle: SMS, link, call, same campaign", ""],
 ["EX-1", "EX-1-2", "url", "2026-11-03T10:06:00+05:30", "", "", "hxxp://kyc-update-bank[.]top/verify", "malicious", "EX-C1", "example", "", "same domain as the SMS", ""],
 ["EX-1", "EX-1-3", "call", "2026-11-03T10:20:00+05:30", "+91 90000 22222", "", "Caller says the account will be frozen unless the OTP is shared (tester's note)", "malicious", "EX-C1", "example", "", "calls are recorded but not scored yet", ""],
 ["EX-2", "EX-2-1", "sms", "2026-11-03T15:00:00+05:30", "+91 90000 33333", "", "Hey, can we move our meeting to 4 pm? I will email the notes.", "benign", "", "example", "", "benign bundle that is linked (same colleague)", ""],
 ["EX-2", "EX-2-2", "email", "2026-11-03T15:05:00+05:30", "colleague@example.org", "Re: meeting", "Thanks for confirming. The notes are here: https://en.wikipedia.org/wiki/Project_management", "benign", "", "example", "", "", ""]]
with open(OUT / "example_testcases.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(COLS); w.writerows(EX)

wb = Workbook(); rm = wb.active; rm.title = "Read me"
lines = [("Review-2 multi-channel test cases", "title"), ("One row = one event (a message, a link or a call). Events that one person or test account saw in one session form a bundle.", None), ("", None),
 ("Where to type", "h"), ("Only the Events sheet, starting at row 7. Rows 2-6 are blue example rows; leave them (they are ignored).", None), ("Do not rename the sheet or the headers. Grey column M counts bundles by itself.", None), ("", None),
 ("Columns", "h"),
 ("bundle_id (required): one id per bundle, e.g. B001. Every event of the bundle repeats it.", None), ("event_id: optional, unique, e.g. B001-1.", None),
 ("channel (required): email, sms, url or call. Calls are recorded but not scored yet.", None),
 ("time (required): when the event happened, like 2026-11-03T10:02:00+05:30.", None),
 ("identity: sender number, sender address or domain, if known. Used to link events.", None), ("subject: email subject only.", None),
 ("content (required): the message text, the URL, or a short note for a call. Defang live links (hxxp, [.]).", None),
 ("event_label (required): malicious or benign. Decide this before you see any model score.", None),
 ("campaign_id: required for malicious events. Events from the same attacker campaign share one id.", None),
 ("source_type (required): lab_simulation, collected_real, public_dataset. Use example only for the blue rows.", None),
 ("basis: required for collected_real. Say why you may use it (own account, participant consent).", None),
 ("notes: anything useful. detector_score: leave empty unless a detector outside this project scored the event (0 to 1).", None), ("", None),
 ("Check your file", "h"), ("python src/refit_fusion.py testcases/review2_testcase_workbook.xlsx", None), ("Full rules, ethics and sample sizes: TESTCASE_FORMAT.md", None)]
for i, (t, k) in enumerate(lines, 1):
    c = rm.cell(i, 1, t); c.font = F(size=14, bold=True, color="7A1F2B") if k == "title" else F(bold=True, size=11) if k == "h" else F(); c.alignment = Alignment(wrap_text=True, vertical="top")
rm.column_dimensions["A"].width = 120

ev = wb.create_sheet("Events"); hdr = COLS[:-1] + ["bundles_counter (auto)"]
order = ["bundle_id", "event_id", "channel", "time", "identity", "subject", "content", "event_label", "campaign_id", "source_type", "basis", "notes"]   # detector_score lives in column N
for j, h in enumerate(order + ["bundles_counter (auto)", "detector_score"], 1):
    c = ev.cell(1, j, h); c.font = F(bold=True, color="FFFFFF"); c.fill = HEAD; c.alignment = Alignment(vertical="center", wrap_text=True)
idx = {h: j for j, h in enumerate(order, 1)}
for i, row in enumerate(EX, 2):
    d = dict(zip(COLS, row))
    for h in order:
        c = ev.cell(i, idx[h], d[h]); c.font = F(color="0000FF"); c.fill = BLUE
    ev.cell(i, 14).fill = BLUE
for r in range(2, N + 1):
    ev.cell(r, 13, f'=IF(OR(A{r}="",J{r}="example"),0,IF(COUNTIFS($A$2:A{r},A{r},$J$2:J{r},"<>example")=1,1,0))').font = F(color="808080"); ev.cell(r, 13).fill = GREY
    for j in range(1, 13):
        ev.cell(r, j).border = BOX
        if r > 6: ev.cell(r, j).font = F()
        ev.cell(r, j).alignment = Alignment(wrap_text=True, vertical="top")
for col, w in zip("ABCDEFGHIJKLMN", [10, 11, 9, 26, 22, 22, 60, 12, 12, 16, 22, 30, 14, 14]): ev.column_dimensions[col].width = w
ev.freeze_panes = "A2"
for col, vals in (("C", CHANNELS), ("H", LABELS), ("J", SOURCES)):
    dv = DataValidation(type="list", formula1='"' + ",".join(vals) + '"', allow_blank=True, showErrorMessage=True, errorTitle="Not allowed", error="Pick a value from the list."); ev.add_data_validation(dv); dv.add(f"{col}7:{col}{N}")

pg = wb.create_sheet("Progress")
pg["A1"] = "Progress (example rows are not counted)"; pg["A1"].font = F(size=12, bold=True, color="7A1F2B")
rng = lambda c: f"Events!${c}$2:${c}${N}"
pg["A3"] = "Bundles collected"; pg["B3"] = f"=SUM(Events!$M$2:$M${N})"
pg["A4"] = "Events collected"; pg["B4"] = f'=SUMPRODUCT(({rng("H")}<>"")*({rng("J")}<>"example"))'
pg["A6"] = "Events by channel and label"; pg["B6"] = "malicious"; pg["C6"] = "benign"
for i, ch in enumerate(CHANNELS, 7):
    pg.cell(i, 1, ch)
    for j, lb in enumerate(LABELS, 2):
        pg.cell(i, j, f'=SUMPRODUCT(({rng("C")}=$A{i})*({rng("H")}={chr(64 + j)}$6)*({rng("J")}<>"example"))')
pg["A12"] = "Events by source type"
for i, s in enumerate(SOURCES[:3], 13):
    pg.cell(i, 1, s); pg.cell(i, 2, f'=SUMPRODUCT(({rng("J")}=$A{i})*({rng("H")}<>""))')
pg["A17"] = "Bundle-level counts (coordinated, benign linked) and the targets are reported by the check command; see TESTCASE_FORMAT.md section 6."
for row in pg.iter_rows():
    for c in row:
        if c.value is not None and c.font.name != "Arial": c.font = F(bold=c.column == 1 and c.row in (3, 4, 6, 12))
pg.column_dimensions["A"].width = 34; pg.column_dimensions["B"].width = 14; pg.column_dimensions["C"].width = 14
wb.save(OUT / "review2_testcase_workbook.xlsx"); print("saved workbook + example csv")
