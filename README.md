# Industrial Packaging Management (Odoo 19 Custom Addons)

Modul kustom Odoo 19 untuk manajemen proses bisnis industri manufaktur kemasan karton box corrugated (*Corrugated Carton Box & Printing Industry*).

Proyek ini mengintegrasikan seluruh rantai proses dari penjualan, kalkulasi HPP otomatis, otomasi Surat Perintah Kerja & Bill of Materials ke lantai pabrik, kontrol batas toleransi pengiriman gudang, hingga persetujuan desain kemasan digital oleh pelanggan melalui Customer Web Portal.

---

## 🚀 Fitur Utama

### 1. Master Spesifikasi Kemasan (`packaging.specification`)
- Parameter teknis lengkap: Dimensi Box ($P \times L \times T\text{ mm}$), Tipe Box (RSC, Die-Cut, Tray), Jenis Flute (B, C, E, BC Flute), Substansi Kertas (Liner luar/medium/dalam), dan Jumlah Warna Cetak Flexo.
- **Kalkulasi Dimensi Lembaran Otomatis (`@api.depends`)**:
  - Panjang Lembaran: $(2 \times (P + L)) + 40\text{ mm}$ (kuping sambungan)
  - Lebar Lembaran: $L + T + 10\text{ mm}$ (toleransi lipatan flap)
  - Luas Lembaran ($m^2$): $(\text{Panjang} \times \text{Lebar}) / 1.000.000$
- **Workflow Status Spesifikasi**: `Draft` $\rightarrow$ `Sample / Mockup` $\rightarrow$ `Approved` $\rightarrow$ `Obsolete`.
- **Role-Based Access Control (ACL)**: Pemisahan hak akses antara Salesman (*Read/Create/Write*) dan Sales Manager (*Full Access*).
- **QWeb PDF Report**: Cetak spesifikasi kemasan teknis langsung pada dokumen Quotation PDF pelanggan.

### 2. Wizard Kalkulator HPP & Penetapan Harga Jual Otomatis (`packaging.cost.wizard`)
- Membantu sales menghitung *Cost of Goods Sold (COGS)* secara presisi:
  - Estimasi berat box karton (gram/pcs).
  - Biaya bahan baku kertas per kg.
  - Biaya cetak flexo per warna per $m^2$.
  - Biaya lem corrugator & finishing.
  - Toleransi susut proses (*waste percentage*, misal 5%).
  - Margin laba kotor (*target margin percentage*, misal 20%).
- Tombol **"Apply Suggested Price to Quotation"** otomatis memperbarui harga satuan pada baris penawaran Sales Order.

### 3. Smart Stat Button & Riwayat Penjualan
- Smart Button `oe_stat_button` pada formulir spesifikasi kemasan:
  - **Orders**: Menampilkan total transaksi Sales Order yang pernah memesan spesifikasi ini.
  - **Qty Sold**: Total akumulasi kuantiti kardus yang sudah terjual (pcs).
- Mengarahkan langsung ke daftar transaksi Sales Order terkait (*Dynamic Action Window*).

### 4. Integrasi Manufaktur (Auto-Generate BoM & SPK / MO)
- **Method Overriding**: Meng-override `action_confirm()` pada `sale.order`.
- Saat Sales Order dikonfirmasi (*Confirm Order*), sistem otomatis:
  1. Membuat master **Bill of Materials (BoM)** terurai berisikan 4 bahan baku utama:
     - Roll Kertas Kraft Liner (`RAW-KRAFT`) dalam kg
     - Roll Kertas Fluting Medium (`RAW-FLUTE`) dalam kg
     - Lem Corrugator & Sambungan (`RAW-GLUE`) dalam kg
     - Tinta Cetak Flexo (`RAW-INK`) dalam kg
  2. Menerbitkan **Manufacturing Order (Surat Perintah Kerja / SPK)** ke pabrik berstatus *Confirmed*.
  3. Menampilkan smart button **Manufacturing** pada formulir Sales Order.

### 5. Toleransi Pengiriman Gudang (Over / Under Delivery Tolerance $\pm 10\%$)
- Mengakomodasi karakteristik proses continuous production industri kemasan karton dan plastik.
- Menghitung batas toleransi pengiriman otomatis pada Surat Jalan Gudang (`stock.move` & `stock.picking`):
  - $\text{Min Qty} = \text{Demand} \times (1 - \text{Tolerance}\% / 100)$
  - $\text{Max Qty} = \text{Demand} \times (1 + \text{Tolerance}\% / 100)$
- **Validasi Over-Delivery**: Memblokir pengiriman jika kuantiti melebihi batas atas toleransi (misal 1.250 pcs pada pesanan 1.000 pcs dengan toleransi $\pm 10\%$).
- **Validasi Sukses**: Pengiriman dalam batas toleransi (misal 1.040 pcs) sah dan diproses berstatus *Done*.

### 6. Upload Desain Mockup & Portal Approval Pelanggan (Digital Signature)
- Tim R&D mengunggah gambar mockup 3D (`artwork_image`) dan file pisau pond (`artwork_file`).
- Sistem menyediakan tautan portal khusus berkeamanan token (`/my/packaging/<id>?token=<token>`).
- Pelanggan membuka browser, memeriksa detail spesifikasi teknis, melihat render mockup, dan membubuhkan **Tanda Tangan Digital (Digital Signature)** secara langsung via HTML5 Canvas.
- Setelah disetujui, status spesifikasi di backend otomatis berubah menjadi **Approved** dan rekaman tanda tangan tersimpan rapi.

---

## 📁 Struktur Modul

```
custom_addons/packaging_management/
├── __init__.py
├── __manifest__.py
├── controllers/
│   ├── __init__.py
│   └── portal.py
├── models/
│   ├── __init__.py
│   ├── packaging_spec.py
│   ├── sale_order_line.py
│   ├── sale_order.py
│   ├── mrp_production.py
│   ├── stock_move.py
│   └── stock_picking.py
├── wizard/
│   ├── __init__.py
│   ├── packaging_cost_wizard.py
│   └── packaging_cost_wizard_views.xml
├── views/
│   ├── packaging_spec_views.xml
│   ├── sale_order_views.xml
│   ├── mrp_production_views.xml
│   ├── stock_picking_views.xml
│   └── portal_templates.xml
├── report/
│   └── sale_order_report_templates.xml
└── security/
    └── ir.model.access.csv
```

---

## ⚙️ Persyaratan Sistem & Instalasi

- **Odoo**: Versi 19.0 Community / Enterprise
- **Python**: 3.10+ (Diuji pada Python 3.14)
- **Database**: PostgreSQL 14+
- **Dependensi Modul Odoo**:
  - `base`
  - `sale_management`
  - `mrp`
  - `sale_mrp`
  - `stock`
  - `portal`

### Cara Menjalankan Modul:
1. Salin folder `custom_addons/packaging_management` ke direktori addons Odoo Anda.
2. Tambahkan `custom_addons` ke dalam parameter `addons_path` pada file `odoo.conf`:
   ```ini
   addons_path = /path/to/odoo/addons,custom_addons
   ```
3. Update daftar modul Odoo dan instal modul:
   ```bash
   python3 odoo/odoo-bin -c odoo.conf -u packaging_management -d <database_name>
   ```
4. Masuk ke Odoo web dan buka menu **Packaging** pada navbar utama.

---

## 👨‍💻 Pengembang
- **Author**: Ericko
- **Repository**: [https://github.com/Ericko9/ericko-odoo](https://github.com/Ericko9/ericko-odoo)
- **License**: LGPL-3
