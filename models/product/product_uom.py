# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ProductUOM(models.Model):
    _name = 'product.uom'
    _description = 'Product UOM'

    name = fields.Char(string='UOM', required=True)
    code = fields.Char(string='Code', required=True)


