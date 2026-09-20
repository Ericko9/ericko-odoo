from odoo import models, fields, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    delivery_tolerance_pct = fields.Float(
        string='Tolerance (±%)',
        compute='_compute_delivery_tolerances',
        store=True,
        readonly=False,
        default=10.0,
        help='Persentase toleransi pengiriman lebih/kurang yang disepakati dengan customer'
    )
    min_delivery_qty = fields.Float(
        string='Min Allowed Qty',
        compute='_compute_delivery_tolerances',
        store=True,
        digits='Product Unit of Measure',
        help='Batas kuantiti pengiriman minimum yang masih sah dalam toleransi'
    )
    max_delivery_qty = fields.Float(
        string='Max Allowed Qty',
        compute='_compute_delivery_tolerances',
        store=True,
        digits='Product Unit of Measure',
        help='Batas kuantiti pengiriman maksimum yang diizinkan dalam toleransi'
    )
    tolerance_status = fields.Selection([
        ('within', 'Within Tolerance'),
        ('over', 'Over Tolerance'),
        ('under', 'Under Tolerance'),
    ], string='Tolerance Status', compute='_compute_delivery_tolerances', store=True, default='within')

    @api.depends('sale_line_id.delivery_tolerance_pct', 'product_uom_qty', 'quantity')
    def _compute_delivery_tolerances(self):
        for move in self:
            # Ambil toleransi dari SO line jika ada, jika tidak default 10.0%
            tol = move.sale_line_id.delivery_tolerance_pct if move.sale_line_id else 10.0
            move.delivery_tolerance_pct = tol
            demand = move.product_uom_qty or 0.0

            if tol > 0 and demand > 0:
                min_q = round(demand * (1.0 - (tol / 100.0)), 2)
                max_q = round(demand * (1.0 + (tol / 100.0)), 2)
            else:
                min_q = demand
                max_q = demand

            move.min_delivery_qty = min_q
            move.max_delivery_qty = max_q

            qty = move.quantity
            if demand <= 0 or qty <= 0:
                move.tolerance_status = 'within'
            elif qty > max_q:
                move.tolerance_status = 'over'
            elif qty < min_q:
                move.tolerance_status = 'under'
            else:
                move.tolerance_status = 'within'
