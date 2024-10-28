from odoo import models, fields, api


class Connections(models.Model):

    _name = 'connections'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Connection type')
    code = fields.Char(string='Code')
    price = fields.Integer(string='Price')
    ref = fields.Char(readonly=True, default='New')

    @api.model
    def create(self, vals):
        res = super(Connections, self).create(vals)
        if res.ref == 'New':
            res.ref = self.env['ir.sequence'].next_by_code('Connections_seq')
        return res
