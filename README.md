# Simulator Tes Masuk — Apple Developer Academy Indonesia

Simulator latihan tes (mock test) yang ringan, terstruktur, dan mudah dikembangkan.
Meniru format tes masuk online: **2 section, durasi 120 menit, semua pilihan ganda (A–D)**.
Sesi simulasi mengambil **25 soal Logic + 15 soal Programming/OOP** dengan timer 60 menit.

Prinsip desain: **bank soal (data) terpisah dari tampilan (UI)**, dilengkapi
validator otomatis yang bahkan **mengeksekusi kode** tiap soal pseudocode untuk
memastikan kunci jawaban tidak salah.

```
.
├─ data/questions.json   # bank soal — SATU-SATUNYA sumber kebenaran
├─ validate.py           # validator otomatis (skema, duplikat, eksekusi kode, kuota)
├─ index.html            # simulator (single-file: HTML+CSS+JS, tanpa dependensi)
├─ build.py              # menyuntik questions.json ke index.html (+ opsi acak)
└─ README.md
```

---

## 1. Menjalankan simulator

Cukup **buka `index.html` di browser** (klik dua kali). Tidak perlu server,
instalasi, atau koneksi internet. Data soal sudah tertanam di dalam file.

- Soal **dan** urutan opsi diacak setiap kali simulasi dimulai.
- Maksimal 3 soal per kategori dalam satu sesi agar tidak terasa berulang.
- Pintasan keyboard: `←` / `→` navigasi, `1`–`4` memilih opsi A–D.
- State disimpan **hanya di memori** (tanpa localStorage/sessionStorage).

> Mode **Fokus Kategori** (mis. hanya OOP atau hanya deret angka) tersedia di
> menu dropdown pada layar awal.

---

## 2. Menjalankan validator

```bash
python validate.py
```

Validator akan **menggagalkan build** (exit code 1) jika ada pelanggaran:

1. **Skema** — setiap soal punya tepat 4 opsi, `answer_index` 0–3, `id` unik,
   dan seluruh field wajib lengkap.
2. **Duplikat** — soal yang teksnya nyaris sama akan **diperingatkan**
   (warning, tidak menggagalkan build).
3. **Eksekusi kode (paling penting)** — untuk setiap soal yang punya field
   `code`, kodenya **dieksekusi** dan output-nya harus **sama persis** dengan
   `options[answer_index]`. Ini mencegah salah kunci jawaban.
4. **Kuota kategori** — minimum 2 soal per kategori; kategori yang kurang akan dilaporkan.

Validator mencetak ringkasan: jumlah soal per kategori, jumlah soal berkode yang
terverifikasi, daftar peringatan, dan daftar error (bila ada).

> **Catatan keamanan:** validator menjalankan `exec()` atas isi field `code`.
> Field `code` ditulis sebagai **Python yang runnable** (pseudocode bergaya
> language-agnostic). Karena `questions.json` adalah konten yang Anda kontrol
> sendiri, ini aman; jangan memuat bank soal dari sumber tidak tepercaya.

---

## 3. Membangun ulang index.html dari bank soal

Setelah mengedit `data/questions.json`, suntik ulang datanya ke `index.html`:

```bash
python build.py             # validasi dulu, lalu suntik
python build.py --shuffle   # acak urutan soal saat disuntik
python build.py --no-validate   # lewati validator (tidak disarankan)
```

`build.py` menjalankan `validate.py` lebih dulu dan **membatalkan** proses bila
validasi gagal, lalu mengganti blok di antara penanda
`/*QUESTIONS_START*/ ... /*QUESTIONS_END*/` di `index.html`.

---

## 4. Cara menambah soal baru

Cukup **edit `data/questions.json`** (tidak perlu menyentuh UI), lalu jalankan
`python build.py`. Format setiap soal:

```json
{
  "id": "L46",
  "section": "logic",
  "category": "deret_angka",
  "question": "Lanjutkan deret: 5, 10, 20, 40, ...",
  "code": "x = 5\nprint(x * 2)",
  "options": ["60", "80", "70", "50"],
  "answer_index": 1,
  "hint": "Petunjuk tanpa membocorkan jawaban.",
  "explanation": "Pembahasan ringkas mengapa jawaban itu benar.",
  "difficulty": "easy"
}
```

Aturan:

- `id` harus **unik**. Konvensi: `L##` untuk Logic, `P##` untuk Programming.
- `section`: `"logic"` atau `"programming"`.
- `category`: salah satu dari daftar di bawah.
- `options`: **tepat 4** string. `answer_index`: 0–3.
- `code` **opsional** — isi hanya untuk soal pseudocode. **Wajib berupa Python
  runnable**, dan output `print(...)`-nya harus persis sama dengan
  `options[answer_index]` (akan dicek validator).
- Jalankan `python validate.py` untuk memastikan tidak ada yang rusak.

### Daftar kategori

**Logic:** `deret_angka`, `deret_huruf`, `pola_matriks`, `definisi_operator`,
`silogisme`, `analogi`, `sandi`, `susunan_posisi`, `urutan_komparatif`,
`probabilitas`, `soal_cerita`, `spasial`, `klasifikasi`, `jam`, `logika_pernyataan`

**Programming:** `trace_aritmatika`, `loop`, `nested_loop`, `while`,
`percabangan`, `boolean`, `pembagian_modulo`, `array`, `string`, `fungsi`,
`oop_class`, `oop_object`, `oop_inheritance`, `oop_encapsulation`, `oop_polymorphism`

---

## 5. Fitur simulator

- Progress bar + indikator `n / total`.
- Penghitung live: benar (hijau ✓) dan salah (merah ✕).
- Label section (Logic / Programming) + kategori + tingkat kesulitan per soal.
- Soal pseudocode tampil dalam blok monospace.
- Feedback langsung: opsi benar jadi hijau, opsi salah jadi merah, lalu pembahasan
  muncul. Tombol **Lihat petunjuk** yang bisa dibuka/tutup.
- Navigasi Sebelumnya / Berikutnya.
- **Timer mundur 60 menit** di pojok atas; berubah kuning lalu merah saat mepet;
  otomatis mengumpulkan jawaban saat waktu habis.
- Layar hasil: ring persentase skor, rincian Logic vs Programming, jumlah soal
  kosong, waktu terpakai, tombol **Tinjau Jawaban** dan **Ulangi**.
- Responsif sampai layar ponsel; fokus keyboard terlihat; menghormati
  `prefers-reduced-motion`.

---

## 6. Kenapa single-file HTML (bukan Streamlit)?

| | Single-file HTML (dipakai) | Python + Streamlit |
|---|---|---|
| Setup | **Nol** — klik untuk buka | `pip install streamlit` + `streamlit run` |
| Distribusi | Satu file `.html` | Perlu Python + dependensi |
| Offline | Ya | Perlu proses server lokal |
| Timer realtime | Mulus (JS native) | Perlu rerun/polling, kurang halus |

Untuk simulator latihan yang ringan dan portabel, single-file HTML menang telak.
Python tetap dipakai untuk hal yang memang cocok: **validasi & build** (`validate.py`,
`build.py`) — termasuk mengeksekusi kode soal untuk memverifikasi kunci jawaban,
yang sulit dilakukan andal di sisi browser.

---

## Catatan

Soal di repo ini **buatan sendiri** untuk latihan bergaya tes masuk, bukan
bocoran soal asli. Tujuannya melatih pola berpikir (TPA/IQ/SNBT-style) dan dasar
pemrograman/OOP.
