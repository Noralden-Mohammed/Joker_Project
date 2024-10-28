from odoo import models, fields, api


class Services(models.Model):

    _name = 'services'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='service type')
    code = fields.Char(string='Code')
    price = fields.Integer(string='Price')
    employee_feeds = fields.Integer(string='Employee Feeds%')
    ref = fields.Char(readonly=True, default='New')

    @api.model
    def create(self, vals):
        res = super(Services, self).create(vals)
        if res.ref == 'New':
            res.ref = self.env['ir.sequence'].next_by_code('Services_seq')
        return res
