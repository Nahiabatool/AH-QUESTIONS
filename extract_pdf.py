#!/usr/bin/env python3
"""Extract ALL MCQ questions from aviation PDFs and generate questions.js."""
import re, os, json

try:
    from pypdf import PdfReader
except ImportError:
    from PyPDF2 import PdfReader

# Path to folder containing the PDFs (adjust if your PDFs are elsewhere)
PDF_DIR = r"c:\Users\Abbas Haider\AppData\Roaming\Cursor\User\workspaceStorage\5b1b155b0c6a7290d197a781ddf3326a\pdfs"

PDFS = [
    (os.path.join(PDF_DIR, "31a016b8-edbd-419b-8b8e-0f3a09925a21", "AIR LAW AND ATC PROCEDURES.pdf"), "Air Law & ATC Procedures", "airlaw"),
    (os.path.join(PDF_DIR, "8202f7ba-126f-4feb-8e3d-3c72dccb39e3", "VFR-IFR COMMUNICATIONS (1).pdf"), "VFR-IFR Communications (1)", "vfr1"),
    (os.path.join(PDF_DIR, "3c13c35f-9a40-4240-8103-92d3c7dd3b77", "VFR-IFR COMMUNICATIONS (2).pdf"), "VFR-IFR Communications (2)", "vfr2"),
    (os.path.join(PDF_DIR, "5c8ab84a-451c-4fdd-a4bd-2a31e601f133", "VFR-IFR COMMUNICATIONS (3).pdf"), "VFR-IFR Communications (3)", "vfr3"),
    (os.path.join(PDF_DIR, "ae00b8f8-203e-4d64-8610-caccc4445c84", "VFR-IFR COMMUNICATIONS (4).pdf"), "VFR-IFR Communications (4)", "vfr4"),
    (os.path.join(PDF_DIR, "e5536a03-1f12-4613-a44c-eb601cb4aa20", "VFR-IFR COMMUNICATIONS (5).pdf"), "VFR-IFR Communications (5)", "vfr5"),
    (os.path.join(PDF_DIR, "9e7fd65e-26c6-46d9-9fcf-f8b566af7791", "VFR-IFR COMMUNICATIONS (6).pdf"), "VFR-IFR Communications (6)", "vfr6"),
    (os.path.join(PDF_DIR, "d19c2973-8bf2-4c90-a01d-d8edacc4407b", "VFR-IFR COMMUNICATIONS (7).pdf"), "VFR-IFR Communications (7)", "vfr7"),
    (os.path.join(PDF_DIR, "f898cac6-44f0-4119-8a68-b1a1a2c7de06", "INSTRUMENTATION.pdf"), "Instrumentation", "inst"),
    (os.path.join(PDF_DIR, "d0786e2e-4a42-4faf-8acc-b01f1f2eb645", "human performance and behavior.pdf"), "Human Performance & Behaviour", "human"),
    (os.path.join(PDF_DIR, "8718e538-6298-4bac-a3ce-5629655ed03c", "OPERATIONAL PROCEDURES.pdf"), "Operational Procedures", "ops"),
]

def clean(s):
    if not s: return ""
    return re.sub(r"\s+", " ", str(s).strip())[:600]

def read_pdf(path):
    if not os.path.isfile(path): return ""
    try:
        return "\n".join((p.extract_text() or "") for p in PdfReader(path).pages)
    except Exception as e:
        print("Error", path, e)
        return ""

# Match "A." or "A)" at start (option line)
opt_start_re = re.compile(r"^[ABCD][\.\)]\s*", re.I)
# Match "Answer:" or "Correct:" or "Key:"
correct_re = re.compile(r"^(?:Answer|Correct|Key)\s*[:\s]+\s*([ABCD])", re.I)
ref_re = re.compile(r"^Ref\s", re.I)

