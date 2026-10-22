# Proyek Analisis Data: Kualitas Udara Beijing (PM2.5)

Analisis data kualitas udara (PM2.5) dari 12 stasiun pemantau di Beijing, Maret 2013 – Februari 2017
(*Beijing Multi-Site Air-Quality Data*), beserta dashboard interaktif Streamlit.

**Pertanyaan bisnis**
1. Bagaimana tren bulanan PM2.5 dan pada musim/bulan apa rata-ratanya melampaui 75 µg/m³?
2. Stasiun mana yang rata-rata PM2.5-nya tertinggi/terendah dan berapa persen harinya melampaui 75 µg/m³?
3. Seberapa besar selisih PM2.5 saat angin < 1 m/s vs > 3 m/s, dan arah angin apa yang dominan pada hari PM2.5 > 150 µg/m³?

Analisis lanjutan: *manual grouping/binning* kategori kualitas udara dan *geospatial analysis* (tanpa machine learning).

## Struktur Folder
```
submission
├── dashboard
│   ├── main_data.csv      # data harian per stasiun (hasil cleaning, dipakai dashboard)
│   └── dashboard.py       # aplikasi Streamlit
├── data                   # 12 berkas CSV mentah (PRSA_Data_*.csv)
├── notebook.ipynb         # proses analisis lengkap (sudah dijalankan)
├── README.md
├── requirements.txt
└── url.txt                # tautan dashboard di Streamlit Cloud
```

## Setup Environment
Disarankan memakai Python 3.10+.

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Atau dengan Anaconda:
```bash
conda create --name air-quality python=3.11
conda activate air-quality
pip install -r requirements.txt
```

## Menjalankan Dashboard
Dari folder root `submission`:
```bash
streamlit run dashboard/dashboard.py
```
Dashboard terbuka di `http://localhost:8501`. Gunakan filter di sidebar (rentang tanggal & stasiun).

## Menjalankan Ulang Notebook
Jalankan dari folder root `submission` agar path `data/` terbaca:
```bash
jupyter notebook notebook.ipynb
```
Sel terakhir akan membuat ulang `dashboard/main_data.csv`.

## Deploy ke Streamlit Cloud
Unggah folder ke repositori GitHub, lalu di https://share.streamlit.io pilih repositori tersebut dengan *Main file path* `dashboard/dashboard.py`. Tuliskan tautan hasil deploy di `url.txt`.
