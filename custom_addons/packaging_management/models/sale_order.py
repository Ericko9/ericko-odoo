from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.depends('stock_reference_ids.production_ids')
    def _compute_mrp_production_ids(self):
        super()._compute_mrp_production_ids()
        for sale in self:
            direct_mos = self.env['mrp.production'].search([
                ('origin', '=', sale.name),
                ('state', '!=', 'cancel')
            ])
            sale.mrp_production_ids = sale.mrp_production_ids | direct_mos
            sale.mrp_production_count = len(sale.mrp_production_ids)

    def action_confirm(self):
        """Method Overriding: Saat SO dikonfirmasi, otomatis generate BoM terurai dan SPK Pabrik"""
        res = super().action_confirm()
        self._generate_packaging_manufacturing_orders()
        return res

    def _get_or_create_raw_material(self, default_code, name):
        """Helper mencari atau membuat master produk bahan baku karton box"""
        Product = self.env['product.product']
        product = Product.search([('default_code', '=', default_code)], limit=1)
        if not product:
            uom_kg = self.env.ref('uom.product_uom_kgm', raise_if_not_found=False)
            if not uom_kg:
                uom_kg = self.env['uom.uom'].search([('name', '=', 'kg')], limit=1)
            vals = {
                'name': name,
                'default_code': default_code,
                'type': 'consu',
            }
            if uom_kg:
                vals['uom_id'] = uom_kg.id
                if 'uom_po_id' in Product._fields:
                    vals['uom_po_id'] = uom_kg.id
            product = Product.create(vals)
        return product

    def _generate_packaging_manufacturing_orders(self):
        """Membuatkan BoM terurai (kertas, flute, lem, tinta) dan SPK ke pabrik secara otomatis"""
        MrpBom = self.env['mrp.bom']
        MrpProduction = self.env['mrp.production']

        # Dapatkan master 4 bahan baku utama industri karton
        p_kraft = self._get_or_create_raw_material('RAW-KRAFT', 'Roll Kertas Kraft Liner')
        p_flute = self._get_or_create_raw_material('RAW-FLUTE', 'Roll Kertas Fluting Medium')
        p_glue = self._get_or_create_raw_material('RAW-GLUE', 'Lem Corrugator & Sambungan')
        p_ink = self._get_or_create_raw_material('RAW-INK', 'Tinta Cetak Flexo')

        for order in self:
            for line in order.order_line:
                spec = line.packaging_spec_id
                if not spec or line.product_uom_qty <= 0:
                    continue

                # Cek jika SPK untuk line ini sudah pernah dibuat sebelumnya
                existing_mo = MrpProduction.search([
                    ('origin', '=', order.name),
                    ('packaging_spec_id', '=', spec.id),
                    ('product_id', '=', line.product_id.id)
                ], limit=1)
                if existing_mo:
                    continue

                # 1. Hitung kebutuhan bahan baku per 1 pcs box berdasarkan luas lembaran
                sheet_area = line.sheet_area_sqm or spec.sheet_area_sqm
                if sheet_area <= 0:
                    continue

                # Formula kebutuhan per 1 pcs (kg) dengan toleransi susut proses 5%:
                # - Kraft (Liner Luar + Dalam = ~300 gsm)
                # - Fluting (Medium 125 gsm x 1.35 take-up = ~168.75 gsm)
                # - Lem Corrugator = ~0.02 kg / m2
                # - Tinta Flexo = ~0.005 kg / m2 per warna
                waste_mult = 1.05
                kraft_kg_per_unit = round((sheet_area * 300.0 / 1000.0) * waste_mult, 4)
                flute_kg_per_unit = round((sheet_area * 168.75 / 1000.0) * waste_mult, 4)
                glue_kg_per_unit = round(sheet_area * 0.02 * waste_mult, 4)
                ink_kg_per_unit = round(sheet_area * 0.005 * max(spec.printing_colors, 1) * waste_mult, 4)

                # 2. Cari atau buat Bill of Materials (BoM) spesifikasi kemasan ini
                bom = MrpBom.search([
                    ('product_id', '=', line.product_id.id),
                    ('code', '=', spec.name)
                ], limit=1)

                bom_lines_vals = [
                    (0, 0, {'product_id': p_kraft.id, 'product_qty': max(kraft_kg_per_unit, 0.0001)}),
                    (0, 0, {'product_id': p_flute.id, 'product_qty': max(flute_kg_per_unit, 0.0001)}),
                    (0, 0, {'product_id': p_glue.id, 'product_qty': max(glue_kg_per_unit, 0.0001)}),
                    (0, 0, {'product_id': p_ink.id, 'product_qty': max(ink_kg_per_unit, 0.0001)}),
                ]

                if not bom:
                    bom = MrpBom.create({
                        'product_tmpl_id': line.product_id.product_tmpl_id.id,
                        'product_id': line.product_id.id,
                        'product_qty': 1.0,
                        'code': spec.name,
                        'type': 'normal',
                        'bom_line_ids': bom_lines_vals,
                    })

                # 3. Buat Surat Perintah Kerja (Manufacturing Order)
                mo_vals = {
                    'product_id': line.product_id.id,
                    'product_qty': line.product_uom_qty,
                    'product_uom_id': line.product_uom_id.id,
                    'bom_id': bom.id,
                    'origin': order.name,
                    'packaging_spec_id': spec.id,
                }
                if 'sale_line_id' in MrpProduction._fields:
                    mo_vals['sale_line_id'] = line.id

                mo = MrpProduction.create(mo_vals)
                if hasattr(mo, 'action_confirm'):
                    mo.action_confirm()
