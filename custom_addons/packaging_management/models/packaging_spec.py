import uuid
from odoo import models, fields, api


class PackagingSpecification(models.Model):
    _name = 'packaging.specification'
    _description = 'Packaging Specification'
    _order = 'name asc'

    name = fields.Char(
        string='Specification Code',
        required=True,
        help='Contoh: BOX-AQU-001'
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        help='Pelanggan pemilik spesifikasi kemasan ini'
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sample', 'Sample / Mockup'),
        ('approved', 'Approved'),
        ('obsolete', 'Obsolete'),
    ], string='Status', default='draft', required=True)

    box_type = fields.Selection([
        ('rsc', 'Regular Slotted Carton (RSC)'),
        ('diecut', 'Die-Cut Box'),
        ('top_bottom', 'Top & Bottom Box'),
        ('tray', 'Corrugated Tray'),
    ], string='Box Type', default='rsc', required=True)

    flute_type = fields.Selection([
        ('b', 'B-Flute (3 mm) - Single Wall'),
        ('c', 'C-Flute (4 mm) - Single Wall'),
        ('e', 'E-Flute (1.5 mm) - Micro Flute'),
        ('bc', 'BC-Flute (7 mm) - Double Wall'),
    ], string='Flute Type', default='b', required=True)

    paper_substance = fields.Char(
        string='Paper Substance',
        default='K150/M125/K150',
        help='Susunan kertas (Luar/Flute/Dalam), contoh: K150/M125/K150'
    )
    joint_type = fields.Selection([
        ('glue', 'Gluing (Lem)'),
        ('stitch', 'Stitching (Jahit Kawat)'),
    ], string='Joint Type', default='glue')

    printing_colors = fields.Integer(
        string='Printing Colors',
        default=0,
        help='Jumlah warna cetak flexo (0 = polos tanpa cetakan)'
    )
    delivery_tolerance_pct = fields.Float(
        string='Delivery Tolerance (±%)',
        default=10.0,
        help='Toleransi pengiriman lebih/kurang hasil produksi pabrik ke customer (standar industri: ±10%)'
    )
    length = fields.Float(string='Length (mm)', default=300.0)
    width = fields.Float(string='Width (mm)', default=200.0)
    height = fields.Float(string='Height (mm)', default=150.0)

    # Dimensi lembaran bahan baku terhitung otomatis
    sheet_length = fields.Float(
        string='Sheet Length (mm)',
        compute='_compute_sheet_dimensions',
        store=True,
        help='Panjang lembaran: (2 * (P + L)) + 40mm kuping sambungan'
    )
    sheet_width = fields.Float(
        string='Sheet Width (mm)',
        compute='_compute_sheet_dimensions',
        store=True,
        help='Lebar lembaran: L + T + 10mm toleransi creasing flap'
    )
    sheet_area_sqm = fields.Float(
        string='Sheet Area (m²)',
        compute='_compute_sheet_dimensions',
        store=True,
        digits=(12, 4),
        help='Luas lembaran karton per pcs dalam satuan meter persegi'
    )

    # Statistik Penjualan (Smart Button)
    order_count = fields.Integer(
        string='Order Count',
        compute='_compute_order_statistics',
        help='Jumlah transaksi Sales Order yang memesan spesifikasi kemasan ini'
    )
    total_qty_sold = fields.Float(
        string='Total Qty Sold (pcs)',
        compute='_compute_order_statistics',
        digits=(12, 0),
        help='Total kuantiti kardus yang sudah terjual untuk spesifikasi ini'
    )

    notes = fields.Text(string='Technical Notes')

    # Desain Mockup & File Teknis (Fitur 5)
    artwork_image = fields.Image(
        string='Artwork / Mockup Image',
        max_width=1920,
        max_height=1920,
        help='Pratinjau gambar mockup 3D atau layout cetak karton box'
    )
    artwork_file = fields.Binary(
        string='Technical Drawing (Pisau Pond / CAD / PDF)',
        help='File teknis pisau pond atau gambar kerja teknis'
    )
    artwork_filename = fields.Char(string='Artwork Filename')

    # Portal Approval & Digital Signature
    access_token = fields.Char(
        string='Portal Access Token',
        copy=False,
        help='Security token untuk akses publik portal approval pelanggan'
    )
    portal_url = fields.Char(
        string='Portal Approval URL',
        compute='_compute_portal_url',
        help='Link portal approval yang dapat dikirimkan ke pelanggan'
    )
    approval_signature = fields.Binary(
        string='Customer Signature',
        copy=False,
        help='Tanda tangan digital persetujuan pelanggan'
    )
    signed_by = fields.Char(
        string='Signed By',
        copy=False,
        help='Nama perwakilan pelanggan yang menyetujui desain'
    )
    signed_on = fields.Datetime(
        string='Signed On',
        copy=False,
        help='Waktu penandatanganan digital'
    )

    def _get_access_token(self):
        self.ensure_one()
        if not self.access_token:
            token = uuid.uuid4().hex
            self.write({'access_token': token})
        return self.access_token

    def _compute_portal_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', '')
        for rec in self:
            if rec.id:
                token = rec.access_token or uuid.uuid4().hex
                if not rec.access_token:
                    rec.access_token = token
                rec.portal_url = f"{base_url}/my/packaging/{rec.id}?token={token}"
            else:
                rec.portal_url = ""

    def action_open_portal(self):
        """Buka halaman approval portal pelanggan di tab baru"""
        self.ensure_one()
        token = self._get_access_token()
        return {
            'type': 'ir.actions.act_url',
            'url': f"/my/packaging/{self.id}?token={token}",
            'target': 'new',
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('access_token'):
                vals['access_token'] = uuid.uuid4().hex
        return super().create(vals_list)

    @api.depends('length', 'width', 'height')
    def _compute_sheet_dimensions(self):
        for record in self:
            if record.length > 0 and record.width > 0 and record.height > 0:
                record.sheet_length = (2 * (record.length + record.width)) + 40.0
                record.sheet_width = record.width + record.height + 10.0
                record.sheet_area_sqm = (record.sheet_length * record.sheet_width) / 1_000_000.0
            else:
                record.sheet_length = 0.0
                record.sheet_width = 0.0
                record.sheet_area_sqm = 0.0

    def _compute_order_statistics(self):
        """Hitung jumlah transaksi dan total kuantiti pcs yang sudah dipesan"""
        for record in self:
            lines = self.env['sale.order.line'].search([
                ('packaging_spec_id', '=', record.id)
            ])
            record.order_count = len(lines.mapped('order_id'))
            record.total_qty_sold = sum(lines.mapped('product_uom_qty'))

    # Workflow Action Buttons
    def action_request_sample(self):
        self.write({'state': 'sample'})

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_set_obsolete(self):
        self.write({'state': 'obsolete'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})

    # Smart Button Action
    def action_view_sales_orders(self):
        """Membuka daftar Sales Order yang menggunakan spesifikasi kemasan ini"""
        self.ensure_one()
        lines = self.env['sale.order.line'].search([
            ('packaging_spec_id', '=', self.id)
        ])
        order_ids = lines.mapped('order_id').ids
        action = {
            'name': f'Sales Orders - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [('id', 'in', order_ids)],
            'context': {'default_partner_id': self.partner_id.id},
        }
        if len(order_ids) == 1:
            action['views'] = [(False, 'form')]
            action['res_id'] = order_ids[0]
        return action
