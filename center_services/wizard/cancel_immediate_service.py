from odoo import models, fields, api
from datetime import date


class CancelImmediateService(models.TransientModel):
    _name = 'cancel.immediate'

    immediate_id = fields.Many2one(comodel_name="immediate.services", string="Service References", readonly=True)
    date = fields.Date(string="Cancel Date", required=True)
    reason = fields.Char(string="Reason", required=True)

    @api.model
    def default_get(self, fields):
        res = super(CancelImmediateService, self).default_get(fields)
        res['date'] = date.today()
        if self.env.context.get('active_id'):
            res['immediate_id'] = self.env.context.get('active_id')
        return res

    def cancel_service(self):
        for rec in self:
            rec.immediate_id.state = 'cancel'
            rec.immediate_id.active = False
            rec.immediate_id.cancel_date = rec.date
            rec.immediate_id.reason = rec.reason
