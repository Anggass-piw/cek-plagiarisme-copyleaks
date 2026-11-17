# Panduan langkah demi langkah: jalankan Cek Plagiarisme Copyleaks di server

Panduan ini memakai **Render Free** agar tidak perlu membeli VPS atau domain sendiri. Render akan memberi alamat `https://...onrender.com` yang bisa dipakai Copyleaks untuk mengirim webhook. Ini cocok untuk uji coba, bukan layanan produksi yang harus selalu aktif.

## Yang perlu disiapkan

- Akun GitHub untuk menyimpan source code.
- Akun Render untuk menjalankan aplikasi.
- Akun Copyleaks dengan API access serta email dan API key API.
- Dokumen PDF/DOCX kecil untuk pengujian. Untuk sandbox, jangan pakai dokumen sensitif.

**Tentang biaya:** Copyleaks Sandbox memang dapat dipakai untuk menguji integrasi, tetapi hasilnya data tiruan. Scan sungguhan menggunakan kredit; kredit produksi gratis untuk akun baru belum terverifikasi. Jangan mengaktifkan mode produksi atau membeli kredit sampai kamu sendiri memeriksa akses dan harga di dashboard Copyleaks.

---

## Langkah 1 — Periksa isi proyek

Source proyek berisi backend FastAPI, halaman upload, generator PDF, Dockerfile, dan `render.yaml`. Login HTTP Basic melindungi halaman serta API. `WEBHOOK_SECRET` membatasi callback Copyleaks, sedangkan `/healthz` dibiarkan terbuka khusus untuk health check Render.

File `.env` tidak boleh dipublikasikan. Repository hanya boleh memuat `.env.example`, yang berisi contoh nama variabel tanpa kredensial asli. Sebelum mengunggah ke GitHub, tinjau README dan daftar file proyek; jangan lanjutkan publikasi sebelum menyetujuinya.

## Langkah 2 — Siapkan Copyleaks API

