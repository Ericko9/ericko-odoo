from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        """Validasi pengiriman barang:
        Memeriksa apakah kuantiti yang dikirim (quantity) melebihi batas toleransi maksimum
        yang diizinkan oleh kontrak spesifikasi pelanggan.
        """
        for picking in self:
            for move in picking.move_ids:
                if move.delivery_tolerance_pct > 0 and move.product_uom_qty > 0:
                    max_qty = move.max_delivery_qty
                    if move.quantity > max_qty:
                        raise ValidationError(
                            _(
                                "Pengiriman untuk produk '%(product)s' sebesar %(qty)s %(uom)s melebihi batas toleransi pengiriman maksimum %(max_qty)s %(uom)s (+%(tol)s%%)!\n\n"
                                "• Kuantiti Pesanan (Demand): %(demand)s %(uom)s\n"
                                "• Toleransi Pabrik: ±%(tol)s%%\n"
                                "• Batas Maksimum Diizinkan: %(max_qty)s %(uom)s\n"
                                "• Kuantiti yang Dicoba Dikirim: %(qty)s %(uom)s\n\n"
                                "Silakan sesuaikan kuantiti kirim agar tidak melebihi kesepakatan batas atas toleransi pelanggan.",
                                product=move.product_id.display_name,
                                qty=f"{move.quantity:,.2f}".rstrip('0').rstrip('.'),
                                max_qty=f"{max_qty:,.2f}".rstrip('0').rstrip('.'),
                                tol=f"{move.delivery_tolerance_pct:.1f}",
                                demand=f"{move.product_uom_qty:,.2f}".rstrip('0').rstrip('.'),
                                uom=move.product_uom.name,
                            )
                        )
        return super().button_validate()
