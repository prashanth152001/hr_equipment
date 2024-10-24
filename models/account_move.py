from odoo import models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    maintenance_request_id = fields.Many2one(comodel_name='maintenance.request', string='Maintenance')
    currency_id = fields.Many2one('res.currency', related='maintenance_request_id.currency_id', store=True, readonly=True)
