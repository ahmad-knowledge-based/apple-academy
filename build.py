#!/usr/bin/env python3
"""
build.py — menyuntik data/questions.json ke dalam index.html.

Alur:
  1. Jalankan validate.py terlebih dahulu. Jika GAGAL, build dibatalkan.
  2. Baca questions.json, lalu (opsional) acak urutan soal.
  3. Ganti isi di antara penanda /*QUESTIONS_START*/ dan /*QUESTIONS_END*/
     pada index.html dengan array soal.

Penggunaan:
  python build.py                # validasi + suntik
  python build.py --shuffle      # acak urutan soal sebelum disuntik
  python build.py --no-validate  # lewati validator (tidak disarankan)
"""

import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_PATH = os.path.join(HERE, "data", "questions.json")
INDEX_PATH = os.path.join(HERE, "index.html")
VALIDATE_PATH = os.path.join(HERE, "validate.py")

START = "/*QUESTIONS_START*/"
END = "/*QUESTIONS_END*/"


def main():
    args = sys.argv[1:]
    do_shuffle = "--shuffle" in args
    do_validate = "--no-validate" not in args

    if do_validate:
        print("→ Menjalankan validate.py ...")
        result = subprocess.run([sys.executable, VALIDATE_PATH])
        if result.returncode != 0:
            print("\nBuild DIBATALKAN: validasi gagal.")
            return 1

    with open(QUESTIONS_PATH, encoding="utf-8") as f:
        questions = json.load(f)

    if do_shuffle:
        import random
        random.shuffle(questions)
        print(f"→ Urutan {len(questions)} soal diacak.")

    payload = json.dumps(questions, ensure_ascii=False, indent=2)

    with open(INDEX_PATH, encoding="utf-8") as f:
        html = f.read()

    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    if not pattern.search(html):
        print(f"ERROR: penanda {START} ... {END} tidak ditemukan di index.html.")
        return 1

    # Gunakan fungsi replacement (bukan string) agar backslash pada payload
    # (mis. "\n" hasil json.dumps) TIDAK diinterpretasikan oleh re.sub.
    replacement = START + payload + END
    new_html = pattern.sub(lambda _: replacement, html, count=1)
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(new_html)

    print(f"\n✓ {len(questions)} soal disuntik ke index.html.")
    print("  Buka index.html di browser untuk memulai simulasi.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
