# -*- coding: utf-8 -GPK*-

# Not a duplicate
# Write and Delete prohibited after Product Creation (due to sequence)
# create, write, delete Permission restricted to user group
# Any one can read the Product Group
# Name includes both name & code

from odoo import models, fields, api, _, exceptions


class ProductGroup(models.Model):
    _name = 'product.group'
    _description = 'Product primary classification'

    name = fields.Char(string='Group', required=True)
    code = fields.Char(string='Code', required=True)

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

    # Default Functions
    @api.multi
    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for record in self:
            name = '[{0}] - {1}'.format(record.code, record.name)
            result.append((record.id, name))
        return result

    @api.multi
    def unlink(self):
        self.check_progress_access()
        msg = '''Product is created based on this group so. Please contact administrator for deleting this record'''
        recs = self.env['product.product'].search([('group_id', '=', self.id)])
        if len(recs):
            raise exceptions.ValidationError(msg=msg)
        else:
            res = super(ProductGroup, self).unlink()

    @api.multi
    def write(self, vals):
        self.check_progress_access()
        res = {}
        msg = '''Product is created based on this group so. Please contact administrator for editing this record'''
        recs = self.env['product.product'].search([('group_id', '=', self.id)])
        if len(recs):
            raise exceptions.ValidationError(msg=msg)
        else:
            res = super(ProductGroup, self).write(vals)
        return res

    @api.model
    def create(self, vals):
        self.check_progress_access()
        res = super(ProductGroup, self).create(vals)
        return res

    _sql_constraints = [
        ('duplicate_product_group_name', 'unique (name)', "Duplicate Product Group Name"),
        ('duplicate_product_group_code', 'unique (code)', "Duplicate Product Group Code"),
    ]