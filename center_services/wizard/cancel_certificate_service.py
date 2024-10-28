from odoo import models, fields, api
from datetime import date


class CancelCertificateService(models.TransientModel):
    _name = 'cancel.certificate'

    certificate_id = fields.Many2one(comodel_name="certificate.management", string="Service References", readonly=True)
    date = fields.Date(string="Cancel Date", required=True)
    reason = fields.Char(string="Reason", required=True)

    @api.model
    def default_get(self, fields):
        res = super(CancelCertificateService, self).default_get(fields)
        res['date'] = date.today()
        if self.env.context.get('active_id'):
            res['certificate_id'] = self.env.context.get('active_id')
        return res

    def cancel_service(self):
        for rec in self:
            rec.certificate_id.state = 'cancel'
            rec.certificate_id.cancel_date = rec.date
            rec.certificate_id.reason = rec.reason
