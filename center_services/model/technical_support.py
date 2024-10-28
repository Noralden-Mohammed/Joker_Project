from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
import random



class TechnicalSupport(models.Model):

    _name = 'technical.support'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'ref'

    partner_id = fields.Many2one('res.partner', string='Customer Name', tracking=True)
    phone = fields.Char(related='partner_id.phone')
    email = fields.Char(related='partner_id.email')
    state = fields.Selection(selection=[('draft', 'Draft'), ('in_consultation', 'In Consultation'), ('done', 'Done')
                                        , ('cancel', 'Cancel')], default='draft', tracking=True)
    ref = fields.Char(default="New", tracking=True, string="References", readonly=True)
    description = fields.Text(string="Description", tracking=True)
    date = fields.Datetime(string="Date", default=fields.Date.today(), tracking=True)
    technical_ids = fields.One2many(comodel_name='technical.line', inverse_name='technical_id')
    total_line = fields.Float(string="Total Line", tracking=True, readonly=True, compute='_compute_total_line')
    total_price = fields.Float(string="Total Price", tracking=True, readonly=True, compute='_compute_total_price')
    package_ids = fields.One2many(comodel_name='package.service', inverse_name='technical_id')
    total_package = fields.Float(tracking=True, readonly=True, compute='_compute_total_package_price')
    employee_ids = fields.One2many(comodel_name='employee.feeds', inverse_name='technical_id')
    total_feeds = fields.Float(string="Total Employee Feeds", tracking=True, readonly=True,
                               compute='_compute_total_feeds')
    cancel_date = fields.Date(string="Cancel Date", tracking=True, readonly=True)
    reason = fields.Char(string="Cancel Reason", tracking=True, readonly=True)
    invoice_id = fields.Many2one(comodel_name='account.move', readonly=True, reacking=True,
                                 string="Related Invoice")
    bill_id = fields.Many2one(comodel_name='account.move', readonly=True, reacking=True,
                              string="Related Items Bill")
    invoice_check = fields.Boolean(default=False, readonly=True, reacking=True)
    bill_check = fields.Boolean(default=False, readonly=True, reacking=True)
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Low'),
        ('2', 'High'),
        ('3', 'Very High')], string="Priority", )
    progress = fields.Integer(string='Preogress', compute="_compute_progress")
    discount = fields.Float(string="Discount", tracking=True)

    def unlink(self):
        if self.state != 'draft':
            raise ValidationError(_("You can delete Service only in draft state :("))
        else:
            return super(TechnicalSupport, self).unlink()

    def button_confirm(self):
        for rec in self:
            rec.state = 'in_consultation'

    def button_done(self):
        for rec in self:
            rec.state = 'done'
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': 'The Certificate Delivered successfully :)',
                    'type': 'rainbow_man',
                }
            }

    def button_cancel(self):
        action = self.env.ref('center_services.cancel_technical_action').read()[0]
        return action

    def button_rest_draft(self):
        for rec in self:
            rec.state = 'draft'

    @api.depends('technical_ids')
    def _compute_total_line(self):
        total = 0.0
        for rec in self:
            for line in rec.technical_ids:
                total = total + line.total
            rec.total_line = total

    @api.depends('package_ids')
    def _compute_total_package_price(self):
        total = 0.0
        for rec in self:
            for line in rec.package_ids:
                total = total + line.price
            rec.total_package = total

    @api.depends('employee_ids')
    def _compute_total_feeds(self):
        total = 0.0
        for rec in self:
            for line in rec.employee_ids:
                total = total + line.feeds
            rec.total_feeds = total

    @api.depends('total_line', 'total_package', 'discount')
    def _compute_total_price(self):
        for rec in self:
            rec.total_price = rec.total_line + rec.total_package - rec.discount

    @api.model
    def create(self, vals):
        res = super(TechnicalSupport, self).create(vals)
        if res.ref == 'New':
            res.ref = self.env['ir.sequence'].next_by_code('technical_support_seq')
        return res

    def create_invoice(self):
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        if not journal:
            raise UserError("No sales journal found.")
        for rec in self:
            try:
                line_vals = []
                for line in rec.package_ids:
                    line_vals.append((0, 0, {
                                    'name': line.connections_id.name,
                                    'quantity': 1,
                                    'price_unit': line.price,
                                }))

                for line in rec.technical_ids:
                    line_vals.append((0, 0, {
                                    'name': line.product_id.name,
                                    'quantity': line.qit,
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
                rec.button_confirm()
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
                for line in rec.technical_ids:
                    line_vals.append((0, 0, {
                        'name': "Cost of " + line.product_id.name,
                        'quantity': line.qit,
                        'price_unit': line.product_id.standard_price,
                    }))
                invoice_vals = {
                    'partner_id': rec.partner_id.id,
                    'move_type': 'in_invoice',
                    'journal_id': journal.id,
                    'invoice_date_due': fields.date.today(),
                    'invoice_date': rec.date,
                    'invoice_line_ids': line_vals,
                }
                invoice = self.env['account.move'].create(invoice_vals)
                rec.bill_id = invoice.id
                rec.bill_check = True
            except Exception as e:
                raise UserError(f"Error creating Bill: {e}")

    def create_employee_feeds(self):
        journal = self.env['account.journal'].search([('type', '=', 'purchase')], limit=1)
        if not journal:
            raise UserError("No Purchase journal found.")
        for rec in self:
            try:
                line_vals = []
                for line in rec.employee_ids:
                    line_vals.append((0, 0, {
                        'name': "Employee Feeds Service ID: " + rec.ref,
                        'quantity': 1,
                        'price_unit': line.feeds
                    }))
                    invoice_vals = {
                        'partner_id': line.partner_id.id,
                        'move_type': 'in_invoice',
                        'journal_id': journal.id,
                        'invoice_date_due': fields.date.today(),
                        'invoice_date': rec.date,
                        'invoice_line_ids': line_vals,
                    }
                    invoice = self.env['account.move'].create(invoice_vals)
                    line.feeds_id = invoice.id
            except Exception as e:
                raise UserError(f"Error creating Bill: {e}")

    @api.depends('state')
    def _compute_progress(self):
        for rec in self:
            progress = 0
            if rec.state == 'draft':
                progress = random.randrange(0, 50)
            elif rec.state == 'in_consultation':
                progress = random.randrange(50, 99)
            elif rec.state == 'done':
                progress = 100
            elif rec.state == 'cancel':
                progress = 0
            rec.progress = progress


class TechnicalSupportLine(models.Model):
    _name = 'technical.line'

    technical_id = fields.Many2one(comodel_name='technical.support')
    product_id = fields.Many2one(comodel_name='product.template', string='Items')
    price = fields.Float(related='product_id.list_price')
    qit = fields.Integer(string='Quantity', default=1)
    uint = fields.Many2one(comodel_name='uom.uom', realated='product_id.uom_id.id')
    total = fields.Float(string="Total", compute="_compute_total_price")

    @api.depends('qit', 'price')
    def _compute_total_price(self):
        for rec in self:
            rec.total = rec.qit * rec.price


class PackageService(models.Model):
    _name = 'package.service'

    connections_id = fields.Many2one('connections',string='Package Service', tracking=True)
    code = fields.Char(related='connections_id.ref', tracking=True)
    price = fields.Integer(related='connections_id.price', tracking=True, string="Package Price")
    technical_id = fields.Many2one(comodel_name='technical.support')


class EmployeeFeeds(models.Model):
    _name = 'employee.feeds'

    partner_id = fields.Many2one(comodel_name='res.partner', string="Employee Name")
    feeds = fields.Float(string="Employee Feeds")
    technical_id = fields.Many2one(comodel_name='technical.support')
    feeds_id = fields.Many2one(comodel_name='account.move', string="Related Bill", readonly=True)


