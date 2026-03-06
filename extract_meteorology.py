#!/usr/bin/env python3
"""Extract questions from METEOROLOGY.pdf and output QUIZ_QUESTIONS_SET4."""
import re
import os
import json

try:
    from pypdf import PdfReader
except ImportError:
    from PyPDF2 import PdfReader

PDF_PATH = r"c:\Users\Abbas Haider\AppData\Roaming\Cursor\User\workspaceStorage\59c9cd72e8be94a90f18f038d506a7a1\pdfs\5dd91ff2-baea-4934-91aa-3d4a77ef72ef\METEOROLOGY.pdf"

def clean(s):
    if not s:
        return ""
    return re.sub(r"\s+", " ", str(s).strip())

def read_pdf(path):
    if not os.path.isfile(path):
        print("PDF not found:", path)
        return ""
    try:
        return "\n".join((p.extract_text() or "") for p in PdfReader(path).pages)
    except Exception as e:
        print("Error reading PDF:", e)
        return ""

def main():
    text = read_pdf(PDF_PATH)
    if not text:
        return
    lines = [clean(l) for l in text.splitlines() if clean(l)]

    skip = {"Question", "Choices", "Answers", "Correct", "Total", "Questions", "FLIGHT PLANNING", "RADIO NAVIGATION", "METEOROLOGY"}
    ref_re = re.compile(r"^Ref\s", re.I)
    single_letter = re.compile(r"^[ABCD]$")
    page_re = re.compile(r"^-- \d+ of \d+ --$")

    question_blocks = []
    i = 0
    current_block = []
    while i < len(lines):
        L = lines[i]
        if L in skip or page_re.match(L) or (L.isdigit() and len(L) <= 4):
            i += 1
            continue
        if ref_re.match(L):
            if current_block:
                question_blocks.append(current_block)
                current_block = []
            i += 1
            continue
        if single_letter.match(L):
            batch = []
            while i < len(lines) and single_letter.match(lines[i]):
                batch.append(lines[i])
                i += 1
            continue
        current_block.append(L)
        i += 1
    if current_block:
        question_blocks.append(current_block)

    option_groups = []
    correct_list = []
    in_ref_section = False
    option_buffer = []
    next_letter_row_is_correct = False
    ref_count_this_block = 0
    i = 0
    while i < len(lines):
        L = lines[i]
        if L in skip or page_re.match(L):
            i += 1
            continue
        if ref_re.match(L):
            if not in_ref_section:
                next_letter_row_is_correct = True
                ref_count_this_block = 0
            in_ref_section = True
            ref_count_this_block += 1
            i += 1
            continue
        if single_letter.match(L):
            batch = []
            while i < len(lines) and single_letter.match(lines[i]):
                batch.append(lines[i].upper())
                i += 1
            if batch and next_letter_row_is_correct and ref_count_this_block > 0:
                n = min(ref_count_this_block, len(batch))
                correct_list.extend(batch[:n])
            next_letter_row_is_correct = False
            in_ref_section = False
            ref_count_this_block = 0
            continue
        if in_ref_section and len(L) > 2:
            option_buffer.append(L)
            if len(option_buffer) == 4:
                option_groups.append(option_buffer)
                option_buffer = []
        i += 1

    n_questions = len(correct_list)
    letter_to_idx = {"A": 0, "B": 1, "C": 2, "D": 3}

    all_q_lines = []
    for b in question_blocks:
        all_q_lines.extend(b)

    start_pattern = re.compile(
        r"^(\(Refer|Given|How|What|Which|For\s|An\s|You\s|When|At\s|The\s|A\s|In\s|From\s|During|If\s|Your|Going|In the|The amount|The tropopause|The thickness|Which layer|Which one)",
        re.I
    )
    q_texts = []
    current = []
    for line in all_q_lines:
        if start_pattern.match(line) and current and len(current) < 15:
            q_texts.append(" ".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        q_texts.append(" ".join(current))

    if len(q_texts) > n_questions:
        q_texts = q_texts[:n_questions]
    while len(q_texts) < n_questions:
        q_texts.append("Question " + str(len(q_texts) + 1))

    out = []
    for idx in range(n_questions):
        q = q_texts[idx][:800] if idx < len(q_texts) else "Question " + str(idx + 1)
        if idx < len(option_groups):
            opts = option_groups[idx]
        else:
            opts = ["Option A", "Option B", "Option C", "Option D"]
        correct_letter = correct_list[idx] if idx < len(correct_list) else "A"
        correct_idx = letter_to_idx.get(correct_letter.upper(), 0)
        out.append({
            "question": q,
            "options": opts,
            "correct": correct_idx
        })

    out_dir = os.path.dirname(os.path.abspath(__file__))
    js_path = os.path.join(out_dir, "meteorology_set4.js")
    with open(js_path, "w", encoding="utf-8") as f:
        f.write("// METEOROLOGY.pdf - Set 4 (" + str(len(out)) + " questions)\n")
        f.write("const QUIZ_QUESTIONS_SET4 = ")
        f.write(json.dumps(out, ensure_ascii=False, indent=2))
        f.write(";\n")
    print("Written", len(out), "questions to", js_path)

if __name__ == "__main__":
    main()
