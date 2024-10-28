from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date
import random


class DeviceMaintenance(models.Model):
    _name = 'device.maintenance'
    _description = 'Device Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'ref'

    partner_id = fields.Many2one('res.partner', string='Customer Name', tracking=True, required=True)
    phone = fields.Char(related='partner_id.phone', tracking=True, string="Phone")
    email = fields.Char(related='partner_id.email', tracking=True, string="Email")
    state = fields.Selection([('draft', 'Draft'),
                              ('detect problem', 'Detect Problem'),
                              ('solving', 'Solving'), ('return device', 'Return Device'), ('cancel', 'Cancel')],
                             default='draft', tracking=True)
    date = fields.Date(string="Date", tracking=True, required=True)
    devices_id = fields.Many2one('devices', string='Device Type')
    code = fields.Char(related='devices_id.code')
    maintenance_type = fields.Char(related='devices_id.maintenance_type', string='Maintenance Type')
    maintenance_ids = fields.One2many('maintenances.type', 'maintenance_id')
    price = fields.Integer(string='Price')
    device_type = fields.Selection(selection=[('laptop', 'Laptop PC'), ('desktop', 'Desktop PC')], string="Device Type",
                                   tracking=True, default="laptop")
    device_model_id = fields.One2many(comodel_name='device.model', inverse_name='maintenance_id')
    total_price = fields.Float(string="Total Price", tracking=True, readonly=True, compute='_compute_total_price')
    total_feeds = fields.Float(string="Employee Feeds", tracking=True, readonly=True, compute='_compute_total_feeds')
    move_id = fields.Many2one(comodel_name='account.move', tracking=True, readonly=True)
    feeds_id = fields.Many2one(comodel_name='account.move', tracking=True, readonly=True)
    ref = fields.Char(string="References", tracking=True, readonly=True, default="New")
    invoice_check = fields.Boolean(tracking=True, readonly=True, default=False)
    cancel_date = fields.Date(tracking=True, readonly=True, string="Cancel Date")
    reason = fields.Char(tracking=True, readonly=True, string="Reason")
    progress = fields.Integer(string='Preogress', compute="_compute_progress")
    discount = fields.Float(string="Discount", tracking=True)
    active = fields.Boolean(string="Active", default=True)
    employee_id = fields.Many2one(comodel_name='res.partner', string="Assigned to", tracking=True)
    payment_state = fields.Selection(selection=[('not_paid', 'Not Paid'), ('in_payment', 'In Payment'),
                                                ('paid', 'Paid'),
                                                ('partial', 'Partially Paid'), ('reversed', 'Reversed')],
                                     default='not_paid', string="Payment state", compute='_compute_payment_state')

    @api.depends('state')
    def _compute_progress(self):
        for rec in self:
            progress = 0
            if rec.state == 'draft':
                progress = random.randrange(0, 25)
            elif rec.state == 'detect problem':
                progress = random.randrange(25, 69)
            elif rec.state == 'solving':
                progress = random.randrange(70, 99)
            elif rec.state == 'return device':
                progress = 100
            elif rec.state == 'cancel':
                progress = 0
            rec.progress = progress

    @api.depends('move_id')
    def _compute_payment_state(self):
        for rec in self:
            if rec.move_id:
                if rec.move_id.payment_state == 'paid':
                    rec.payment_state = 'paid'
                elif rec.move_id.payment_state == 'not_paid':
                    rec.payment_state = 'not_paid'
                elif rec.move_id.payment_state == 'in_payment':
                    rec.payment_state = 'in_payment'
                elif rec.move_id.payment_state == 'partial':
                    rec.payment_state = 'partial'
                elif rec.move_id.payment_state == 'reversed':
                    rec.payment_state = 'reversed'
                elif rec.move_id.payment_state == 'reversed':
                    rec.payment_state = 'reversed'
            else:
                rec.payment_state = 'not_paid'

    @api.model
    def create(self, vals_list):
        res = super(DeviceMaintenance, self).create(vals_list)
        if res.ref == "New":
            res.ref = self.env['ir.sequence'].next_by_code('device_maintenance_seq')
        return res

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_("You can delete Service only in draft state :("))
        return super(DeviceMaintenance, self).unlink()

    @api.depends('total_price')
    def _compute_total_feeds(self):
        for rec in self:
            total = 0.0
            total = total + ((rec.total_price - rec.discount) * 0.5)
            rec.total_feeds = total

    @api.depends('maintenance_ids')
    def _compute_total_price(self):
        for rec in self:
            total = 0.0
            for line in rec.maintenance_ids:
                total = total + line.total
            rec.total_price = total

    def detect_button(self):
        for rec in self:
            rec.state = 'detect problem'

    def solving_button(self):
        for rec in self:
            if rec.invoice_check:
                rec.state = 'solving'
                return {
                    'effect': {
                        'fadeout': 'slow',
                        'message': 'The Device is Ready :)',
                        'type': 'rainbow_man',
                    }
                }
            else:
                raise ValidationError(_("You can't solving Device without Payment\n"
                                        "please check if invoice is created :("))

    def reset_to_draft(self):
        for rec in self:
            if rec.move_id:
                if rec.move_id.state == 'draft':
                    rec.state = 'draft'
                    rec.active = True
                else:
                    raise UserError("Your Related Invoice must be Draft\nDon't forget reset invoices to drft :)")
            else:
                rec.state = 'draft'
                rec.active = True

    def return_button(self):
        for rec in self:
            if rec.invoice_check:
                rec.state = 'return device'
                return {
                    'effect': {
                        'fadeout': 'slow',
                        'message': 'The Device Delivered successfully :)',
                        'type': 'rainbow_man',
                    }
                }
            else:
                raise ValidationError(_("You can't return Device without Payment\n"
                                        "please check if invoice is created :("))

    def cancel_button(self):
        action = self.env.ref('center_services.cancel_device_action').read()[0]
        return action

    def create_invoice(self):
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        if not journal:
            raise UserError("No sales journal found.")
        for rec in self:
            try:
                line_vals = []
                for line in rec.maintenance_ids:
                    line_vals.append((0, 0, {
                        'name': line.product_id.name,
                        'quantity': line.qit,
                        'price_unit': line.product_price
                    }))
                invoice_vals = {
                    'partner_id': rec.partner_id.id,
                    'move_type': 'out_invoice',
                    'journal_id': journal.id,
                    'invoice_date_due': date.today(),
                    'invoice_line_ids': line_vals,
                    }
                invoice = self.env['account.move'].create(invoice_vals)
                rec.move_id = invoice.id
                rec.invoice_check = True
                rec.create_employee_feeds()
                # self.env.cr.rollbac()
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
                        'name': "Employee Feeds of " + rec.ref,
                        'quantity': 1,
                        'price_unit': rec.total_feeds,
                    }))],
                }
                invoice = self.env['account.move'].create(invoice_vals)
                rec.feeds_id = invoice.id
            except Exception as e:
                raise UserError(f"Error creating Bill: {e}")


