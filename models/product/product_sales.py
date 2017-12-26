# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ProductSales(models,Model):
    _name = 'product.sales'
    _description = 'Product Price in certain time'

    product_id = fields.Many2one(comodel_name='product.product', string='Product', readonly=True)
    from_date = fields.Date(string='From Date', required=True)
    till_date = fields.Date(string='Till Date', required=True)
    price = fields.Float(string='Price', required=True)

    def check_date_on_creation(self):
        pass


