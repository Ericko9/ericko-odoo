{
    'name': 'Industrial Packaging Management',
    'version': '19.0.1.0.0',
    'summary': 'Manajemen spesifikasi dan kalkulasi kemasan karton box untuk pabrik/industri',
    'description': """
Industrial Packaging Management
===============================
Modul kustom untuk perusahaan manufaktur/distributor kemasan industri (Corrugated Carton Box).
Fitur:
- Master Spesifikasi Kemasan Pelanggan (panjang, lebar, tinggi, flute, substansi kertas, warna cetak)
- Workflow Status Spesifikasi: Draft -> Sample/Mockup -> Approved -> Obsolete
- Integrasi ke Sales Order Line untuk pemilihan spek kemasan custom
- Kalkulasi otomatis dimensi dan luas lembaran karton mentah (Corrugated Sheet Area)
- Validasi input ukuran box
- Role-based security (Salesman vs Sales Manager)
- Cetak spesifikasi kemasan pada dokumen Quotation PDF
- Wizard Kalkulator HPP (COGS) & Penetapan Harga Jual Otomatis
- Smart Stat Button & Riwayat Penjualan pada Master Spek
- Integrasi Manufaktur: Auto-Generate BoM & SPK (Manufacturing Order) saat Sales Order dikonfirmasi
    """,
    'author': 'Ericko',
    'category': 'Sales/Manufacturing',
    'depends': ['base', 'sale_management', 'mrp', 'sale_mrp', 'stock', 'portal'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/packaging_cost_wizard_views.xml',
        'views/packaging_spec_views.xml',
        'views/sale_order_views.xml',
        'views/mrp_production_views.xml',
        'views/stock_picking_views.xml',
        'views/portal_templates.xml',
        'report/sale_order_report_templates.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