class Maintenance(models.Model):
    _name = 'maintenances.type'

    service = fields.Char(string='Service')
    type = fields.Selection([('hardware', 'Hardware'), ('software', 'Software')])
    price = fields.Integer(string='Price')
    status = fields.Boolean(string='Status')
    emp_feeds = fields.Integer(string="Employee Feeds %")
    maintenance_id = fields.Many2one('device.maintenance')
    product_id = fields.Many2one(comodel_name='product.template')
    product_price = fields.Float(related='product_id.list_price', string="Price")
    qit = fields.Integer(string='Quantity', default=1)
    total = fields.Float(string="Total", compute="_compute_total_price")

    @api.depends('qit', 'product_price')
    def _compute_total_price(self):
        for rec in self:
            rec.total = rec.qit * rec.product_price


class DeviceModel(models.Model):
    _name = 'device.model'

    name = fields.Char(tracking=True, required=True, string="Device Model")
    active = fields.Boolean(string="Active", default=True, tracking=True)
    generation = fields.Char(tracking=True, required=True, string="Generation")
    processor = fields.Char(tracking=True, required=True, string="Processor")
    ram_memory = fields.Char(tracking=True, required=True, string="RAM Memory")
    hard_desk = fields.Char(tracking=True, required=True, string="Hard Disk")
    graphic_card = fields.Char(tracking=True, required=True, string="Graphic Card")
    maintenance_id = fields.Many2one(comodel_name='device.maintenance')
