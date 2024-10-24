from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    equipment_ok = fields.Boolean(string='Can be Equipment')
    maintenance_team_id = fields.Many2one(comodel_name='maintenance.team', string='Maintenance Team')
    category_id = fields.Many2one(comodel_name='maintenance.equipment.category', string='Category')
    technician_id = fields.Many2one(comodel_name='res.users', string='Technician')
    used_by = fields.Selection([('department', 'Department'), ('employee', 'Employee'), ('other', 'Other')],
                               string='Used By')

    equipment_ids = fields.One2many(comodel_name='maintenance.equipment', inverse_name='product_id', string='Equipments', readonly=True)

    @api.model
    def create(self, vals):
        # Create the product template
        product = super(ProductTemplate, self).create(vals)

        # If the product is marked as equipment, check if it needs to create equipment
        if product.equipment_ok:
            product._create_equipment_on_serials()
        return product

    def write(self, vals):
        # Call super to update the product template
        result = super(ProductTemplate, self).write(vals)

        # Handle equipment creation or deletion based on the checkbox
        for product in self:
            if 'equipment_ok' in vals:
                if vals['equipment_ok'] and not product.equipment_ids:
                    product._create_equipment_on_serials()
                elif not vals['equipment_ok'] and product.equipment_ids:
                    product.equipment_ids.unlink()  # Optionally delete the equipment

        return result

    def _create_equipment_on_serials(self):
        """Create equipment records for each serial number of the product."""
        # Assuming you want to create an equipment for each serial number
        for serial_number in self._get_serial_numbers():
            equipment_vals = {
                'name': f"{self.name} - {serial_number}",
                'category_id': self.category_id.id,
                'equipment_assign_to': self.used_by,
                'maintenance_team_id': self.maintenance_team_id.id,
                'technician_user_id': self.technician_id.id,
                'serial_no': serial_number,  # You will need to store the serial number
                'product_id': self.id,
            }
            equipment = self.env['maintenance.equipment'].create(equipment_vals)
            self.equipment_ids |= equipment  # Add the equipment to the One2many relation

    def _get_serial_numbers(self):
        """Fetch serial numbers related to this product."""
        # Fetch the serial numbers from stock production lots or any other model storing them
        serial_numbers = self.env['stock.lot'].search([('product_id', '=', self.id)])
        return serial_numbers.mapped('name')