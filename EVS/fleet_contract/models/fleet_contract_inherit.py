from odoo import models, fields, api, _
from datetime import timedelta
from odoo.exceptions import ValidationError, UserError



class FleetVehicleLogContract(models.Model):
    _inherit = 'fleet.vehicle.log.contract'

    # Add new fields for purchase order, purchase request, and COC
    purchase_order = fields.Binary(string="Purchase Order", tracking=True)
    purchase_request = fields.Binary(string="Purchase Request", tracking=True)
    coc_file = fields.Binary(string="COC", tracking=True)
    po_number = fields.Char(string="Purchase Order Number", tracking=True)
    pr_number = fields.Char(string="Purchase Request Number", tracking=True)
    coc_number = fields.Char(string="COC Number", tracking=True)
    file_name1 = fields.Char(string="File Name")
    file_name2 = fields.Char(string="File Name")
    file_name3 = fields.Char(string="File Name")
    duration = fields.Float(string="Duration", compute="_compute_duration", store=True, tracking=True, readonly=False)
    invoice_id = fields.Many2one(comodel_name='account.move', string="Related Invoice", readonly=True, tracking=True)
    invoice_check = fields.Boolean(defualte=False, tracking=True)


    @api.depends('start_date', 'expiration_date', 'cost_frequency')
    def _compute_duration(self):
        for record in self:
            if record.start_date and record.expiration_date:
                # Calculate the difference between start_date and expiration_date
                start_date = fields.Date.from_string(record.start_date)
                end_date = fields.Date.from_string(record.expiration_date)

                if record.cost_frequency == 'daily':  # If the cost frequency is daily
                    delta = (end_date - start_date).days
                elif record.cost_frequency == 'weekly':  # Weekly
                    delta = (end_date - start_date).days / 7
                elif record.cost_frequency == 'monthly':  # Monthly
                    delta = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
                elif record.cost_frequency == 'yearly':  # Yearly
                    delta = (end_date.year - start_date.year)
                else:
                    delta = 0  # Default to 0 if no valid frequency is selected

                record.duration = delta
            else:
                record.duration = 0

    def create_invoice(self):
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        if not journal:
            raise UserError("No sales journal found.")
        for rec in self:
                invoice_vals = {
                    'partner_id': rec.insurer_id.id,
                    'move_type': 'out_invoice',
                    'journal_id': journal.id,
                    'invoice_date_due': rec.expiration_date,
                    'invoice_date': rec.date,
                    'invoice_line_ids': [(0, 0, {
                        'name': rec.name + " " + rec.ins_ref,
                        'quantity': 1,
                        'price_unit': (rec.duration * rec.cost_generated) + rec.amount,
                    })],
                }
                invoice = self.env['account.move'].create(invoice_vals)
                rec.invoice_id = invoice.id
                # self.env.cr.rollbac()
                rec.invoice_check = True
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Customer Invoice',
                    'view_mode': 'form',
                    'res_model': 'account.move',
                    'res_id': invoice.id,
                    'target': 'current',
                }
        # except Exception as e:
        #         raise UserError(f"Error creating invoice: {e}")

