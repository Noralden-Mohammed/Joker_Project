from odoo import models, fields, api
from odoo.exceptions import ValidationError
MODEL_FIELDS_TO_VEHICLE = {
    'transmission': 'transmission', 'model_year': 'model_year', 'electric_assistance': 'electric_assistance',
    'color': 'color', 'seats': 'seats', 'doors': 'doors', 'trailer_hook': 'trailer_hook','load_weight':'load_weight',
    'default_co2': 'co2', 'co2_standard': 'co2_standard', 'default_fuel_type': 'fuel_type',
    'power': 'power', 'horsepower': 'horsepower', 'horsepower_tax': 'horsepower_tax', 'category_id': 'category_id',
}
class FleetInherit(models.Model):
    _inherit = 'fleet.vehicle'


    # responsible_id = fields.Many2one('res.partner', string='Responsible', required=True)
    vehicle_license = fields.Binary(tracking=True, string="Vehicle License")
    start_license_date = fields.Date(tracking=True, string="Start Date")
    end_license_date = fields.Date(tracking=True, string="End Date")
    license_location = fields.Char(string="Location", tracking=True)
    license_number = fields.Char(tracking=True)
    # license_type = fields.Selection(selection=[('')],string="Type", tracking=True)
    file_name = fields.Char(string="File Name")
    driver_id = fields.Many2one('hr.employee', 'Driver', tracking=True, help='Driver address of the vehicle', copy=False)
    future_driver_id = fields.Many2one('hr.employee', 'Future Driver', tracking=True, help='Next Driver Address of the vehicle', copy=False)
    load_weight = fields.Integer(trucking=True, compute='_compute_model_fields', store=True, readonly=False)
    # purchaser_id = fields.Many2one('hr.employee', string="Driver", compute='_compute_purchaser_id', readonly=False, store=True)


    @api.model_create_multi
    def create(self, vals_list):
        ptc_values = [self._clean_vals_internal_user(vals) for vals in vals_list]
        vehicles = super().create(vals_list)
        for vehicle, vals, ptc_value in zip(vehicles, vals_list, ptc_values):
            if ptc_value:
                vehicle.sudo().write(ptc_value)
            if 'driver_id' in vals and vals['driver_id']:
                vehicle.create_driver_history(vals)
            if 'future_driver_id' in vals and vals['future_driver_id']:
                state_waiting_list = self.env.ref('fleet.fleet_vehicle_state_waiting_list', raise_if_not_found=False)
                states = vehicle.mapped('state_id').ids
                if not state_waiting_list or state_waiting_list.id not in states:
                    future_driver = self.env['hr.employee'].browse(vals['future_driver_id'])
                    if self.vehicle_type == 'bike':
                        future_driver.sudo().write({'plan_to_change_bike': True})
                    if self.vehicle_type == 'car':
                        future_driver.sudo().write({'plan_to_change_car': True})
        return vehicles


class HREmployee(models.Model):
    _inherit = 'hr.employee'

    plan_to_change_car = fields.Boolean('Plan To Change Car', default=False, tracking=True)
    plan_to_change_bike = fields.Boolean('Plan To Change Bike', default=False)
    license_card = fields.Binary(string="License Card")
    personal_card = fields.Binary()
    license_number = fields.Char(string="License Number")
    license_expiry_date = fields.Date(string="License Expiry Date")
    license_issued_date = fields.Date(string="License Issued Date")
    license_type = fields.Selection([
        ('a', 'Type A'),
        ('b', 'Type B'),
        ('c', 'Type C')
    ], string="License Type")
    file_name = fields.Char(string="File Name")


class FleetVehicleModel(models.Model):
    _inherit = 'fleet.vehicle.model'

    load_weight = fields.Integer(trucking=True)
