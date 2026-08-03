---
name: indonesian-commit-format
description: Use when committing or pushing git changes to enforce Indonesian commit message format starting with "perbaikan di bagian <detail_perbaikan>"
---

# Format Commit Git Bahasa Indonesia

Skill ini mengatur konvensi pesan commit Git agar selalu menggunakan format Bahasa Indonesia dengan awalan:

`perbaikan di bagian <modul/fitur/komponen>`

---

## 📌 Aturan Pesan Commit

1. **Format Wajib**:
   ```bash
   git commit -m "perbaikan di bagian <penjelasan singkat bagian yang diperbaiki>"
   ```

2. **Pedoman Penulisan**:
   - Gunakan huruf kecil (lowercase) untuk pesan commit.
   - Jelaskan secara spesifik bagian atau fitur yang mengalami perubahan/perbaikan.
   - Singkat, jelas, dan menggambarkan perubahan kode yang dilakukan.

---

## 💡 Contoh Penggunaan

| Kasus Perubahan | Contoh Pesan Commit |
| :--- | :--- |
| Memperbaiki link / badge pada README | `git commit -m "perbaikan di bagian link profile dan badge readme"` |
| Memperbaiki bug pada fungsi kalkulasi | `git commit -m "perbaikan di bagian kalkulasi logika pembayaran"` |
| Memperbaiki tampilan UI / CSS header | `git commit -m "perbaikan di bagian tampilan responsive header"` |
| Memperbaiki error handling API | `git commit -m "perbaikan di bagian penanganan error endpoint auth"` |

---

## 🚀 Alur Eksekusi Git Commit & Push

Ketika melakukan commit dan push:
```bash
git add .
git commit -m "perbaikan di bagian <bagian yang diubah>"
git push origin <branch>
```
