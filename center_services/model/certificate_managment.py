from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import random


class CertificateManagement(models.Model):
    _name = 'certificate.management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'ref'

    partner_id = fields.Many2one('res.partner', string="Customer", required=True, tracking=True)
    date = fields.Date(required=True, tracking=True, default=fields.Date.today())
    phone = fields.Char(related="partner_id.phone", tracking=True)
    email = fields.Char(related="partner_id.email", tracking=True)
    price = fields.Float(tracking=True, string="Total Price", compute="_compute_total_price")
    employee_feeds = fields.Float(tracking=True, string="Employee Feeds", compute="_compute_employee_feeds")
    state = fields.Selection(selection=[('draft', 'Draft'), ('confirm', 'Confirm'), ('send', 'Send'), ('done', 'Done'),
                                        ('delivery', 'Delivery'), ('cancel', 'Cancel')], default="draft", tracking=True)
    certificate_line = fields.One2many(comodel_name="certificate.line", inverse_name="certificate_id", tracking=True)
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Low'),
        ('2', 'High'),
        ('3', 'Very High')], string="Priority", )
    progress = fields.Integer(string='Preogress', compute="_compute_progress")
    ref = fields.Char(default="New", tracking=True, readonly=True, string="References")
    cancel_date = fields.Date(string="Cancel Date", tracking=True, readonly=True)
    reason = fields.Char(string="Cancel Reason", tracking=True, readonly=True)
    invoice_check = fields.Boolean(default=False, tracking=True)
    bill_check = fields.Boolean(default=False, tracking=True)
    feeds_check = fields.Boolean(default=False, tracking=True)
    employee_user = fields.Many2one(comodel_name="res.partner", domain=[('is_employee', '=', True)])
    invoice_id = fields.Many2one(comodel_name="account.move", string="Customer Invoice", tracking=True, readonly=True)
    bill_id = fields.Many2one(comodel_name="account.move", string="Cost Bill", tracking=True, readonly=True)
    feeds_id = fields.Many2one(comodel_name="account.move", string="Feeds Bill", tracking=True, readonly=True)
    discount = fields.Float(string="Discount", tracking=True)
    active = fields.Boolean(string="Discount", tracking=True)

    def button_send(self):
        for rec in self:
            if rec.invoice_check:
                rec.state = 'send'
                rec.employee_user = self.env.user.partner_id
            else:
                raise UserError("Sorry you can't send without invoice ^_^"
                                      "\nCreate Invoice First Please !"
                                      "\nWith my Love :)")

    def button_confirm(self):
        for rec in self:
            rec.state = 'confirm'

    def button_done(self):
        for rec in self:
            rec.state = 'done'
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'The Service Done Successfully :)',
                'type': 'rainbow_man',
            }
        }

    def button_delivery(self):
        for rec in self:
            rec.state = 'delivery'
            rec.active
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'The Certificate Delivered successfully :)',
                'type': 'rainbow_man',
            }
            }

    def button_cancel(self):
        action = self.env.ref('center_services.cancel_certificate_action').read()[0]
        return action

    def button_rest_to_draft(self):
        for rec in self:
            rec.state = 'draft'

    @api.depends('state')
    def _compute_progress(self):
        for rec in self:
            progress = 0
            if rec.state == 'draft':
                progress = random.randrange(0, 25)
            elif rec.state == 'confirm':
                progress = random.randrange(25, 50)
            elif rec.state == 'send':
                progress = random.randrange(50, 70)
            elif rec.state == 'done':
                progress = random.randrange(70, 99)
            elif rec.state == 'delivery':
                progress = 100
            elif rec.state == 'cancel':
                progress = 0
            rec.progress = progress

    @api.depends('certificate_line')
    def _compute_total_price(self):
        for rec in self:
            total = 0.0
            for line in rec.certificate_line:
                total += line.price
            rec.price = total - rec.discount

    @api.depends('certificate_line')
    def _compute_employee_feeds(self):
        for rec in self:
            feeds = 0.0
            for line in rec.certificate_line:
                feeds += (line.price * (line.feeds / 100))
            rec.employee_feeds = feeds - rec.discount

    @api.model
    def create(self, vals_list):
        res = super(CertificateManagement, self).create(vals_list)
        if res.ref == "New":
            res.ref = self.env['ir.sequence'].next_by_code('certificate_service_seq')
        return res

    def unlink(self):
        if self.state != 'draft':
            raise ValidationError(_("You can delete Service only in draft state :("))
        else:
            return super(CertificateManagement, self).unlink()

    def create_invoice(self):
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        if not journal:
            raise UserError("No sales journal found.")
        for rec in self:
            try:
                line_vals = []
                for line in rec.certificate_line:
                    line_vals.append((0, 0, {
                                    'name': line.service_id.certificate_service,
                                    'quantity': 1,
                                    'price_unit': line.price,
                                }))
                if rec.discount:
                    line_vals.append((0, 0, {
                                        'name': "Discount",
                                        'quantity': 1,
                                        'price_unit': 0 - rec.discount,
                                    }))
                invoice_vals = {
                    'partner_id': rec.partner_id.id,
                    'move_type': 'out_invoice',
                    'journal_id': journal.id,
                    'invoice_date_due': fields.date.today(),
                    'invoice_date': rec.date,
                    'invoice_line_ids': line_vals,
                }
                invoice = self.env['account.move'].create(invoice_vals)
                rec.invoice_id = invoice.id
                # self.env.cr.rollbac()
                rec.invoice_check = True
                rec.create_bill()
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

    def create_bill(self):
        journal = self.env['account.journal'].search([('type', '=', 'purchase')], limit=1)
        if not journal:
            raise UserError("No Purchase journal found.")
        for rec in self:
            try:
                line_vals = []
                for line in rec.certificate_line:
                    line_vals.append((0, 0, {
                        'name': "Cost of " + line.service_id.certificate_service,
                        'quantity': 1,
                        'price_unit': line.cost,
                    }))
                invoice_vals = {
                    'partner_id': rec.partner_id.id,
                    'move_type': 'in_invoice',
                    'journal_id': journal.id,
                    'invoice_date_due': fields.date.today(),
                    'invoice_date': rec.date,
                    'invoice_line_ids':line_vals,
                }
                invoice = self.env['account.move'].create(invoice_vals)
                rec.bill_id = invoice.id
                rec.bill_check = True
                # return {
                #     'type': 'ir.actions.act_window',
                #     'name': 'Customer Invoice',
                #     'view_mode': 'form',
                #     'res_model': 'account.move',
                #     'res_id': invoice.id,
                #     'target': 'current',
                # }
            except Exception as e:
                raise UserError(f"Error creating Bill: {e}")

    def create_employee_feeds(self):
        journal = self.env['account.journal'].search([('type', '=', 'purchase')], limit=1)
        if not journal:
            raise UserError("No Purchase journal found.")
        for rec in self:
            try:
                line_vals = []
                for line in rec.certificate_line:
                    line_vals.append((0, 0, {
                        'name': "Employee Feeds of " + line.service_id.certificate_service,
                        'quantity': 1,
                        'price_unit': line.price * (line.feeds / 100)
                    }))
                invoice_vals = {
                    'partner_id': rec.employee_user.id,
                    'move_type': 'in_invoice',
                    'journal_id': journal.id,
                    'invoice_date_due': fields.date.today(),
                    'invoice_date': rec.date,
                    'invoice_line_ids': line_vals,
                }
                invoice = self.env['account.move'].create(invoice_vals)
                rec.feeds_id = invoice.id
                rec.feeds_check = True
                # return {
                #     'type': 'ir.actions.act_window',
                #     'name': 'Customer Invoice',
                #     'view_mode': 'form',
                #     'res_model': 'account.move',
                #     'res_id': invoice.id,
                #     'target': 'current',
                # }
            except Exception as e:
                raise UserError(f"Error creating Bill: {e}")


