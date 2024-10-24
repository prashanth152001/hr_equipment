from odoo import models, fields


class ProjectTask(models.Model):
    _inherit = 'project.task'

    maintenance_request_id = fields.Many2one(comodel_name='maintenance.request', string='Maintenance')
    priority = fields.Selection([('0', 'Low'), ('1', 'High')],
                                default='0', string='Priority')
