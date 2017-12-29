# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions


class ProductSubGroup(models.Model):
    _name = 'product.sub.group'
    _description = 'Product secondary classification based on Primary'

    group_id = fields.Many2one(comodel_name='product.group', string='Group', required=True)
    name = fields.Char(string='Sub Group', required=True)
    code = fields.Char(string='Sub Group Code', required=True)

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
        recs = self.env['product.product'].search([('sub_group_id', '=', self.id)])
        if len(recs):
            raise exceptions.ValidationError(msg=msg)
        else:
            res = super(ProductSubGroup, self).write(vals)
        return res

    @api.multi
    def unlink(self):
        msg = '''Product is created based on this group so. Please contact administrator for deleting this record'''
        recs = self.env['product.product'].search([('sub_group_id', '=', self.id)])
        if len(recs):
            raise exceptions.ValidationError(msg=msg)
        else:
            self.unlink()
