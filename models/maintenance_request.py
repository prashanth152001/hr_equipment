from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.populate import compute


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'
    _rec_name = 'name'

    product_id = fields.Many2one(comodel_name='product.template', string='Product')
    project_id = fields.Many2one(comodel_name='project.project', string='Project')
    request_status = fields.Selection([('new_request', 'New Request'),
                                       ('wait_for_approval', 'Wait for Approval'),
                                       ('approved', 'Approved'),
                                       ('in_progress', 'In Progress'),
                                       ('repaired', 'Repaired'),
                                       ('scrap', 'Scrap'),
                                       ('invoiced', 'Invoiced'),
                                       ('cancel', 'Cancelled')],
                                      default='new_request', string='Request Status', tracking=True)
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  default=lambda self: self.env.company.currency_id)
    damage_details_ids = fields.One2many(comodel_name='damage.details', inverse_name='maintenance_request_id',
                                         string='Damage Details')
    maintenance_checklist_ids = fields.One2many(comodel_name='maintenance.checklist',
                                                inverse_name='maintenance_request_id',
                                                string='Checklist')
    component_line_ids = fields.One2many(comodel_name='maintenance.components', inverse_name='component_id',
                                    string='Components')
    components_total_amount = fields.Monetary(string='Components Total', compute='_compute_components_total_amount',
                                              store=True, currency_field='currency_id')
    job_details_line_ids = fields.One2many(comodel_name='project.task', inverse_name='maintenance_request_id',
                                           string='Job Details')
    hours_spent = fields.Float(string='Hours Spent', compute='_compute_hours_spent')
    job_orders_count = fields.Integer(string='Job Orders Count', compute='_compute_job_orders_count')
    stock_movement_line_ids = fields.One2many(comodel_name='stock.picking',
                                              inverse_name='maintenance_request_id',
                                              string='Stock Movement Lines')
    stock_movements_count = fields.Integer(string='Stock Movements Count', compute='_compute_stock_movements_count')
    expense_details_line_ids = fields.One2many(comodel_name='account.move',
                                               inverse_name='maintenance_request_id',
                                               string='Expense Details Lines')
    expense_details_count = fields.Integer(string='Expense Details Count', compute='_compute_expense_details_count')
    untaxed_expenses = fields.Monetary(string='Untaxed Expenses', compute='_compute_total_expenses',
                                       store=True, currency_field='currency_id')
    taxed_expenses = fields.Monetary(string='Taxed Expenses', compute='_compute_total_expenses',
                                     store=True, currency_field='currency_id')
    total_expenses = fields.Monetary(string='Total Expenses', compute='_compute_total_expenses',
                                     store=True, currency_field='currency_id')
    location_id = fields.Many2one(comodel_name='stock.location', string='Source Location')
    location_dest_id = fields.Many2one(comodel_name='stock.location', string='Destination Location')

    @api.onchange('equipment_id')
    def _onchange_equipment_id(self):
        for record in self:
            record.product_id = record.equipment_id.product_id.id

    @api.depends('job_details_line_ids.total_hours_spent')
    def _compute_hours_spent(self):
        for record in self:
            record.hours_spent = sum(task.total_hours_spent for task in record.job_details_line_ids)

    @api.depends('component_line_ids.subtotal')
    def _compute_components_total_amount(self):
        for record in self:
            total = sum(component.subtotal for component in record.component_line_ids)
            record.components_total_amount = total

    # Computing total expenses
    @api.depends('expense_details_line_ids.amount_total')
    def _compute_total_expenses(self):
        for record in self:
            total_expense = sum(expense.amount_total for expense in record.expense_details_line_ids)
            untaxed_expense = sum(expense.amount_untaxed for expense in record.expense_details_line_ids)
            taxed_expense = sum(expense.amount_tax for expense in record.expense_details_line_ids)
            record.total_expenses = total_expense
            record.untaxed_expenses = untaxed_expense
            record.taxed_expenses = taxed_expense

    # Computing job orders count
    @api.depends('job_details_line_ids.name')
    def _compute_job_orders_count(self):
        self.job_orders_count = self.env['project.task'].search_count(
            domain=[('maintenance_request_id', '=', self.id)],
        )

    def action_open_job_orders(self):
        return {
            'name': _('Job Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'view_mode': 'list,form',
            'target': 'current',
            'domain': [('maintenance_request_id', '=', self.id)],
        }

    # Computing stock movements count
    @api.depends('job_details_line_ids.name')
    def _compute_stock_movements_count(self):
        self.stock_movements_count = self.env['stock.picking'].search_count(
            domain=[('origin', '=', self.name)],
        )

    def action_open_delivery_orders(self):
        return {
            'name': _('Delivery Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'target': 'current',
            'domain': [('origin', '=', self.name)],
        }

    # Computing vendor bills count
    @api.depends('expense_details_line_ids.name')
    def _compute_expense_details_count(self):
        self.expense_details_count = self.env['account.move'].search_count(
            domain=[('payment_reference', '=', self.name)],
        )

    def action_open_vendor_bills(self):
        return {
            'name': _('Vendor Bills'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'target': 'current',
            'domain': [('payment_reference', '=', self.name)],
        }

    def action_submit_new_request(self):
        for rec in self:
            rec.request_status = 'wait_for_approval'
            rec.stage_id = self.env['maintenance.stage'].search([('name', '=', 'Wait for Approval')], limit=1)
        template = self.env.ref('hr_equipment.email_template_maintenance_request_approval')
        template.send_mail(self.id)

    def action_approve_request(self):
        for rec in self:
            rec.request_status = 'approved'
            rec.stage_id = self.env['maintenance.stage'].search([('name', '=', 'Approved')], limit=1)
            rec.equipment_id.equipment_status = 'maintenance'
        template = self.env.ref('hr_equipment.email_template_maintenance_request_approved')
        template.send_mail(self.id)

    def action_confirm_request(self):
        for rec in self:
            rec.request_status = 'in_progress'
            rec.stage_id = self.env['maintenance.stage'].search([('name', '=', 'In Progress')], limit=1)

            # Check if the equipment_id is not set
            if rec.equipment_id:
                job_order = rec.env['project.task'].create({
                    'name': "Maintenance JOB " + rec.equipment_id.name,
                    'project_id': rec.project_id.id,
                    'maintenance_request_id': rec.id,
                })
            else:
                raise UserError("No equipment assigned to this maintenance request.")

            # Find the picking type for delivery orders (outgoing shipments)
            picking_type = rec.env['stock.picking.type'].search([
                ('code', '=', 'outgoing')
            ], limit=1)

            # Ensure that component lines exist
            if not rec.component_line_ids:
                raise UserError("No component lines found for this request.")

            # Accumulate stock moves for all component lines
            stock_moves = []
            for component_line in rec.component_line_ids:
                if not rec.location_id:
                    raise UserError("Source location is missing for one of the components.")

                # Create stock move lines for each component line
                stock_moves.append((0, 0, {
                    'product_id': component_line.product_id.id,
                    'name': component_line.product_id.name,
                    'product_uom_qty': component_line.quantity,
                    'location_id': rec.location_id.id,  # Source location
                    'location_dest_id': rec.location_dest_id.id,  # Destination location
                    'product_uom': component_line.uom_id.id,  # Unit of Measure of the product
                    'origin': rec.name,
                }))

            # Create a single delivery order with multiple stock moves
            delivery_order = rec.env['stock.picking'].create({
                'partner_id': rec.user_id.partner_id.id,  # Make sure the partner_id is valid
                'origin': rec.name,
                'picking_type_id': picking_type.id,
                'location_id': rec.location_id.id,  # Source location for the delivery order
                'location_dest_id': rec.location_dest_id.id,  # Destination location for the delivery order
                'move_ids': stock_moves,  # The list of stock moves created above
                'maintenance_request_id': rec.id,  # Set the link to maintenance request
            })

    def action_process_request(self):
        for rec in self:
            rec.request_status = 'repaired'
            rec.stage_id = self.env['maintenance.stage'].search([('name', '=', 'Repaired')], limit=1)
            rec.equipment_id.equipment_status = 'free'

    def action_equipment_scrap_request(self):
        for rec in self:
            rec.request_status = 'scrap'
            rec.stage_id = self.env['maintenance.stage'].search([('name', '=', 'Scrap')], limit=1)

            # Check if the equipment exists
            if rec.equipment_id:
                # Archive the equipment by setting the active field to False
                rec.equipment_id.active = False

    def action_create_invoice(self):
        for rec in self:
            # Update the request status and stage
            rec.request_status = 'invoiced'
            rec.stage_id = self.env['maintenance.stage'].search([('name', '=', 'Invoiced')], limit=1)

            # Prepare invoice lines from component lines
            invoice_lines = []
            for line in rec.component_line_ids:
                invoice_lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'quantity': line.quantity,
                    'price_unit': line.unit_price,
                    'name': line.product_id.display_name,
                    'tax_ids': [(6, 0, line.taxes_ids.ids)]
                }))

            # Create the vendor bill (account.move)
            vendor_bill = self.env['account.move'].create({
                'move_type': 'in_invoice',  # Vendor Bill
                'partner_id': rec.user_id.partner_id.id,
                'payment_reference': rec.name,
                'invoice_origin': rec.name,  # To track the origin of the invoice
                'invoice_date': fields.Date.today(),
                'currency_id': rec.currency_id.id,  # Set currency for the invoice
                'invoice_line_ids': invoice_lines,  # Add the prepared invoice lines
                'maintenance_request_id': rec.id,  # Link the invoice to the maintenance request
            })

    def action_cancel_request(self):
        for rec in self:
            rec.request_status = 'cancel'
            rec.stage_id = self.env['maintenance.stage'].search([('name', '=', 'Cancel')], limit=1)

    # Approve selected requests in tree view
    def action_approve_selected_maintenance_requests(self):
        for rec in self:
            if rec.request_status == 'wait_for_approval':
                rec.request_status = 'approved'
                rec.stage_id = self.env['maintenance.stage'].search([('name', '=', 'Approved')], limit=1)
                rec.equipment_id.equipment_status = 'maintenance'
                template = rec.env.ref('hr_equipment.email_template_maintenance_request_approved')
                template.send_mail(rec.id)
        return True