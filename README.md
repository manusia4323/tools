# The Pirates

CLI Python sederhana untuk mendokumentasikan teknologi dan memeriksa sinyal
halaman login pada satu website dalam setiap perintah.

## Instalasi

Gunakan Python 3.10 atau lebih baru:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Di Windows, aktifkan virtual environment dengan `.venv\Scripts\activate`.

## Cara pakai

Periksa satu halaman dan simpan cookie ke `sessions/`:
    python main.py recon -u https://example.com

Simpan laporan sebagai JSON atau Markdown.
Catatan: `--output` adalah flag global, jadi ditulis SEBELUM subcommand:

    python main.py --output json recon -u https://example.com
    python main.py --output md   recon -u https://example.com

```bash
python main.py recon -u https://example.com
```

Untuk memakai proxy lokal (contoh Burp/mitmproxy) atau tidak menyimpan cookie:

```bash
python main.py recon -u https://example.com --proxy http://127.0.0.1:8080 --no-save
```

Tampilkan cookie yang tersimpan untuk sebuah host:

```bash
python main.py cookies -H example.com
```

Cookie disimpan sebagai JSON lokal di `sessions/`. Jaga folder tersebut seperti
data sensitif dan jangan bagikan isinya.

## Penggunaan yang diizinkan

Gunakan hanya pada website milik sendiri atau website yang memang memberi izin
untuk diperiksa. Tool ini hanya mengambil satu halaman per perintah dan tidak
menjalankan pengujian injeksi, fuzzing, atau pengiriman payload.
