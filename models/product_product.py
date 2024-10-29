from odoo import models, fields


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _create_equipment_for_serial(self, lot):
        """Create equipment records for each serial number during stock receipt."""
        equipment_vals = {
            'name': f"{self.name} - {lot.name}",
            'category_id': self.category_id.id,
            'equipment_assign_to': self.used_by,
            'maintenance_team_id': self.maintenance_team_id.id,
            'technician_user_id': self.technician_id.id,
            'serial_no': lot.name,  # Serial number from lot
            'product_id': self.id,
            'processor_type': self.processor_type,
            'ram_size': self.ram_size,
            'rom_size': self.rom_size,
        }
        self.env['maintenance.equipment'].create(equipment_vals)