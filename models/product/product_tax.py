# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ProductTax(models.Model):
    _name = 'product.tax'
    _description = 'Product Tax Master'

    name = fields.Char(string='Tax', required=True)
    code = fields.Char(string='Code', required=True)

    @api.multi
    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for record in self:
            name = '{1} - [{0}]'.format(record.name, record.code)
            result.append((record.id, name))
        return result
