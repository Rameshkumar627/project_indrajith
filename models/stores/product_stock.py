# -*- coding: utf-8 -*-

# Stock must be readonly
# No duplicate of product_id and location_id


from odoo import models, fields, api, _


class Stock(models.Model):
    _name = 'product.stock'
    _description = 'Product Stock in particular location'

    product_id = fields.Many2one(comodel_name='product.product', string='Product', readonly=True)
    uom_id = fields.Many2one(comodel_name='product.uom', string='UOM', related='product_id.uom_id')
    group_id = fields.Many2one(comodel_name='product.group', string='Product Group', related='product_id.group_id')
    sub_group_id = fields.Many2one(comodel_name='product.group', string='Product Sub Group',
                                   related='product_id.sub_group_id')
    location_id = fields.Many2one(comodel_name='stock.location', string='Location', readonly=True)
    quantity = fields.Float(string='Quantity', readonly=True)

    _sql_constraints = [
        ('duplicate_product_stock', 'unique (product_id, location_id)', "Duplicate Product Stock"),
    ]
