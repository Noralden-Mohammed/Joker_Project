# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import timedelta


class FleetVehicleServices(models.Model):
    _inherit = 'fleet.vehicle.log.services'

    invoice_id = fields.Many2one(comodel_name='account.move', string="Related Invoice", readonly=True, tracking=True)
    invoice_check = fields.Boolean(defualte=False, tracking=True)

    def create_invoice(self):
        journal = self.env['account.journal'].search([('type', '=', 'purchase')], limit=1)
        if not journal:
            raise UserError("No Purchase Journal found.")
        for rec in self:
                invoice_vals = {
                    'partner_id': rec.vendor_id.id,
                    'move_type': 'in_invoice',
                    'journal_id': journal.id,
                    'invoice_date_due': rec.date,
                    'invoice_date': rec.date,
                    'invoice_line_ids': [(0, 0, {
                        'name': rec.description + " " + rec.service_type_id.name,
                        'quantity': 1,
                        'price_unit':rec.amount,
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




