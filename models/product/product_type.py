# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ProductType(models.Model):
    _name = 'product.type'
    _description = 'Product Type'

    name = fields.Char(string='Product Type', required=True)


