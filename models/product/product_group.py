# -*- coding: utf-8 -GPK*-

from odoo import models, fields, api, _, exceptions


class ProductGroup(models.Model):
    _name = 'product.group'
    _description = 'Product primary classification'

    name = fields.Char(string='Group', required=True)
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
        msg = '''Product is created based on this group so. Please contact administrator for editing this record'''
        recs = self.env['product.product'].search([('group_id', '=', self.id)])
        if len(recs):
            raise exceptions.ValidationError(msg=msg)
        else:
            res = super(ProductGroup, self).write(vals)
        return res

    @api.multi
    def unlink(self):
        msg = '''Product is created based on this group so. Please contact administrator for deleting this record'''
        recs = self.env['product.product'].search([('group_id', '=', self.id)])
        if len(recs):
            raise exceptions.ValidationError(msg=msg)
        else:
            self.unlink()

