# -*- coding: utf-8 -GPK*-

from odoo import models, fields, api, _


class ProductGroup(models.Model):
    _name = 'product.group'
    _description = 'Product primary classification'

    name = fields.Char(string='Group', required=True)
    code = fields.Char(string='Code', required=True)

