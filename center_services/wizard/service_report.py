# -*- coding: utf-8 -*-
from odoo import models, fields
from odoo.exceptions import UserError
import logging


_logger = logging.getLogger(__name__)


class ServiceReport(models.TransientModel):
    _name = 'service.report'

    start_date = fields.Date(string="Date From")
    end_date = fields.Date(string="Date To")
    costumer_id = fields.Many2one(comodel_name='res.partner', string="Costumer")
    employee_id = fields.Many2one(comodel_name='res.partner', string="Employee")

    def get_report(self):
        # requests = self.env['movement.request'].get_requests_between_dates(self.start_date, self.end_date)
        # domain = self.env['requisition.request'].search([('request_date', '>=', self.start_date), ('request_date', '<=', self.end_date),('state', '=', '5')])
        domain = []
        if self.start_date:
            domain.append(('request_date', '>=', self.start_date))

        if self.end_date:
            domain.append(('request_date', '<=', self.end_date))

        if self.project_id:
            domain.append(('program_id', '=', self.project_id.id))

        res = self.env['requisition.request'].search(domain)
        if not res:
            raise UserError('No records found pleas check your selected date and service .')
        _logger.info('Requests found: %s', res)
        # return self.env.ref('requisition.request').search(domain)
        return self.env.ref('sstc_altwaki_project.report_request').report_action(res)