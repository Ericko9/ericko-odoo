from odoo import models, fields


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    packaging_spec_id = fields.Many2one(
        'packaging.specification',
        string='Packaging Spec',
        readonly=True,
        help='Spesifikasi kemasan karton box pesanan dari Sales Order'
    )
