# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class Stock(models.Model):
    _name = 'product.stock'
    _description = 'Product Stock in particular location'

    product_id = fields.Many2one(comodel_name='product.product', string='Product', required=True)
    uom_id = fields.Many2one(comodel_name='product.uom', string='UOM', related='product_id.uom_id')
    group_id = fields.Many2one(comodel_name='product.group', string='Product Group', related='product_id.group_id')
    sub_group_id = fields.Many2one(comodel_name='product.group', string='Product Sub Group',
                                   related='product_id.sub_group_id')
    location_id = fields.Many2one(comodel_name='stock.location', string='Location', required=True)
    quantity = fields.Float(string='Quantity')


