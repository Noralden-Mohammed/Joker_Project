from odoo import models, fields, api


class Devices(models.Model):

    _name = 'devices'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Device type')
    code = fields.Char(string='Code')
    maintenance_type = fields.Char(string='Maintenance Type')
    ref = fields.Char(readonly=True, default='New')

    @api.model
    def create(self, vals):
        res = super(Devices, self).create(vals)
        if res.ref == 'New':
            res.ref = self.env['ir.sequence'].next_by_code('Devices_seq')
        return res
