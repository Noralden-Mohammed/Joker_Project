from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
import random


class ImmedaiteServices(models.Model):
    _name = "immediate.services"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'partner_id'

    services_id = fields.Many2one('services', string='Service Type', tracking=True)
    price = fields.Integer(related='services_id.price', tracking=True)
    code = fields.Char(related='services_id.code', tracking=True)
    partner_id = fields.Many2one('res.partner', string='Customer Name', tracking=True)
    date = fields.Datetime(string="Date", tracking=True)
    phone = fields.Char(related='partner_id.phone', tracking=True)
    state = fields.Selection(selection=[('draft', 'Draft'), ('in_consultation', 'In Consultation'),
                                        ('done', 'Done'), ('cancel', 'Cancel')], default='draft',
                             string="State", tracking=True)
    employee_id = fields.Many2one(comodel_name='res.partner', string="Assigned to", tracking=True)
    invoice_id = fields.Many2one(comodel_name='account.move', string="Related Invoice", readonly=True, tracking=True)
    feeds_id = fields.Many2one(comodel_name='account.move', string="Related Employee Bill", readonly=True,
                               tracking=True)
    invoice_check = fields.Boolean(default=False, readonly=True)
    feeds = fields.Float(compute="_compute_employee_feeds", readonly=True, tracking=True, string="Employee Feeds")
    cancel_date = fields.Date(readonly=True, tracking=True, string="Cancel Date")
    reason = fields.Char(readonly=True, tracking=True, string="Cancel Reason")
    progress = fields.Integer(string='Preogress', compute="_compute_progress")
    discount = fields.Float(string="Discount", tracking=True)
    # services_count = fields.Integer(string="Services Count", compute='_compute_service_count')
    active = fields.Boolean(string="Active", default=True)
    payment_state = fields.Selection(selection=[('not_paid', 'Not Paid'), ('in_payment', 'In Payment'), ('paid', 'Paid'),
                                                ('partial', 'Partially Paid'), ('reversed', 'Reversed')],
                                     default='not_paid', string="Payment state", compute='_compute_payment_state')

    @api.depends('state')
    def _compute_progress(self):
        for rec in self:
            progress = 0
            if rec.state == 'draft':
                progress = random.randrange(0, 50)
            elif rec.state == 'in_consultation':
                progress = random.randrange(50, 90)
            elif rec.state == 'done':
                progress = 100
            elif rec.state == 'cancel':
                progress = 0
            rec.progress = progress

    @api.depends('invoice_id')
    def _compute_payment_state(self):
        for rec in self:
            if rec.invoice_id:
                if rec.invoice_id.payment_state == 'paid':
                    rec.payment_state = 'paid'
                elif rec.invoice_id.payment_state == 'not_paid':
                    rec.payment_state = 'not_paid'
                elif rec.invoice_id.payment_state == 'in_payment':
                    rec.payment_state = 'in_payment'
                elif rec.invoice_id.payment_state == 'partial':
                    rec.payment_state = 'partial'
                elif rec.invoice_id.payment_state == 'reversed':
                    rec.payment_state = 'reversed'
                elif rec.invoice_id.payment_state == 'reversed':
                    rec.payment_state = 'reversed'
            else:
                rec.payment_state = 'not_paid'

    def unlink(self):
        if self.state != 'draft':
            raise ValidationError(_("You can delete Service only in draft state :("))
        else:
            return super(ImmedaiteServices, self).unlink()

    @api.depends('services_id')
    def _compute_employee_feeds(self):
        for rec in self:
            rec.feeds = (rec.price - rec.discount) * (rec.services_id.employee_feeds / 100)

    def confirm(self):
        for rec in self:
            rec.state = 'in_consultation'

    def done(self):
        for rec in self:
            if rec.invoice_check:
                rec.state = 'done'
                return {
                    'effect': {
                        'fadeout': 'slow',
                        'message': 'The Service Done successfully :)',
                        'type': 'rainbow_man',
                    }
                }
            else:
                raise UserError("Sorry you can't Finish Service without invoice ^_^"
                                "\nCreate Invoice First Please !"
                                "\nWith my Love :)")

    def cancel(self):
        action = self.env.ref('center_services.cancel_immediate_action').read()[0]
        return action

    def reset_to_draft(self):
        for rec in self:
            if rec.invoice_id:
                if rec.invoice_id.state == 'draft':
                    rec.state = 'draft'
                    rec.active = True
                else:
                    raise UserError("Sorry you need to reset invoice first ^_^")
            else:
                rec.state = 'draft'
                rec.active = True

    def create_invoice(self):
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        if not journal:
            raise UserError("No sales journal found.")
        for rec in self:
            try:
                invoice_vals = {
                    'partner_id': rec.partner_id.id,
                    'move_type': 'out_invoice',
                    'journal_id': journal.id,
                    'invoice_date_due': fields.date.today(),
                    'invoice_date': rec.date,
                    'invoice_line_ids': [(0, 0, {
                        'name': rec.services_id.name + " + Discount " + str(rec.discount),
                        'quantity': 1,
                        'price_unit': rec.price - rec.discount,
                    })],
                }
                invoice = self.env['account.move'].create(invoice_vals)
                rec.invoice_id = invoice.id
                rec.invoice_check = True
                rec.create_employee_feeds()
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Customer Invoice',
                    'view_mode': 'form',
                    'res_model': 'account.move',
                    'res_id': invoice.id,
                    'target': 'current',
                }
            except Exception as e:
                raise UserError(f"Error creating invoice: {e}")

    def create_employee_feeds(self):
        journal = self.env['account.journal'].search([('type', '=', 'purchase')], limit=1)
        if not journal:
            raise UserError("No Purchase journal found.")
        for rec in self:
            try:
                invoice_vals = {
                    'partner_id': rec.employee_id.id,
                    'move_type': 'in_invoice',
                    'journal_id': journal.id,
                    'invoice_date_due': fields.date.today(),
                    'invoice_date': rec.date,
                    'invoice_line_ids': [((0, 0, {
                        'name': "Employee Feeds of " + rec.services_id.name,
                        'quantity': 1,
                        'price_unit': rec.feeds,
                    }))],
                }
                invoice = self.env['account.move'].create(invoice_vals)
                rec.feeds_id = invoice.id
            except Exception as e:
                raise UserError(f"Error creating Bill: {e}")
