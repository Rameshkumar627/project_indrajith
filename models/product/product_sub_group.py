# -*- coding: utf-8 -*-

# Can be a duplicate of name
# Not a duplicate of code
# create, write, delete Permission restricted to user group
# Any one can read the Product Sub-Group
# Name includes both name & code

from odoo import models, fields, api, _, exceptions


class ProductSubGroup(models.Model):
    _name = 'product.sub.group'
    _description = 'Product secondary classification based on Primary'

    group_id = fields.Many2one(comodel_name='product.group', string='Group', required=True)
    name = fields.Char(string='Sub Group', required=True)
    code = fields.Char(string='Sub Group Code', required=True)

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
    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for record in self:
            name = '{1} - [{0}]'.format(record.name, record.code)
            result.append((record.id, name))
        return result

    @api.multi
    def unlink(self):
        self.check_progress_access()
        msg = '''Product is created based on this group so. Please contact administrator for deleting this record'''
        recs = self.env['product.product'].search([('sub_group_id', '=', self.id)])
        if len(recs):
            raise exceptions.ValidationError(msg=msg)
        else:
            self.unlink()

    @api.multi
    def write(self, vals):
        self.check_progress_access()
        res = {}
        msg = '''Product is created based on this group so. Please contact administrator for editing this record'''
        recs = self.env['product.product'].search([('sub_group_id', '=', self.id)])
        if len(recs):
            raise exceptions.ValidationError(msg=msg)
        else:
            res = super(ProductSubGroup, self).write(vals)
        return res

    @api.model
    def create(self, vals):
        self.check_progress_access()
        res = super(ProductSubGroup, self).create(vals)
        return res

    _sql_constraints = [
        ('duplicate_product_sub_group_code', 'unique (code)', "Duplicate Product Sub Group Code"),
    ]