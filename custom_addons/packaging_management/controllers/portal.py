import base64
from odoo import http, fields, _
from odoo.http import request
from werkzeug.exceptions import NotFound, Forbidden


from odoo.addons.portal.controllers.portal import CustomerPortal


class PackagingPortalController(CustomerPortal):

    def _get_spec_or_fail(self, spec_id, token=None):
        spec = request.env['packaging.specification'].sudo().browse(spec_id)
        if not spec.exists():
            raise NotFound()

        # Izinkan jika user adalah internal user Odoo ATAU memiliki token akses yang sah
        is_internal_user = request.env.user and request.env.user.has_group('base.group_user')
        if not is_internal_user:
            if not token or token != spec.access_token:
                raise Forbidden(_("Invalid or missing access token."))

        return spec

    @http.route(['/my/packaging/<int:spec_id>'], type='http', auth='public', website=False, sitemap=False)
    def portal_spec_detail(self, spec_id, token=None, approved=False, **kw):
        """Halaman portal persetujuan desain spesifikasi kemasan karton box"""
        spec = self._get_spec_or_fail(spec_id, token=token)
        values = {
            'spec': spec,
            'token': token or spec.access_token,
            'approved_just_now': bool(approved),
            'frontend_languages': {},
        }
        return request.render('packaging_management.portal_spec_approval_page', values)

    @http.route(['/my/packaging/<int:spec_id>/approve'], type='http', auth='public', methods=['POST'], website=False, csrf=False)
    def portal_spec_approve(self, spec_id, token=None, **post):
        """Menerima submit tanda tangan digital pelanggan dan mengonfirmasi spesifikasi"""
        spec = self._get_spec_or_fail(spec_id, token=token)

        signee_name = post.get('signee_name', '').strip() or spec.partner_id.name
        signature_data = post.get('signature', '').strip()

        if signature_data:
            # Hilangkan prefix data:image/png;base64, jika ada
            if 'base64,' in signature_data:
                signature_data = signature_data.split('base64,')[1]

            spec.sudo().write({
                'approval_signature': signature_data,
                'signed_by': signee_name,
                'signed_on': fields.Datetime.now(),
                'state': 'approved',
            })

        return request.redirect(f'/my/packaging/{spec_id}?token={token or spec.access_token}&approved=1')
