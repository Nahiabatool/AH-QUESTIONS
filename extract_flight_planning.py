#!/usr/bin/env python3
"""Extract questions from FLIGHT PLANNING.pdf and output QUIZ_QUESTIONS_SET2 for questions.js"""
import re
import os
import json

try:
    from pypdf import PdfReader
except ImportError:
    from PyPDF2 import PdfReader

PDF_PATH = r"c:\Users\Abbas Haider\AppData\Roaming\Cursor\User\workspaceStorage\59c9cd72e8be94a90f18f038d506a7a1\pdfs\f2c18fae-73e6-4d88-953b-df5db2860c9e\FLIGHT PLANNING.pdf"

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

    skip = {"Question", "Choices", "Answers", "Correct", "Total", "Questions", "FLIGHT PLANNING"}
    ref_re = re.compile(r"^Ref\s", re.I)
    single_letter = re.compile(r"^[ABCD]$")
    page_re = re.compile(r"^-- \d+ of \d+ --$")

    # Collect all correct answer letters in order (they appear as single A/B/C/D lines in rows)
    correct_letters = []
    # Collect all option lines (groups of 4) - lines that are not Ref, not single letter, not skip
    all_option_lines = []
    # Collect question text lines (before Ref blocks) - we'll need to associate with options
    question_blocks = []  # list of list of lines per question

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
            # Collect consecutive single letters (one per question in this batch)
            batch = []
            while i < len(lines) and single_letter.match(lines[i]):
                batch.append(lines[i])
                i += 1
            if batch:
                correct_letters.extend(batch)
            # Next might be option lines for next batch - we'll collect when we see 4 lines before a Ref or single letter
            continue
        # Otherwise it's content: could be question text or option text
        current_block.append(L)
        i += 1
    if current_block:
        question_blocks.append(current_block)

    # Now we have correct_letters (818 entries). We need to split question_blocks into individual questions.
    # question_blocks are separated by Ref - so each block might have multiple questions (multiple lines).
    # Option lines: in the PDF, after Ref we have 4 lines per question (options A B C D). So we need to find
    # where the option lines are. They appear after "Ref" lines and before the single-letter "Correct" row.
    # Re-parse: collect lines in order; when we see Ref we're past question text; then we get option lines (every 4 = one question); then single letters = correct.
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

    # Build question texts: we need n_questions texts. question_blocks had blocks separated by Ref; each block can have several questions. So total lines in question_blocks might be way more than n_questions. Heuristic: assume we have n_questions questions and we have sum(len(b) for b in question_blocks) lines. So we need to split the concatenated question lines into n_questions. Simple split: take first line as Q1, then try to detect Q2 start (e.g. line starting with "(" or "Given" or "How" or "What" or "Which" or "For" or "An" or "The" or "You" or "When" or "A "). So we scan and whenever we see a line that looks like a question start we start a new question. Then we have list of question text lines per question. Join with space.
    all_q_lines = []
    for b in question_blocks:
        all_q_lines.extend(b)

    # Split into individual questions: many questions start with "(Refer" or "Given" or "How" or "What" or "Which" or "For" or "An aircraft" or "You " or "When" or "At " or "The " or "A " or "In " or "From " or "During " or "If " or "Your " or "Minimum " or "Standard " etc.
    start_pattern = re.compile(
        r"^(\(Refer|Given|How|What|Which|For\s|An\s|You\s|When|At\s|The\s|A\s|In\s|From\s|During|If\s|Your|Minimum|Standard|VFR|An aircraft|A flight|A descent|A public|A turbine|A jet|A mountain|Using the|Repetitive|Which of|From the|It is possible|Your aircraft|The term|The planned|The cruising|The navigation|The still|The alternate|The fuel|The outbound|The option|The total|The symbol|The frequency|The minimum|The maximum|The correct|The estimated|The endurance|The reserve|The remaining|The distance|The time|The speed|The pressure|The wind|The heading|The track|The ground)",
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

    # We might have too many or too few q_texts. We need exactly n_questions. If we have more, take first n_questions. If fewer, pad with "Question N".
    if len(q_texts) > n_questions:
        q_texts = q_texts[:n_questions]
    while len(q_texts) < n_questions:
        q_texts.append("Question " + str(len(q_texts) + 1))

    # Build output: each item { question, options: [A,B,C,D], correct: 0-3 }
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

    # Write as JavaScript
    out_dir = os.path.dirname(os.path.abspath(__file__))
    js_path = os.path.join(out_dir, "flight_planning_set2.js")
    with open(js_path, "w", encoding="utf-8") as f:
        f.write("// FLIGHT PLANNING.pdf - Set 2 (" + str(len(out)) + " questions)\n")
        f.write("const QUIZ_QUESTIONS_SET2 = ")
        f.write(json.dumps(out, ensure_ascii=False, indent=2))
        f.write(";\n")
    print("Written", len(out), "questions to", js_path)

if __name__ == "__main__":
    main()
