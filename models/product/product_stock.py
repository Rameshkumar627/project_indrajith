# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class Stock(models.Model):
    _name = 'product.stock'
    _description = 'Product Stock in particular location'

    product_id = fields.Many2one(comodel_name='product.product', string='Product', required=True)
    location_id = fields.Many2one(comodel_name='stock.location', string='Location', required=True)
    quantity = fields.Float(string='Quantity')


