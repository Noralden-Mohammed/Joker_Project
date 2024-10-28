# -*- coding: utf-8 -*-
# from odoo import http


# class FleetDashboard(http.Controller):
#     @http.route('/fleet_dashboard/fleet_dashboard', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/fleet_dashboard/fleet_dashboard/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('fleet_dashboard.listing', {
#             'root': '/fleet_dashboard/fleet_dashboard',
#             'objects': http.request.env['fleet_dashboard.fleet_dashboard'].search([]),
#         })

#     @http.route('/fleet_dashboard/fleet_dashboard/objects/<model("fleet_dashboard.fleet_dashboard"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('fleet_dashboard.object', {
#             'object': obj
#         })

