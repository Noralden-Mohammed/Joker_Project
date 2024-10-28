# -*- coding: utf-8 -*-

from odoo import models, fields, api


# class fleet_dashboard(models.Model):
#     _name = 'fleet_dashboard.fleet_dashboard'
#
class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'
    _description = 'Fleet Vehicle Information'

    name = fields.Char('Vehicle Name', required=True)
    vehicle_type = fields.Selection([('car', 'Car'), ('truck', 'Truck')], string='Type', required=True)
    model = fields.Char('Model')
    license_plate = fields.Char('License Plate')
    driver_id = fields.Many2one('fleet.driver', string='Assigned Driver')
    status = fields.Selection([('active', 'Active'), ('maintenance', 'Maintenance'), ('inactive', 'Inactive')], string='Status', default='active')
    plan_to_change_car = fields.Boolean(
        related='fleet.vehicle.plan_to_change_car',
        store=True  # or False, depending on whether you want it stored
    )

class FleetDriver(models.Model):
    _name = 'fleet.driver'
    _description = 'Driver Information'

    name = fields.Char('Driver Name', required=True)
    license_number = fields.Char('License Number', required=True)
    vehicle_ids = fields.One2many('fleet.vehicle', 'driver_id', string='Assigned Vehicles')

class FleetFuelUsage(models.Model):
    _name = 'fleet.fuel.usage'
    _description = 'Fuel Usage Information'

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', required=True)
    fuel_amount = fields.Float('Fuel Amount (liters)', required=True)
    fuel_cost = fields.Float('Fuel Cost')
    date = fields.Date('Date', default=fields.Date.today)

class FleetCost(models.Model):
    _name = 'fleet.cost'
    _description = 'Cost Information'

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', required=True)
    maintenance_cost = fields.Float('Maintenance Cost')
    fuel_cost = fields.Float('Fuel Cost')
    other_costs = fields.Float('Other Costs')
    total_cost = fields.Float('Total Cost', compute='_compute_total_cost')

    @api.depends('maintenance_cost', 'fuel_cost', 'other_costs')
    def _compute_total_cost(self):
        for record in self:
            record.total_cost = record.maintenance_cost + record.fuel_cost + record.other_costs

class FleetService(models.Model):
    _name = 'fleet.service'
    _description = 'Service Information'

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', required=True)
    service_type = fields.Selection([('maintenance', 'Maintenance'), ('repair', 'Repair')], string='Service Type', required=True)
    service_date = fields.Date('Service Date', default=fields.Date.today)
    cost = fields.Float('Service Cost')


