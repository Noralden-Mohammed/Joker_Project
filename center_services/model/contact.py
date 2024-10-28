from odoo import fields, models, _


class ImmedaiteServicesContact(models.Model):

    _inherit = ['res.partner']

    services_ids = fields.One2many('immediate.services', string='Service', inverse_name='partner_id')
    services_count = fields.Integer(string="Services Count", compute='_compute_service_count')
    is_employee = fields.Boolean(string="Is Employee", compute="_compute_is_employee", store=True)

    def _compute_is_employee(self):
        for partner in self:
            count = self.env['hr.employee'].search_count([('work_email', '=', partner.email)])
            if count > 0:
                partner.is_employee = True

    def _compute_service_count(self):
        for rec in self:
            app_count = self.env['immediate.services'].search_count([('partner_id', '=', rec.name)])
            rec.services_count = app_count

    def action_service_search(self):
        return {
            'name': _('Services'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'immediate.services',
            'target': 'current',
            'domain': [('partner_id', '=', self.id)],
        }
