from odoo import models, fields


class DamageDetails(models.Model):
    _name = 'damage.details'
    _description = 'Damage Details'
    _rec_name = 'damage_description'

    damage_description = fields.Char(string='Description', required=True)
    date = fields.Date(string='Date')
    maintenance_request_id = fields.Many2one(comodel_name='maintenance.request', string='Maintenance Request')