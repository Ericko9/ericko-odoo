from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    packaging_spec_id = fields.Many2one(
        'packaging.specification',
        string='Packaging Spec',
        help='Pilih master spesifikasi kemasan milik pelanggan',
        domain="[('partner_id', '=', parent.partner_id)]"
    )
    length = fields.Float(string='Length (mm)', default=0.0)
    width = fields.Float(string='Width (mm)', default=0.0)
    height = fields.Float(string='Height (mm)', default=0.0)
    delivery_tolerance_pct = fields.Float(
        string='Tolerance (±%)',
        default=10.0,
        help='Toleransi pengiriman lebih/kurang hasil produksi pabrik ke customer (default: ±10%)'
    )

    # Computed fields dimensi lembaran bahan baku
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

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            spec_id = vals.get('packaging_spec_id')
            if spec_id:
                spec = self.env['packaging.specification'].browse(spec_id)
                if spec:
                    if not vals.get('length'):
                        vals['length'] = spec.length
                    if not vals.get('width'):
                        vals['width'] = spec.width
                    if not vals.get('height'):
                        vals['height'] = spec.height
                    if not vals.get('delivery_tolerance_pct') and spec.delivery_tolerance_pct:
                        vals['delivery_tolerance_pct'] = spec.delivery_tolerance_pct
        return super().create(vals_list)

    @api.onchange('packaging_spec_id')
    def _onchange_packaging_spec_id(self):
        """Ketika sales memilih spesifikasi, autofill ukuran box & toleransi kirim"""
        if self.packaging_spec_id:
            self.length = self.packaging_spec_id.length
            self.width = self.packaging_spec_id.width
            self.height = self.packaging_spec_id.height
            if self.packaging_spec_id.delivery_tolerance_pct:
                self.delivery_tolerance_pct = self.packaging_spec_id.delivery_tolerance_pct


    @api.depends('length', 'width', 'height')
    def _compute_sheet_dimensions(self):
        """Menghitung otomatis dimensi & luas lembaran karton saat P, L, T berubah"""
        for line in self:
            if line.length > 0 and line.width > 0 and line.height > 0:
                sheet_l = (2 * (line.length + line.width)) + 40.0
                sheet_w = line.width + line.height + 10.0
                line.sheet_length = sheet_l
                line.sheet_width = sheet_w
                line.sheet_area_sqm = (sheet_l * sheet_w) / 1_000_000.0
            else:
                line.sheet_length = 0.0
                line.sheet_width = 0.0
                line.sheet_area_sqm = 0.0

    @api.constrains('length', 'width', 'height')
    def _check_box_dimensions(self):
        """Mencegah input nilai dimensi <= 0 jika spesifikasi kemasan dipilih"""
        for line in self:
            if line.packaging_spec_id:
                if line.length <= 0 or line.width <= 0 or line.height <= 0:
                    raise ValidationError(
                        "Dimensi kemasan (Panjang, Lebar, Tinggi) harus bernilai lebih dari 0 mm!"
                    )

    def action_open_cost_wizard(self):
        """Buka pop-up wizard kalkulasi HPP dan harga jual kemasan"""
        self.ensure_one()
        return {
            'name': 'Calculate Packaging Price',
            'type': 'ir.actions.act_window',
            'res_model': 'packaging.cost.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_order_line_id': self.id,
                'default_packaging_spec_id': self.packaging_spec_id.id if self.packaging_spec_id else False,
                'default_sheet_area_sqm': self.sheet_area_sqm,
                'default_printing_colors': self.packaging_spec_id.printing_colors if self.packaging_spec_id else 1,
            }
        }
