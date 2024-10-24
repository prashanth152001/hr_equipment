from odoo import models, fields


class MaintenanceChecklist(models.Model):
    _name = 'maintenance.checklist'
    _description = 'Maintenance Checklist'

    check_description = fields.Char(string='Description')
    name = fields.Char(string='Name', required=True)
    maintenance_request_id = fields.Many2one(comodel_name='maintenance.request', string='Maintenance Request')