from odoo import models, fields, api
from datetime import date


class CancelDeviceService(models.TransientModel):
    _name = 'cancel.device'

    device_id = fields.Many2one(comodel_name="device.maintenance", string="Service References", readonly=True)
    date = fields.Date(string="Cancel Date", required=True)
    reason = fields.Char(string="Reason", required=True)

    @api.model
    def default_get(self, fields):
        res = super(CancelDeviceService, self).default_get(fields)
        res['date'] = date.today()
        if self.env.context.get('active_id'):
            res['device_id'] = self.env.context.get('active_id')
        return res

    def cancel_service(self):
        for rec in self:
            rec.device_id.state = 'cancel'
            rec.device_id.active = False
            rec.device_id.cancel_date = rec.date
            rec.device_id.reason = rec.reason
