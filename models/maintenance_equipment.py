from odoo import models, fields, api


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    product_id = fields.Many2one(comodel_name='product.template', string='Product')
    equipment_status = fields.Selection([
        ('free', 'Free'),
        ('occupy', 'Occupy'),
        ('maintenance', 'Maintenance'),
    ], default='free', string='Status')
    processor_type = fields.Selection([('0', 'i3'),
                                       ('1', 'i5'),
                                       ('2', 'i7'),
                                       ('3', 'i9')], string='Processor')
    ram_size = fields.Selection([('0', '4GB'),
                                 ('1', '8GB'),
                                 ('2', '16GB')], string='RAM')
    rom_size = fields.Selection([('0', '256SSD'),
                                 ('1', '512SSD'),
                                 ('2', '1TB')], string='ROM')
    show_laptop_fields = fields.Boolean(compute='_compute_show_laptop_fields', store=True)

    @api.depends('category_id')
    def _compute_show_laptop_fields(self):
        for record in self:
            record.show_laptop_fields = record.category_id.name == 'Laptop'
