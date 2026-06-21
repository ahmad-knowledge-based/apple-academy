#!/usr/bin/env python3
"""
Validator otomatis untuk bank soal Simulator Tes Apple Developer Academy.

Menjalankan pemeriksaan terhadap data/questions.json:
  1. Skema setiap soal benar (4 opsi, answer_index 0-3, id unik, field wajib).
  2. Tidak ada teks soal yang nyaris duplikat (peringatan, bukan error).
  3. Setiap soal dengan field "code" dieksekusi; output harus SAMA dengan
     options[answer_index] (mencegah salah kunci jawaban).
  4. Kuota minimum per kategori terpenuhi.

Keluar dengan kode 1 jika ada error (build gagal), 0 jika lolos.
Penggunaan: python validate.py
"""

import io
import json
import os
import sys
from contextlib import redirect_stdout
from difflib import SequenceMatcher

HERE = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_PATH = os.path.join(HERE, "data", "questions.json")

REQUIRED_FIELDS = ["id", "section", "category", "question", "options",
                   "answer_index", "hint", "explanation", "difficulty"]
VALID_SECTIONS = {"logic", "programming"}
VALID_DIFFICULTY = {"easy", "medium", "hard"}
MIN_PER_CATEGORY = 2          # kuota minimum tiap kategori
DUPLICATE_THRESHOLD = 0.85    # ambang kemiripan teks soal

LOGIC_CATEGORIES = [
    "deret_angka", "deret_huruf", "pola_matriks", "definisi_operator",
    "silogisme", "analogi", "sandi", "susunan_posisi", "urutan_komparatif",
    "probabilitas", "soal_cerita", "spasial", "klasifikasi", "jam",
    "logika_pernyataan",
]
PROGRAMMING_CATEGORIES = [
    "trace_aritmatika", "loop", "nested_loop", "while", "percabangan",
    "boolean", "pembagian_modulo", "array", "string", "fungsi",
    "oop_class", "oop_object", "oop_inheritance", "oop_encapsulation",
    "oop_polymorphism",
]
ALL_CATEGORIES = LOGIC_CATEGORIES + PROGRAMMING_CATEGORIES


# ---- util warna terminal (mati otomatis jika bukan TTY) -------------------
class C:
    def _wrap(code):
        return (lambda s: f"\033[{code}m{s}\033[0m") if sys.stdout.isatty() else (lambda s: s)
    red = _wrap("31")
    green = _wrap("32")
    yellow = _wrap("33")
    bold = _wrap("1")
    dim = _wrap("2")


def run_code(code):
    """Eksekusi pseudocode (Python runnable) dan kembalikan output yang dicetak."""
    buf = io.StringIO()
    sandbox = {"__builtins__": __builtins__}
    with redirect_stdout(buf):
        exec(code, sandbox)
    return buf.getvalue().strip()


