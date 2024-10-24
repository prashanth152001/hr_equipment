from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    maintenance_request_id = fields.Many2one(comodel_name='maintenance.request', string='Maintenance')

    def button_validate(self):
        """Extend the stock picking validation process to create equipment for serial numbers."""
        # First, call the original `button_validate` method using `super()`
        res = super(StockPicking, self).button_validate()

        # Now, proceed with your custom logic after the picking is validated
        for move_line in self.move_line_ids:
            product = move_line.product_id
            # Check if the product is marked as equipment and has serial tracking
            if product.equipment_ok and move_line.lot_id:
                # Ensure that no equipment already exists with the same serial number (lot_id)
                existing_equipment = self.env['maintenance.equipment'].search(
                    [('serial_no', '=', move_line.lot_id.name)], limit=1)

                if existing_equipment:
                    raise UserError(
                        _('Another asset already exists with the serial number: %s' % move_line.lot_id.name))

                # If no equipment exists, create a new equipment entry
                product._create_equipment_for_serial(move_line.lot_id)

        return res

    def action_view_moves(self):
        self.ensure_one()
        return {
            'name': _('Stock Moves'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.move',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.move_ids.ids)],
        }