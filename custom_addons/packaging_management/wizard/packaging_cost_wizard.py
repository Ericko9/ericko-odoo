from odoo import models, fields, api


class PackagingCostWizard(models.TransientModel):
    _name = 'packaging.cost.wizard'
    _description = 'Packaging Cost and Price Calculator'

    order_line_id = fields.Many2one(
        'sale.order.line',
        string='Sales Order Line',
        required=True
    )
    packaging_spec_id = fields.Many2one(
        'packaging.specification',
        string='Packaging Specification',
        readonly=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )

    # 1. Parameter Material & Dimensi
    sheet_area_sqm = fields.Float(
        string='Sheet Area (m²)',
        digits=(12, 4),
        readonly=True,
        help='Luas lembaran karton per pcs dari baris pesanan'
    )
    flute_type = fields.Selection(
        related='packaging_spec_id.flute_type',
        string='Flute Type',
        readonly=True
    )
    paper_substance = fields.Char(
        related='packaging_spec_id.paper_substance',
        string='Paper Substance',
        readonly=True
    )
    total_gsm = fields.Float(
        string='Total GSM (g/m²)',
        default=450.0,
        help='Estimasi berat gramatur total kertas per m² (Luar + Gelombang + Dalam)'
    )
    box_weight_kg = fields.Float(
        string='Est. Box Weight (kg)',
        compute='_compute_cost_and_price',
        digits=(12, 4),
        help='Berat per box: Luas Lembaran x Total GSM / 1000'
    )

    # 2. Parameter Biaya Produksi (COGS / HPP)
    paper_price_per_kg = fields.Monetary(
        string='Paper Price / kg',
        default=1.20,
        currency_field='currency_id',
        help='Harga bahan baku kertas per kilogram'
    )
    paper_cost = fields.Monetary(
        string='Paper Cost / pcs',
        compute='_compute_cost_and_price',
        currency_field='currency_id'
    )
    printing_colors = fields.Integer(
        string='Printing Colors',
        default=1
    )
    printing_cost_per_color = fields.Monetary(
        string='Print Cost / color',
        default=0.03,
        currency_field='currency_id',
        help='Biaya proses cetak per warna per pcs box'
    )
    total_printing_cost = fields.Monetary(
        string='Total Print Cost',
        compute='_compute_cost_and_price',
        currency_field='currency_id'
    )
    joint_cost = fields.Monetary(
        string='Finishing Cost (Lem/Jahit)',
        default=0.02,
        currency_field='currency_id',
        help='Biaya lem atau kawat jahit sambungan per box'
    )
    waste_percent = fields.Float(
        string='Production Waste (%)',
        default=5.0,
        help='Persentase susut/afval bahan baku selama proses produksi'
    )

    # 3. Total HPP & Harga Jual Penawaran
    total_cogs = fields.Monetary(
        string='Total HPP / COGS (per pcs)',
        compute='_compute_cost_and_price',
        currency_field='currency_id',
        help='Total HPP: (Biaya Kertas + Cetak + Finishing) x (1 + Waste %)'
    )
    margin_percent = fields.Float(
        string='Target Profit Margin (%)',
        default=25.0,
        help='Persentase margin laba kotor yang diharapkan'
    )
    suggested_price = fields.Monetary(
        string='Suggested Unit Price',
        compute='_compute_cost_and_price',
        currency_field='currency_id',
        help='Harga jual satuan yang direkomendasikan untuk Quotation'
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        line_id = self.env.context.get('default_order_line_id')
        if line_id:
            line = self.env['sale.order.line'].browse(line_id)
            res.update({
                'order_line_id': line.id,
                'packaging_spec_id': line.packaging_spec_id.id if line.packaging_spec_id else False,
                'sheet_area_sqm': line.sheet_area_sqm,
                'printing_colors': line.packaging_spec_id.printing_colors if line.packaging_spec_id else 1,
            })
        return res

    @api.depends('sheet_area_sqm', 'total_gsm', 'paper_price_per_kg',
                 'printing_colors', 'printing_cost_per_color', 'joint_cost',
                 'waste_percent', 'margin_percent')
    def _compute_cost_and_price(self):
        for wizard in self:
            # 1. Hitung Berat Box (kg)
            weight = (wizard.sheet_area_sqm * wizard.total_gsm) / 1000.0
            wizard.box_weight_kg = weight

            # 2. Hitung Komponen Biaya
            paper_cost = weight * wizard.paper_price_per_kg
            print_cost = wizard.printing_colors * wizard.printing_cost_per_color
            waste_factor = 1.0 + (wizard.waste_percent / 100.0)

            # Total HPP per pcs
            base_cogs = paper_cost + print_cost + wizard.joint_cost
            total_cogs = base_cogs * waste_factor

            wizard.paper_cost = paper_cost
            wizard.total_printing_cost = print_cost
            wizard.total_cogs = total_cogs

            # 3. Hitung Harga Jual berdasarkan Margin
            margin = wizard.margin_percent
            if margin >= 100.0:
                suggested_price = total_cogs * (1.0 + (margin / 100.0))
            elif margin > 0.0:
                # Rumus profit margin komersial: HPP / (1 - Margin%)
                suggested_price = total_cogs / (1.0 - (margin / 100.0))
            else:
                suggested_price = total_cogs

            wizard.suggested_price = suggested_price

    def action_apply_price(self):
        """Terapkan harga satuan hasil kalkulasi ke Sales Order Line"""
        self.ensure_one()
        if self.order_line_id:
            self.order_line_id.price_unit = self.suggested_price
        return {'type': 'ir.actions.act_window_close'}
