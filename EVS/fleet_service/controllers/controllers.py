# -*- coding: utf-8 -*-
# from odoo import http


# class FleetService(http.Controller):
#     @http.route('/fleet_service/fleet_service', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/fleet_service/fleet_service/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('fleet_service.listing', {
#             'root': '/fleet_service/fleet_service',
#             'objects': http.request.env['fleet_service.fleet_service'].search([]),
#         })

#     @http.route('/fleet_service/fleet_service/objects/<model("fleet_service.fleet_service"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('fleet_service.object', {
#             'object': obj
#         })

