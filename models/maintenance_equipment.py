from odoo import models, fields


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    product_id = fields.Many2one(comodel_name='product.template', string='Product')
    equipment_status = fields.Selection([
        ('free', 'Free'),
        ('occupy', 'Occupy'),
        ('maintenance', 'Maintenance'),
    ], default='free', string='Status')