# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class Product(models.Model):
    _name = 'product.product'
    _description = 'Product Master'

    product_group_id = fields.Many2one(comodel_name='product.group', string='Product Group', required=True)
    product_sub_group_id = fields.Many2one(comodel_name='product.sub.group', string='Product Sub Group', required=True)
    product_type_id = fields.Many2one(comodel_name='product.type', string='prduct Type', required=True)
    name = fields.Char(string='Product', required=True)
    code = fields.Char(string='Code', reaonly=True)

    sale_ids = fields.One2many(comodel_name='product.sales', inverse_name='product_id', string='Sales Detils')
    purchase_ids = fields.One2many(comodel_name='product.purchase', inverse_name='product_id', string='Purchase Details')