def main():
    errors = []
    warnings = []

    if not os.path.exists(QUESTIONS_PATH):
        print(C.red(f"ERROR: {QUESTIONS_PATH} tidak ditemukan."))
        return 1

    with open(QUESTIONS_PATH, encoding="utf-8") as f:
        try:
            questions = json.load(f)
        except json.JSONDecodeError as e:
            print(C.red(f"ERROR: JSON tidak valid - {e}"))
            return 1

    if not isinstance(questions, list) or not questions:
        print(C.red("ERROR: questions.json harus berupa array yang tidak kosong."))
        return 1

    # ---- 1. validasi skema -------------------------------------------------
    seen_ids = set()
    for i, q in enumerate(questions):
        loc = q.get("id", f"#{i}")

        for field in REQUIRED_FIELDS:
            if field not in q:
                errors.append(f"[{loc}] field wajib '{field}' tidak ada.")

        qid = q.get("id")
        if qid in seen_ids:
            errors.append(f"[{loc}] id duplikat: '{qid}'.")
        seen_ids.add(qid)

        if q.get("section") not in VALID_SECTIONS:
            errors.append(f"[{loc}] section tidak valid: '{q.get('section')}'.")

        if q.get("category") not in ALL_CATEGORIES:
            errors.append(f"[{loc}] kategori tidak dikenal: '{q.get('category')}'.")

        if q.get("difficulty") not in VALID_DIFFICULTY:
            errors.append(f"[{loc}] difficulty tidak valid: '{q.get('difficulty')}'.")

        opts = q.get("options")
        if not isinstance(opts, list) or len(opts) != 4:
            errors.append(f"[{loc}] harus tepat 4 opsi (ditemukan {len(opts) if isinstance(opts, list) else 'bukan list'}).")
        elif len({str(o) for o in opts}) != 4:
            warnings.append(f"[{loc}] ada opsi yang teksnya identik.")

        ai = q.get("answer_index")
        if not isinstance(ai, int) or not (0 <= ai <= 3):
            errors.append(f"[{loc}] answer_index harus 0-3 (ditemukan {ai}).")

    # ---- 2. deteksi soal nyaris duplikat -----------------------------------
    # Bandingkan teks soal + kode, agar soal pseudocode yang berbagi kalimat
    # pembuka ("Apa keluaran ...") tidak menimbulkan false-positive.
    def dup_text(q):
        return (q.get("question", "") + "\n" + q.get("code", "")).strip()

    for a in range(len(questions)):
        for b in range(a + 1, len(questions)):
            qa = dup_text(questions[a])
            qb = dup_text(questions[b])
            ratio = SequenceMatcher(None, qa, qb).ratio()
            if ratio >= DUPLICATE_THRESHOLD:
                warnings.append(
                    f"[{questions[a].get('id')}] & [{questions[b].get('id')}] "
                    f"teks soal mirip ({ratio:.0%})."
                )

    # ---- 3. eksekusi kode & verifikasi kunci jawaban -----------------------
    code_count = 0
    code_ok = 0
    for q in questions:
        if "code" not in q:
            continue
        code_count += 1
        loc = q.get("id")
        try:
            output = run_code(q["code"])
        except Exception as e:
            errors.append(f"[{loc}] kode gagal dieksekusi: {type(e).__name__}: {e}")
            continue

        opts = q.get("options", [])
        ai = q.get("answer_index")
        if not isinstance(ai, int) or not (0 <= ai < len(opts)):
            continue  # sudah dilaporkan di langkah 1
        expected = str(opts[ai]).strip()
        if output != expected:
            errors.append(
                f"[{loc}] output kode '{output}' != kunci jawaban '{expected}' "
                f"(options[{ai}])."
            )
        else:
            code_ok += 1

    # ---- 4. kuota kategori -------------------------------------------------
    counts = {}
    for q in questions:
        counts[q.get("category")] = counts.get(q.get("category"), 0) + 1

    for cat in ALL_CATEGORIES:
        n = counts.get(cat, 0)
        if n < MIN_PER_CATEGORY:
            errors.append(f"kategori '{cat}' hanya {n} soal (minimum {MIN_PER_CATEGORY}).")

    # ---- ringkasan ---------------------------------------------------------
    print(C.bold("\n=== RINGKASAN BANK SOAL ==="))
    n_logic = sum(1 for q in questions if q.get("section") == "logic")
    n_prog = sum(1 for q in questions if q.get("section") == "programming")
    print(f"Total soal       : {len(questions)}  (Logic: {n_logic}, Programming: {n_prog})")
    print(f"Soal berkode     : {code_count}  (terverifikasi via eksekusi: {C.green(str(code_ok))})")

    print(C.bold("\nJumlah soal per kategori:"))
    for section, cats in (("LOGIC", LOGIC_CATEGORIES), ("PROGRAMMING", PROGRAMMING_CATEGORIES)):
        print(C.dim(f"  [{section}]"))
        for cat in cats:
            n = counts.get(cat, 0)
            mark = C.green("ok") if n >= MIN_PER_CATEGORY else C.red("KURANG")
            print(f"    {cat:<20} {n:>2}  {mark}")

    if warnings:
        print(C.yellow(C.bold(f"\nPERINGATAN ({len(warnings)}):")))
        for w in warnings:
            print(C.yellow(f"  ! {w}"))

    if errors:
        print(C.red(C.bold(f"\nERROR ({len(errors)}):")))
        for e in errors:
            print(C.red(f"  x {e}"))
        print(C.red(C.bold("\nVALIDASI GAGAL.")))
        return 1

    print(C.green(C.bold("\nVALIDASI LOLOS. Semua soal valid & kunci jawaban berkode terverifikasi.")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
