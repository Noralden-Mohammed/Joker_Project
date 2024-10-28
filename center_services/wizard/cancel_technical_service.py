from odoo import models, fields, api
from datetime import date


class CancelTechnicalService(models.TransientModel):
    _name = 'cancel.technical'

    cancel_date = fields.Date(required=True)
    reason = fields.Char(required=True)
    technical_id = fields.Many2one(comodel_name='technical.support', readonly=True, required=True)

    @api.model
    def default_get(self, fields):
        res = super(CancelTechnicalService, self).default_get(fields)
        res['cancel_date'] = date.today()
        if self.env.context.get('active_id'):
            res['technical_id'] = self.env.context.get('active_id')
        return res

    def cancel_service(self):
        for rec in self:
            rec.technical_id.state = 'cancel'
            rec.technical_id.cancel_date = rec.cancel_date
            rec.technical_id.reason = rec.reason
