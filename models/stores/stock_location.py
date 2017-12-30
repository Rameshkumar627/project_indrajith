# -*- coding: utf-8 -*-

# No duplicate in name
# No duplicate in code
# Write and Delete prohibited after Product Stock Creation (due to sequence)
# create, write, delete Permission restricted to user group
# Any one can read the Stock Location
# Name includes both name & value
# On Button click for all product stock location is generated

from odoo import models, fields, api, _, exceptions


class StockLocation(models.Model):
    _name = 'stock.location'
    _description = 'Stock Location'

    name = fields.Char(string='Location', required=True)
    code = fields.Char(string='Code', required=True)

    def check_stock_location(self):
        recs = self.env['product.stock'].search([('location_id', '=', self.id)])

        if recs:
            raise exceptions.ValidationError('Error! You are not authorised to change this record')

    # Button Function
    @api.multi
    def product_stock_location_updation(self):
        ''' Update stock location for each product '''
        products = self.env['product.product'].search([('id', '>', 0)])

        product_stock_obj = self.env['product.stock']
        for product in products:
            rec = product_stock_obj.search([('location_id', '=', self.id), ('product_id', '=', product.id)])
            if not rec:
                data = {
                    'product_id': product.id,
                    'location_id': self.id,
                    'quantity': 0,
                }
                product_stock_obj.create(data)

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
        self.check_stock_location()
        raise exceptions.ValidationError('Error! You are not authorised to change this record')
        return res

    @api.multi
    def write(self, vals):
        self.check_progress_access()
        self.check_stock_location()
        res = super(StockLocation, self).write(vals)
        return res

    @api.model
    def create(self, vals):
        self.check_progress_access()
        res = super(StockLocation, self).create(vals)
        return res

    _sql_constraints = [
        ('duplicate_stock_location_name', 'unique (name)', "Duplicate Stock Location Name"),
        ('duplicate_stock_location_code', 'unique (code)', "Duplicate Stock Location Code"),
    ]