1. Buat/masuk ke akun melalui [Copyleaks API](https://api.copyleaks.com/signup).
2. Di dashboard, pastikan akunmu punya akses API, lalu catat email akun dan API key. Simpan seperti password; jangan tempel ke source code atau commit GitHub.
3. Jika API access atau API key tidak tersedia, berhenti di sini dan tanyakan ketersediaannya ke Copyleaks. Aplikasi belum bisa mengirim scan tanpa kredensial tersebut.
4. Untuk uji integrasi, biarkan sandbox aktif. Dokumentasi Copyleaks menyebut sandbox mengembalikan mock result, bukan analisis dokumen sungguhan, dan membatasi 100 scan sandbox per jam. [Submit File dan Sandbox](https://docs.copyleaks.com/reference/actions/authenticity/submit-file)

Aplikasi mengirim `expiration: 1`, agar Copyleaks menghapus scan satu jam setelah scan selesai. [Dokumentasi submit-file](https://docs.copyleaks.com/reference/actions/authenticity/submit-file)

## Langkah 3 — Tinjau proyek sebelum publikasi

1. Buka `README.md`, `PANDUAN-DEPLOY.md`, dan daftar file di proyek.
2. Pastikan source tidak memuat `.env`, API key, password, atau dokumen pribadi.
3. Baru setelah kamu menyetujui konten, buat repository GitHub **Public** bernama misalnya `cek-plagiarisme-copyleaks` dan unggah source. Nama ini hanya contoh; repository belum dibuat oleh panduan ini.

Sesuai preferensimu, publikasi harus menunggu persetujuan eksplisit setelah kamu melihat README dan daftar file. Jangan mengubah repository menjadi public jika ada rahasia di dalamnya.

## Langkah 4 — Buat layanan di Render

1. Masuk ke [Render Dashboard](https://dashboard.render.com/).
2. Pilih **New → Blueprint**.
3. Hubungkan repository GitHub yang sudah disetujui dan dipublikasikan.
4. Render akan membaca `render.yaml`. Pilih layanan `cek-plagiarisme-copyleaks` dan plan **Free**.
5. Saat diminta, isi variabel berikut langsung di form rahasia Render:
   - `APP_USERNAME`: nama login untuk membuka aplikasi.
   - `APP_PASSWORD`: password kuat khusus aplikasi.
   - `COPYLEAKS_EMAIL`: email akun Copyleaks yang punya API access.
   - `COPYLEAKS_KEY`: API key Copyleaks.
6. Pastikan `COPYLEAKS_SANDBOX` masih `true`. `WEBHOOK_SECRET` dibuat otomatis oleh Blueprint; jangan bagikan nilainya.
7. Klik untuk membuat layanan dan tunggu proses build/deploy selesai.

Tidak perlu mengisi `PUBLIC_URL` pada Render. Saat berjalan, aplikasi membaca `RENDER_EXTERNAL_URL` yang diberikan Render untuk membentuk alamat webhook HTTPS. [Variabel URL publik Render](https://render.com/docs/environment-variables)

## Langkah 5 — Cek deployment

1. Di dashboard Render, buka halaman service dan salin URL publik `https://...onrender.com`.
2. Buka `https://...onrender.com/healthz`. Jika siap, responsnya `{"ok":true}`. Endpoint ini hanya health check.
3. Buka URL utama. Browser akan meminta username dan password HTTP Basic yang dibuat pada Langkah 4.
4. Jika URL belum bisa dibuka, lihat **Events** dan **Logs** di Render. Jangan menaruh API key/password di chat atau di log.

## Langkah 6 — Uji alur sandbox

1. Gunakan file uji PDF/DOCX kecil yang tidak sensitif.
2. Login dan unggah file. Aplikasi mengirim file ke API Copyleaks, lalu menunggu webhook `completed`/`error`.
3. Setelah selesai, unduh PDF laporan.
4. Pastikan laporan menandai **MODE SANDBOX**. Nilai dan sumber pada sandbox adalah data simulasi; ini hanya membuktikan alur upload → Copyleaks → webhook → PDF tersambung, bukan menguji akurasi pada dokumen tersebut.
5. Jika PDF tidak muncul, lihat log Render dan periksa tabir berikut: API access/key, URL callback publik, dan hasil webhook. Copyleaks mengharuskan endpoint webhook menjawab dengan HTTP 2xx dalam 70 detik; callback yang gagal dicoba ulang hingga 17 kali. [Aturan webhook resmi](https://docs.copyleaks.com/reference/data-types/authenticity/webhooks/overview)

## Langkah 7 — Jika ingin scan sungguhan

Jangan lakukan langkah ini sebelum kamu sendiri memeriksa akses API dan harga/kredit di dashboard Copyleaks.

1. Pastikan akun punya API access dan kredit yang cukup untuk scan.
2. Pertimbangkan bahwa dokumen asli akan dikirim ke Copyleaks; aplikasi mengatur penghapusan scan Copyleaks setelah satu jam, tetapi PDF sementara tetap berada di RAM aplikasi sampai diunduh atau job kedaluwarsa (maksimal dua jam).
3. Jika kamu setuju menggunakan kredit, ubah `COPYLEAKS_SANDBOX` di Render dari `true` menjadi `false`, simpan perubahan, lalu deploy/restart sesuai instruksi Render.
4. Lakukan hanya satu scan uji pada dokumen yang memang boleh diproses oleh layanan itu. Laporan ini tetap bukan laporan Turnitin dan skor kemiripan bukan vonis plagiarisme.

Tidak ada kredit yang dibeli dan tidak ada mode produksi yang diaktifkan oleh panduan ini.

## Batasan Render Free yang perlu dipahami

- Render menghentikan service gratis setelah 15 menit tanpa trafik masuk. Request berikutnya membangunkannya lagi, biasanya perlu sekitar satu menit.
- Job dan PDF saat ini disimpan di RAM, bukan database. Restart atau deploy ketika scan sedang berlangsung dapat membuat job hilang.
- Copyleaks mensyaratkan callback selesai dalam 70 detik; Render yang baru bangun bisa membuat callback pertama terlambat. Copyleaks menyediakan retry, tetapi hasil dapat tertunda. Karena itu kombinasi ini hanya untuk uji coba/hobi, bukan layanan yang perlu selalu tersedia. [Batas resmi Render Free](https://render.com/docs/free)
- Render mencatat Free sebagai layanan untuk uji coba/hobi dan memberi batas pemakaian bulanan. Pantau penggunaan; jangan tambahkan metode pembayaran atau mengubah plan tanpa persetujuanmu.

## Troubleshooting singkat

- **Render tidak mau build:** buka `Logs`; pastikan repository punya `render.yaml`, `Dockerfile`, `requirements.txt`, `app/`, dan `web/` di direktori root.
- **`/healthz` gagal:** deployment belum siap atau build gagal; periksa Events/Logs.
- **Login ditolak:** cek `APP_USERNAME` dan `APP_PASSWORD` pada Environment di Render, lalu restart/deploy.
- **Upload gagal / 502:** periksa email/API key, status API access, sandbox flag, dan error di log server.
- **Tidak ada PDF setelah upload:** pastikan service mendapat HTTPS publik, `WEBHOOK_SECRET` masih terset, dan lihat log untuk callback. Copyleaks mengirim hasil lewat webhook, bukan sebagai respons langsung dari submit.
- **Setelah idle terasa lambat:** wajar di Render Free karena service tidur. Jangan spam request; tunggu service menyala.

## Deploy ke VPS sendiri nanti

Jika suatu saat sudah punya VPS dan domain, lihat bagian **Server Docker sendiri dengan domain** di `README.md`. `docker-compose.yml` menjalankan aplikasi bersama Caddy untuk HTTPS. VPS/domain belum disiapkan dalam panduan Render ini.
