# -*- coding: utf-8 -*-

# Can be a duplicate name
# Not a duplicate value
# Write and Delete prohibited after Product sales/Purchase Creation (due to sequence)
# create, write, delete Permission restricted to user group
# Any one can read the Product Tax
# Name includes both name & value

from odoo import models, fields, api, _, exceptions


class ProductTax(models.Model):
    _name = 'product.tax'
    _description = 'Product Tax Master'

    name = fields.Char(string='Name', required=True)
    tax = fields.Char(string='Tax', required=True)

    # Check Transaction for Tax
    def check_sales_transaction(self):
        pass

    def check_purchase_transaction(self):
        pass

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

    # Default Function
    @api.multi
    @api.depends('name', 'tax')
    def name_get(self):
        result = []
        for record in self:
            name = '{0} - {1}%'.format(record.name, record.tax)
            result.append((record.id, name))
        return result

    @api.multi
    def unlink(self):
        self.check_progress_access()
        self.check_sales_transaction()
        self.check_purchase_transaction()
        res = super(ProductTax, self).unlink()
        return res

    @api.multi
    def write(self, vals):
        self.check_progress_access()
        self.check_sales_transaction()
        self.check_purchase_transaction()
        res = super(ProductTax, self).write(vals)
        return res

    @api.model
    def create(self, vals):
        self.check_progress_access()
        res = super(ProductTax, self).create(vals)
        return res

    _sql_constraints = [
        ('duplicate_product_tax_value', 'unique (Tax)', "Duplicate Tax"),
    ]