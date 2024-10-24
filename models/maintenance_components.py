from odoo import models, fields, api


class MaintenanceComponents(models.Model):
    _name = 'maintenance.components'
    _description = 'Maintenance Components'

    product_id = fields.Many2one(comodel_name='product.template', string='Product', required=True)
    quantity = fields.Float(string='Quantity', default=1)
    uom_id = fields.Many2one(comodel_name='uom.uom', string='Unit of Measure')
    unit_price = fields.Monetary(string='Unit Price', currency_field='currency_id')
    taxes_ids = fields.Many2many(comodel_name='account.tax', string='Tax')
    total_tax = fields.Monetary(string='Total Tax', compute='_compute_total_tax', store=True, currency_field='currency_id')
    subtotal = fields.Monetary(string='Subtotal', compute='_compute_subtotal', store=True, currency_field='currency_id')
    component_id = fields.Many2one(comodel_name='maintenance.request', string='Components')
    currency_id = fields.Many2one('res.currency', related='component_id.currency_id', store=True, readonly=True)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.uom_id = self.product_id.uom_id.id
            self.unit_price = self.product_id.list_price
            self.taxes_ids = self.product_id.taxes_id

    @api.depends('unit_price', 'quantity', 'taxes_ids')
    def _compute_total_tax(self):
        for line in self:
            if line.taxes_ids:
                taxes = line.taxes_ids.compute_all(
                    line.unit_price, line.currency_id, line.quantity, product=line.product_id
                )
                line.total_tax = sum(t['amount'] for t in taxes['taxes'])
            else:
                line.total_tax = 0.0

    @api.depends('unit_price', 'quantity', 'total_tax')
    def _compute_subtotal(self):
        for line in self:
            unit_price = line.unit_price or 0.0
            quantity = line.quantity or 0.0
            if line.taxes_ids:
                taxes = line.taxes_ids.compute_all(
                    unit_price, line.currency_id, quantity, product=line.product_id
                )
                line.subtotal = taxes['total_included']
            else:
                line.subtotal = unit_price * quantity
