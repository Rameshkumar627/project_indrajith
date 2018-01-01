# -*- coding: utf-8 -*-

# Stock must be readonly
# No duplicate of product_id and location_id
# On creation check access

from odoo import models, fields, api, _, exceptions


class Stock(models.Model):
    _name = 'product.stock'
    _description = 'Product Stock in particular location'

    product_id = fields.Many2one(comodel_name='product.product', string='Product', readonly=True)
    uom_id = fields.Many2one(comodel_name='product.uom', string='UOM', readonly=True)
    group_id = fields.Many2one(comodel_name='product.group', string='Product Group', related='product_id.group_id')
    sub_group_id = fields.Many2one(comodel_name='product.sub.group', string='Product Sub Group',
                                   related='product_id.sub_group_id')
    location_id = fields.Many2one(comodel_name='stock.location', string='Location', readonly=True)
    quantity = fields.Float(string='Quantity', readonly=True)

    _sql_constraints = [
        ('duplicate_product_stock', 'unique (product_id, uom_id, location_id)', "Duplicate Product Stock"),
    ]

    # Access Function
    def check_progress_access(self):
        group_list = ['Product Manager']
        if not self.check_group_access(group_list):
            raise exceptions.ValidationError('Error! You are not authorised to change this record')

    def check_group_access(self, group_list):
        ''' Check if current user in the group list return True'''
        group_ids = self.env.user.groups_id
        status = False
        for group in group_ids:
            if group.name in group_list:
                status = True
        return status

    @api.multi
    def unlink(self):
        raise exceptions.ValidationError('Error! You are not authorised to delete this record')

    @api.model
    def create(self, vals):
        self.check_progress_access()
        res = super(Stock, self).create(vals)
        return res
