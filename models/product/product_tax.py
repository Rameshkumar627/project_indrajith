# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ProductTax(models.Model):
    _name = 'product.tax'
    _description = 'Product Tax Master'

    name = fields.Char(string='Tax', required=True)
    code = fields.Char(string='Code', required=True)

