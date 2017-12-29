# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions


class StockLocation(models.Model):
    _name = 'stock.location'
    _description = 'Stock Location'

    name = fields.Char(string='Location', required=True)
    code = fields.Char(string='Code', required=True)

    @api.multi
    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for record in self:
            name = '{1} - [{0}]'.format(record.name, record.code)
            result.append((record.id, name))
        return result

    @api.multi
    def write(self, vals):
        res = {}
        msg = '''Product is created based on this location so. Please contact administrator for editing this record'''
        recs = self.env['product.stock'].search([('location_id', '=', self.id)])
        if len(recs):
            raise exceptions.ValidationError(msg=msg)
        else:
            res = super(StockLocation, self).write(vals)
        return res

    @api.multi
    def unlink(self):
        msg = '''Product is created based on this location so. Please contact administrator for deleting this record'''
        recs = self.env['product.stock'].search([('location_id', '=', self.id)])
        if len(recs):
            raise exceptions.ValidationError(msg=msg)
        else:
            self.unlink()