def parse_page_blocks(text):
    lines = [clean(l) for l in text.splitlines() if clean(l)]
    single_letter = re.compile(r"^[ABCD]$")
    skip = {"Question", "Choices", "Answers", "Correct", "Total", "Questions"}
    qs = []
    i = 0
    while i < len(lines):
        L = lines[i]
        if L in skip or ref_re.match(L):
            i += 1
            continue
        if single_letter.match(L):
            answers = []
            j = i
            while j < len(lines) and single_letter.match(lines[j]):
                answers.append(lines[j])
                j += 1
            if 4 <= len(answers) <= 6:
                nq = len(answers)
                opts = []
                k = i - 1
                while k >= 0 and len(opts) < nq * 4:
                    line = lines[k]
                    if line and len(line) > 2 and line not in skip and not ref_re.match(line) and not single_letter.match(line):
                        opts.insert(0, line)
                    k -= 1
                if len(opts) == nq * 4:
                    q_lines = []
                    while k >= 0 and not ref_re.match(lines[k]) and len(q_lines) < 20:
                        if lines[k] and len(lines[k]) > 8:
                            q_lines.insert(0, lines[k])
                        k -= 1
                    step = max(1, len(q_lines) // nq)
                    for idx in range(nq):
                        q_text = " ".join(q_lines[idx*step:(idx+1)*step]) if q_lines else ""
                        if len(q_text) < 10: continue
                        a,b,c,d = opts[idx*4:(idx+1)*4]
                        qs.append({"q": q_text, "A": a, "B": b, "C": c, "D": d, "correct": answers[idx]})
            i = j
            continue
        i += 1
    return qs

def parse_option_style(text):
    """Alternative parser: look for A. B. C. D. option blocks and Answer: X."""
    lines = text.splitlines()
    qs = []
    i = 0
    while i < len(lines):
        line = clean(lines[i])
        if not line:
            i += 1
            continue
        # Look for line that looks like "A. option text" or "A) option text"
        m = opt_start_re.match(line)
        if m:
            opts = {}
            q_lines = []
            j = i - 1
            while j >= 0 and len(q_lines) < 15:
                prev = clean(lines[j])
                if not prev or ref_re.match(prev) or prev in {"Question", "Choices", "Answers", "Correct", "Total", "Questions"}:
                    j -= 1
                    continue
                if opt_start_re.match(prev) or re.match(r"^[ABCD]$", prev):
                    break
                if len(prev) > 15:
                    q_lines.insert(0, prev)
                j -= 1
            while i < len(lines):
                L = clean(lines[i])
                if not L:
                    i += 1
                    continue
                if re.match(r"^[ABCD][\.\)]\s*", L, re.I):
                    letter = L[0].upper()
                    opts[letter] = re.sub(r"^[ABCD][\.\)]\s*", "", L, flags=re.I).strip()[:500]
                    i += 1
                    if len(opts) == 4:
                        break
                    continue
                if len(opts) > 0:
                    break
                i += 1
            if len(opts) == 4:
                correct_letter = None
                for k in range(i, min(i + 5, len(lines))):
                    L = clean(lines[k])
                    mc = correct_re.search(L)
                    if mc:
                        correct_letter = mc.group(1).upper()
                        break
                if not correct_letter:
                    correct_letter = "A"
                q_text = " ".join(q_lines)[:500] if q_lines else "Question"
                if len(q_text) > 20 and all(opts.get(x) for x in "ABCD"):
                    qs.append({
                        "q": q_text,
                        "A": opts["A"], "B": opts["B"], "C": opts["C"], "D": opts["D"],
                        "correct": correct_letter
                    })
            continue
        i += 1
    return qs

def main():
    out_dir = os.path.dirname(os.path.abspath(__file__))
    all_sets = []
    for path, name, sid in PDFS:
        if not os.path.isfile(path):
            print("Not found:", path)
            continue
        print("Extracting:", name)
        text = read_pdf(path)
        qs1 = parse_page_blocks(text)
        qs2 = parse_option_style(text)
        seen = set()
        qs = []
        for q in qs1 + qs2:
            key = (q["q"][:80], q.get("A", "")[:50])
            if key not in seen and len(q.get("q", "")) > 15 and all(q.get(x) for x in "ABCD"):
                seen.add(key)
                qs.append(q)
        print("  ->", len(qs), "questions")
        if not qs: continue
        size = 100
        for start in range(0, len(qs), size):
            subset = qs[start:start+size]
            all_sets.append({
                "id": f"{sid}-{start//size+1}",
                "name": f"{name} — Set {start//size+1} (Questions {start+1}-{start+len(subset)})",
                "questions": subset
            })
    js_path = os.path.join(out_dir, "questions.js")
    with open(js_path, "w", encoding="utf-8") as f:
        f.write("// Extracted from PDFs - run extract_pdf.py to regenerate\nwindow.AVIATION_SETS = ")
        f.write(json.dumps(all_sets, ensure_ascii=False, indent=2))
        f.write(";\n")
    print("Written:", js_path, "| Total sets:", len(all_sets))

if __name__ == "__main__":
    main()