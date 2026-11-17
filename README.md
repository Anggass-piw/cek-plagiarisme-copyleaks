# Cek Plagiarisme (Copyleaks)

Aplikasi FastAPI untuk mengirim PDF/DOCX ke Copyleaks, menerima hasil lewat webhook, lalu membuat laporan PDF ringkas. Upload, polling, dan unduh laporan dilindungi HTTP Basic Auth. Webhook memakai rahasia acak di URL; endpoint `/healthz` hanya untuk pemeriksaan layanan.

Panduan lengkap dari persiapan akun sampai pengujian server: [`PANDUAN-DEPLOY.md`](PANDUAN-DEPLOY.md).

## Deploy ke Render Free untuk uji coba

1. Buat akun Copyleaks dan periksa dashboard apakah API access tersedia untuk akunmu. Simpan email dan API key. **Sandbox memberi hasil tiruan gratis; scan produksi memerlukan API access/kredit, dan kredit produksi gratis untuk akun baru belum terverifikasi.** Jangan matikan sandbox atau membeli kredit tanpa memeriksa dashboard dan menyetujui biayanya.
2. Setelah repository ditinjau dan dipublikasikan, di Render pilih **New → Blueprint**, lalu sambungkan repository ini. Render membaca `render.yaml` dan meminta `APP_USERNAME`, `APP_PASSWORD`, `COPYLEAKS_EMAIL`, dan `COPYLEAKS_KEY`. Gunakan password panjang. `WEBHOOK_SECRET` dibuat otomatis, dan URL HTTPS publik Render dipakai otomatis untuk callback.
3. Biarkan `COPYLEAKS_SANDBOX=true`, tunggu deploy sukses, lalu buka URL `onrender.com` yang diberikan Render dan masuk dengan kredensial aplikasi.
4. Uji dengan dokumen yang tidak sensitif. Sandbox memang mengembalikan data tiruan; tujuannya hanya memastikan upload → webhook → PDF bekerja, bukan mengukur plagiarisme sebenarnya.
5. Baru setelah kamu memastikan akses API dan biaya scan produksi di dashboard Copyleaks, ubah `COPYLEAKS_SANDBOX` menjadi `false` di Render jika memang ingin scan sungguhan.

### Batasan paket gratis

Render Free tidur setelah 15 menit tanpa trafik masuk; bangun kembali biasanya sekitar satu menit. Berkas hasil dan antrean job di aplikasi ini hanya disimpan di RAM, jadi restart/tidur atau deploy dapat menghilangkan job yang belum selesai. Render menyatakan paket gratis ditujukan untuk uji coba/hobi, bukan produksi. Jangan andalkan setup ini untuk layanan selalu tersedia atau dokumen penting. [Batasan resmi Render Free](https://render.com/docs/free), [variabel URL publik Render](https://render.com/docs/environment-variables).

## Server Docker sendiri dengan domain

Untuk VPS yang sudah memiliki Docker dan domain HTTPS:

1. Salin `.env.example` ke `.env` dan isi `DOMAIN`, `PUBLIC_URL`, login aplikasi, email/key Copyleaks, serta `WEBHOOK_SECRET` (buat dengan `openssl rand -hex 32`).
2. Pertahankan `COPYLEAKS_SANDBOX=true` saat menguji.
3. Jalankan `docker compose up -d --build`, lalu buka `https://DOMAIN`.

Compose menjalankan Caddy sebagai reverse proxy TLS. Arahkan DNS domain ke alamat IP VPS terlebih dahulu. Jangan expose aplikasi tanpa password.

## Data dan retensi

Dokumen yang diunggah dikirim ke Copyleaks untuk dipindai. Proyek ini meminta Copyleaks menghapus scan setelah **1 jam** dari selesainya pemindaian (`expiration: 1`); laporan sementara di RAM server dihapus saat diunduh atau kedaluwarsa setelah paling lama 2 jam. Hindari mengunggah dokumen sensitif saat masih dalam sandbox/testing, dan tinjau kebijakan privasi Copyleaks sebelum penggunaan nyata.

## Catatan teknis

- Job dan PDF tersimpan di memori proses, sehingga aplikasi harus dijalankan dengan satu worker. Render Blueprint menggunakan satu proses.
- Dokumen dibatasi maksimal 10 MB dan hanya `.pdf`/`.docx`.
- Ringkasan skor/sumber mengambil field dari webhook; validasi hasil sandbox terlebih dahulu sebelum mengandalkan PDF untuk keperluan akademik.
- API scan sungguhan mengonsumsi kredit sesuai akses/produk Copyleaks. Mode sandbox adalah hasil mock dan tidak boleh dipakai untuk menilai isi dokumen.
