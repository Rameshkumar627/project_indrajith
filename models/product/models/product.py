# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

PROGRESS_INFO = [('draft', 'Draft'), ('confirmed', 'Confirmed')]


class Product(models.Model):
    _name = 'product.product'
    _description = 'Product Master'

    group_id = fields.Many2one(comodel_name='product.group', string='Product Group', required=True)
    sub_group_id = fields.Many2one(comodel_name='product.sub.group', string='Product Sub Group', required=True)
    name = fields.Char(string='Product', required=True)
    code = fields.Char(string='Code', reaonly=True)
    uom_id = fields.Many2one(comodel_name='product.uom', string='Product UOM', required=True)
    progress = fields.Selection(PROGRESS_INFO, default='draft', string='Progress')
    active = fields.Boolean(string='Active', default=True)

    sale_ids = fields.One2many(comodel_name='product.sales', inverse_name='product_id', string='Sales Detils')
    purchase_ids = fields.One2many(comodel_name='product.purchase', inverse_name='product_id', string='Purchase Details')
    stock_ids = fields.One2many(comodel_name='product.stock', inverse_name='product_id', string='Stock Details')

    @api.multi
    def trigger_approve(self):
        self.write({'progress': 'Confirmed'})

    @api.multi
    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for record in self:
            name = '{1} - [{0}]'.format(record.name, record.code)
            result.append((record.id, name))
        return result

    def check_purchase_transaction(self):
        return True

    def check_sales_transaction(self):
        return True

    @api.multi
    def write(self, vals):
        res = {}
        purchase = self.check_purchase_transaction()
        sales = self.check_sales_transaction()
        if purchase or sales:
            res = super(Product, self).write(vals)

        return res

    @api.multi
    def unlink(self):
        res = {}
        purchase = self.check_purchase_transaction()
        sales = self.check_sales_transaction()
        if purchase or sales:
            self.write({'active': False})
