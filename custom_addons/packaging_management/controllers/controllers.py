# from odoo import http


# class PackagingManagement(http.Controller):
#     @http.route('/packaging_management/packaging_management', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/packaging_management/packaging_management/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('packaging_management.listing', {
#             'root': '/packaging_management/packaging_management',
#             'objects': http.request.env['packaging_management.packaging_management'].search([]),
#         })

#     @http.route('/packaging_management/packaging_management/objects/<model("packaging_management.packaging_management"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('packaging_management.object', {
#             'object': obj
#         })

