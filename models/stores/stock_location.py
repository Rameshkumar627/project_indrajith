# -*- coding: utf-8 -*-

# No duplicate in name
# No duplicate in code
# Write and Delete prohibited after Product Stock Creation (due to sequence)
# create, write, delete Permission restricted to user group
# Any one can read the Stock Location
# Name includes both name & value

from odoo import models, fields, api, _, exceptions


class StockLocation(models.Model):
    _name = 'stock.location'
    _description = 'Stock Location'

    name = fields.Char(string='Location', required=True)
    code = fields.Char(string='Code', required=True)

    # Access Function
    def check_progress_access(self):
        group_list = ['Product Manager']
        outer_obj = self.env['check.group.access'].browse([('id', '=', 1)])
        if not outer_obj.check_group_access(group_list):
            raise exceptions.ValidationError('Error! You are not authorised to change this record')

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
        raise exceptions.ValidationError('Error! You are not authorised to change this record')

    @api.multi
    def write(self, vals):
        self.check_progress_access()
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

