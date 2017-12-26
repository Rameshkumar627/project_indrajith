# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ProductSubGroup(models.Model):
    _name = 'product.sub.group'
    _description = 'Product secondary classification based on Primary'

    group_id = fields.Many2one(comodel_name='product.group', string='Group', required=True)
    name = fields.Char(string='Sub Group', required=True)
    code = fields.Char(string='Sub Group Code', required=True)


