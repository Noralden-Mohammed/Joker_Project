from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta



class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    fuel_service_ids = fields.One2many('fleet.vehicle.fuel', 'vehicle_id', string='Fuel Services')
    total_fuel_cost = fields.Float(compute='_compute_total_fuel_cost', string='Total Fuel Cost')
    fuel_service_count = fields.Integer(string='Fuel Service Count', compute='_compute_fuel_service_count')

    @api.depends('fuel_service_ids.cost')
    def _compute_total_fuel_cost(self):
        for vehicle in self:
            vehicle.total_fuel_cost = sum(vehicle.fuel_service_ids.mapped('cost'))

    def _compute_fuel_service_count(self):
        for vehicle in self:
            vehicle.fuel_service_count = len(vehicle.fuel_service_ids)

    def action_open_fuel_history(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Fuel History',
            'res_model': 'fleet.vehicle.fuel',
            'view_mode': 'tree,form',
            'domain': [('vehicle_id', '=', self.id)],
            'context': dict(self._context),
        }


class FleetVehicleFuel(models.Model):
    _name = 'fleet.vehicle.fuel'
    _description = 'Fuel Service'
    _order = 'date desc'
    _rec_name = 'vehicle_id'

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', required=True)
    date = fields.Date(string='Service Date', required=True, default=fields.Date.context_today)
    cost = fields.Float(string='Fuel Cost', required=True)
    fuel_size = fields.Float(string="Fuel Liters", required=True)
    odometer = fields.Float(string="Odometer", required=True)
    description = fields.Text(string='Description')
    driver_id = fields.Many2one(related='vehicle_id.driver_id', tracking=True)
    state = fields.Selection(selection=[('draft', 'Draft'), ('confirm', 'Confirmed'), ('done', 'Done'), ('cancel', 'Cancelled')
                                        ], default='draft', tracking=True)
    invoice_id = fields.Many2one(comodel_name='account.move', string="Related Invoice", readonly=True, tracking=True)
    invoice_check = fields.Boolean(defualte=False, tracking=True)

    def confirm(self):
        for rec in self:
            rec.state = 'confirm'

    def done(self):
        for rec in self:
            rec.state = 'done'
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': 'The Fuel Done Successfully :)',
                    'type': 'rainbow_man',
                }
            }

    def cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def reset_to_draft(self):
        for rec in self:
            rec.state = 'draft'

    def create_invoice(self):
        journal = self.env['account.journal'].search([('type', '=', 'purchase')], limit=1)
        if not journal:
            raise UserError("No purchase journal found.")
        for rec in self:
            # Find the partner (company) related to the vehicle
                partner = rec.vehicle_id.company_id.partner_id

                invoice_vals = {
                    'partner_id': partner.id,
                    'move_type': 'in_invoice',
                    'journal_id': journal.id,
                    'invoice_date_due': rec.date,
                    'invoice_date': rec.date,
                    'invoice_line_ids': [(0, 0, {
                        'name': "Refuel " + rec.vehicle_id.name,
                        'quantity': 1,
                        'price_unit': rec.cost,
                    })],
                }
                invoice = self.env['account.move'].create(invoice_vals)
                rec.invoice_id = invoice.id
                # self.env.cr.rollbac()
                rec.invoice_check = True
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Vendor Bill',
                    'view_mode': 'form',
                    'res_model': 'account.move',
                    'res_id': invoice.id,
                    'target': 'current',
                }


class FleetVehicleLogServices(models.Model):
    _inherit = 'fleet.vehicle.log.services'

    purchaser_id = fields.Many2one('hr.employee', string="Driver", compute='_compute_purchaser_id', readonly=False, store=True)
