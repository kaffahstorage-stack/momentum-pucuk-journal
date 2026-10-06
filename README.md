# Momentum Pucuk — Jurnal MT5

Tampilan website utuh ada di **index.html**. Tidak perlu npm, React, atau build.

## GitHub Pages
Settings → Pages → Build and deployment → Source: **Deploy from a branch** → Branch: **main**, folder **/(root)** → Save.

Alamat yang diharapkan setelah GitHub Pages aktif:
https://kaffahstorage-stack.github.io/momentum-pucuk-journal/

## Hubungkan MT5 Windows
1. Download repository (Code → Download ZIP), lalu ekstrak.
2. Pasang Python 3.11/3.12 64-bit dari python.org. Buka MT5 dan login.
3. Klik `start_journal.bat`. Pemasangan awal membutuhkan internet.
4. Salin kode penghubung dari jendela tersebut ke website, lalu klik Hubungkan.
5. Izinkan akses jaringan lokal jika browser meminta. Bila browser memblokir akses dari HTTPS GitHub Pages ke localhost, gunakan `http://127.0.0.1:8766`, yang menyajikan HTML identik.
6. Biarkan MT5 dan penghubung berjalan. Website memperbarui data tiap 5 detik.

Jika memiliki beberapa terminal MT5: `py -3 mt5_bridge.py --terminal "C:\Program Files\Nama MT5\terminal64.exe"`.

## Apa yang otomatis
- Membaca posisi dan history deals dari terminal yang sudah login; tidak meminta kredensial broker.
- Menggabungkan deal menurut position ID, termasuk partial close dan entry bertahap.
- Menyimpan snapshot di `%LOCALAPPDATA%\MomentumPucukJournal\journal.sqlite`, dipisahkan menurut akun/server.
- Menghitung win rate dari profit bersih, profit factor, expectancy dalam mata uang akun, dan drawdown hasil tertutup.
- Profit bersih menjumlahkan profit + commission + swap + fee dari deal yang memiliki position ID. Charge terpisah tanpa position ID tidak dialokasikan.
- Reversal netting dan posisi dengan history tidak lengkap ditandai Perlu diperiksa dan dikeluarkan dari statistik selesai.

## Memisahkan strategi TP pucuk
Beri komentar **PUCUK** atau gunakan magic number khusus pada order, lalu gunakan filter website. Label TP broker hanya menyatakan penutupan karena TP menurut MT5; bukan bukti bahwa TP tersebut persis pucuk candle. Tidak mendeteksi indikator Pine secara langsung dan tidak menghitung R tanpa informasi SL awal yang terverifikasi.

## Batas koneksi
Penghubung hanya mendengarkan di PC lokal (127.0.0.1), menggunakan kode pairing, dan mengizinkan origin GitHub akun ini. Jangan bagikan kode pairing. Kode hanya tersimpan di browser jika opsi Ingat kode dipilih. Database dan kode tidak diunggah ke GitHub. Untuk menghapus pairing, hentikan bridge, hapus pairing-key.txt pada folder data, lalu jalankan lagi.

Website GitHub dapat dibuka dari HP, tetapi tidak dapat membaca penghubung PC lewat 127.0.0.1 milik HP. Sinkron lintas perangkat memerlukan backend terautentikasi tambahan. Saat PC mati, data tidak diperbarui; history dibaca ulang ketika bridge kembali hidup. Restart bridge dalam keadaan offline belum memuat snapshot lama sampai akun dikenali.

## Validasi
Unit test agregasi deal dapat dijalankan dengan `py -3 -m unittest test_bridge.py`. Integrasi terminal MT5 nyata harus diuji di PC Windows pengguna.
