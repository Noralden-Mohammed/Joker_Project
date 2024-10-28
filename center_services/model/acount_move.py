from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def print_invoice_temp(self):
        return self.env.ref("center_services.action_print_invoice").report_action(self)