class CertificateService(models.Model):
    _name = 'certificate.service'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'certificate_service'

    certificate_type = fields.Selection(selection=[('extract', 'Extract'), ('documentation', 'Documentation')],
                                        required=True, tracking=True, string="Service Type")
    certificate_service = fields.Char(required=True, tracking=True, string="Service Name")
    price = fields.Float(required=True, tracking=True, string="Service Price")
    cost = fields.Float(required=True, tracking=True, string="Service Cost")
    employee_feeds = fields.Integer(required=True, tracking=True, string="Employee Feeds %")
    code = fields.Char(tracking=True, required=True, string="Code")
    certificate_id = fields.Many2one(comodel_name='certificate.management')


class CertificateLine(models.Model):
    _name = 'certificate.line'

    service_id = fields.Many2one(comodel_name='certificate.service', string="Service", required=True, tracking=True)
    service_type = fields.Selection(related='service_id.certificate_type', tracking=True, string="Service Type")
    price = fields.Float(related='service_id.price', tracking=True)
    cost = fields.Float(related='service_id.cost', tracking=True)
    feeds = fields.Integer(related='service_id.employee_feeds', tracking=True)
    certificate_no = fields.Char(string="Certificate No", tracking=True)
    siting_number = fields.Char(string="Siting Number", tracking=True)
    certificate_id = fields.Many2one(comodel_name="certificate.management")


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    address_home_id = fields.Many2one(comodel_name='res.partner', string="Address Home")