from odoo import models, fields, _


class EquipmentTransferWizard(models.Model):
    _name = 'equipment.transfer.wizard'
    _description = 'Equipment Transfer Wizard'

    assigned_to_id = fields.Many2one(comodel_name='hr.employee', string='Assigned To')
    previous_allocation_code_id = fields.Many2one(comodel_name='all.allocations', string='Previous Allocation')

    def action_create_allocation_request(self):
        transfer_allocation = self.env['all.allocations'].create({
            'subject': self.previous_allocation_code_id.subject,
            'assigned_to_id': self.assigned_to_id.id,
            'allocation_status': self.previous_allocation_code_id.allocation_status,
            'previous_allocation_code_id': self.previous_allocation_code_id.id,
        })
        self.previous_allocation_code_id.previous_allocation_code_id = transfer_allocation.id
        self.previous_allocation_code_id.transfer_wizard_id = self.id