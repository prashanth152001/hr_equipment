from odoo import fields, models, api, _
from datetime import datetime


class AllAllocations(models.Model):
    _name = 'all.allocations'
    _inherit = ['mail.thread']
    _description = 'All Allocations'
    _rec_name = 'allocation_code'

    allocation_code = fields.Char(string='Allocation Code', default='New')
    subject = fields.Char(string='Subject', required=True, tracking=True)
    assigned_to_id = fields.Many2one(comodel_name='hr.employee', string='Assigned To', required=True, tracking=True)
    allocation_status = fields.Selection([('in_office', 'In Office'), ('remote', 'Remote')], string='Allocation')
    create_date = fields.Datetime(string='Create Date')
    created_by_id = fields.Many2one(comodel_name='res.users', string='Created By')
    approved_by_id = fields.Many2one(comodel_name='res.users', string='Approved By', tracking=True)
    approved_date = fields.Datetime(string='Approved Date')
    priority_status = fields.Selection([('normal', 'Normal'), ('high', 'High')],
                                default='normal', string='Priority')
    description_notes = fields.Text(string='Description')
    warehouse_id = fields.Many2one(comodel_name='stock.warehouse', string='Warehouse')
    source_id = fields.Many2one(comodel_name='stock.location', string='Source')
    destination_id = fields.Many2one(comodel_name='stock.location', string='Destination')
    selection_state = fields.Selection([('new', 'New'),
                                   ('waiting_for_approval', 'Waiting for Approval'),
                                   ('approved', 'Approved'),
                                   ('allocated', 'Allocated'),
                                   ('return', 'Return'),
                                   ('transfer', 'Transfer'),
                                   ('cancel', 'Cancel')],
                                  default='new', tracking=True)
    department_id = fields.Many2one(comodel_name='hr.department', string='Department')
    job_position_id = fields.Many2one(comodel_name='hr.job', string='Job Position')
    category_id = fields.Many2one(comodel_name='maintenance.equipment.category', string='Category')
    equipment_id = fields.Many2one(comodel_name='maintenance.equipment', string='Equipment', tracking=True)
    product_id = fields.Many2one(comodel_name='product.template', string='Product')
    serial_no = fields.Char(string='Serial No')
    scheduled_date = fields.Datetime(string='Scheduled Date')
    previous_allocation_code_id = fields.Many2one(comodel_name='all.allocations', string='Allocation')
    transfer_wizard_id = fields.Many2one(comodel_name='equipment.transfer.wizard', string='Transfer Allocation')
    transfers_count = fields.Integer(string='Transfers Count', compute='_compute_transfers_count')
    inventory_pickings_count = fields.Integer(compute='_compute_inventory_pickings_count')

    @api.onchange('assigned_to_id')
    def _onchange_assigned_to_id(self):
        for rec in self:
            rec.department_id = rec.assigned_to_id.department_id
            rec.job_position_id = rec.assigned_to_id.job_id

    @api.onchange('equipment_id')
    def _onchange_equipment_id(self):
        for rec in self:
            rec.category_id = rec.equipment_id.category_id
            rec.product_id = rec.equipment_id.product_id
            rec.serial_no = rec.equipment_id.serial_no

    def _compute_inventory_pickings_count(self):
        self.inventory_pickings_count = self.env['stock.picking'].search_count(
            domain=[('origin', '=', self.allocation_code)],
        )

    def action_open_inventory_pickings(self):
        return {
            'name': _('Pickings'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'target': 'current',
            'domain': [('origin', '=', self.allocation_code)],
        }

    def _compute_transfers_count(self):
        self.transfers_count = self.env['all.allocations'].search_count(
            domain=[('previous_allocation_code_id', '=', self.id)],
        )

    def action_open_transfer_allocations(self):
        return {
            'name': _('Transfers'),
            'type': 'ir.actions.act_window',
            'res_model': 'all.allocations',
            'view_mode': 'list,form',
            'target': 'current',
            'domain': [('previous_allocation_code_id', '=', self.id)],
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('allocation_code') or vals['allocation_code'] == 'New':
                vals['allocation_code'] = self.env['ir.sequence'].next_by_code('all.allocations')
            vals['created_by_id'] = self.env.user.id
        return super().create(vals_list)

    def action_submit_allocation_request(self):
        for rec in self:
            rec.selection_state = 'waiting_for_approval'
        template = self.env.ref('hr_equipment.email_template_equipment_allocation_approval_request')
        template.send_mail(self.id)

    def action_approve_allocation_request(self):
        for rec in self:
            rec.selection_state = 'approved'
            rec.approved_by_id = self.env.user.id
            rec.approved_date = datetime.today()
        template = self.env.ref('hr_equipment.email_template_equipment_allocation_approval_request')
        template.send_mail(self.id)

    def action_allocate_equipment(self):
        for rec in self:
            # Update the record's selection state
            rec.selection_state = 'allocated'

            # Update the equipment status and employee assignment
            rec.equipment_id.equipment_status = 'occupy'
            rec.equipment_id.employee_id = self.assigned_to_id

            # Find the picking type for delivery orders (outgoing shipments)
            picking_type = rec.env['stock.picking.type'].search([
                ('warehouse_id', '=', rec.warehouse_id.id),
                ('code', '=', 'outgoing')
            ], limit=1)

            # Create a delivery order
            delivery_order = rec.env['stock.picking'].create({
                'partner_id': self.assigned_to_id.user_partner_id.id,
                'origin': rec.allocation_code,
                'picking_type_id': picking_type.id,
                'location_id': rec.source_id.id,  # Specify source location
                'location_dest_id': rec.destination_id.id,  # Specify destination location
                'move_ids': [(0, 0, {
                    'product_id': rec.product_id.id,
                    'product_uom_qty': 1,  # Adjust quantity as needed
                    'product_uom': rec.product_id.uom_id.id,  # Assuming you have a UOM defined
                    'location_id': rec.source_id.id,  # Specify source location
                    'location_dest_id': rec.destination_id.id,  # Specify destination location
                    'name': rec.product_id.name,
                })],
            })
        template = self.env.ref('hr_equipment.email_template_equipment_allocation_notification')
        template.send_mail(self.id)

    def action_return_allocated_equipment(self):
        for rec in self:
            # Update the record's selection state
            rec.selection_state = 'return'

            # Update the equipment status and employee assignment
            rec.equipment_id.equipment_status = 'free'
            rec.equipment_id.employee_id = ""

            # Find the picking type for picking orders (incoming shipments)
            picking_type = rec.env['stock.picking.type'].search([
                ('warehouse_id', '=', rec.warehouse_id.id),
                ('code', '=', 'incoming')
            ], limit=1)

            # Create a picking order
            picking_order = rec.env['stock.picking'].create({
                'partner_id': self.assigned_to_id.user_partner_id.id,
                'origin': rec.allocation_code,
                'picking_type_id': picking_type.id,
                'location_id': rec.source_id.id,  # Specify source location
                'location_dest_id': rec.destination_id.id,  # Specify destination location
                'move_ids': [(0, 0, {
                    'product_id': rec.product_id.id,
                    'product_uom_qty': 1,  # Adjust quantity as needed
                    'product_uom': rec.product_id.uom_id.id,  # Assuming you have a UOM defined
                    'location_id': rec.source_id.id,  # Specify source location
                    'location_dest_id': rec.destination_id.id,  # Specify destination location
                    'name': rec.product_id.name,
                })],
            })
        template = self.env.ref('hr_equipment.email_template_equipment_return_notification')
        template.send_mail(self.id)

    def action_transfer_allocation_equipment(self):
        for rec in self:
            rec.selection_state = 'transfer'
            # rec.transfer_wizard_id.previous_allocation_code_id = rec.id
        return {
            'name': _('Transfer'),
            'type': 'ir.actions.act_window',
            'res_model': 'equipment.transfer.wizard',
            'view_mode': 'form',
            'context': {'default_previous_allocation_code_id': self.id},
            'target': 'new',
        }

    def action_cancel_allocation_request(self):
        for rec in self:
            rec.selection_state = 'cancel'

    def action_set_to_draft(self):
        for rec in self:
            rec.selection_state = 'new'

    # List view approve button action
    def action_approve_selected_allocation_requests(self):
        for rec in self:
            if rec.selection_state == 'waiting_for_approval':
                rec.selection_state = 'approved'
                rec.approved_by_id = self.env.user.id
                rec.approved_date = datetime.today()
                template = rec.env.ref('hr_equipment.email_template_equipment_allocation_approval_request')
                template.send_mail(rec.id)
        return True