# -*- coding: utf-8 -*-

# Not a duplicate name
# Not a duplicate code
# Write and Delete prohibited after Product Creation (due to sequence)
# create, write, delete Permission restricted to user group
# Special Button for sale/ Purchase/ Stock
# All User have read permission on Product
# Stock for each location is created once product is confirmed

from odoo import models, fields, api, _, exceptions

PROGRESS_INFO = [('draft', 'Draft'), ('confirmed', 'Confirmed')]


class Product(models.Model):
    _name = 'product.product'
    _description = 'Product Master'

    group_id = fields.Many2one(comodel_name='product.group', string='Product Group', required=True)
    sub_group_id = fields.Many2one(comodel_name='product.sub.group', string='Product Sub Group', required=True)
    name = fields.Char(string='Product', required=True)
    code = fields.Char(string='Code', reaonly=True)
    uom_id = fields.Many2one(comodel_name='product.uom', string='Product UOM', required=True)
    progress = fields.Selection(PROGRESS_INFO, default='draft', string='Progress')
    active = fields.Boolean(string='Active', default=True)

    def get_sequence(self):
        obj = self.env['ir.sequence'].sudo()
        self.sequence_creation()

        sequence = obj.next_by_code('product.{0}.{1}'.format(self.group_id.code, self.sub_group_id.code))
        return '{0}'.format(sequence)

    def sequence_creation(self):
        obj = self.env['ir.sequence'].sudo()
        if not obj.search([('code', '=', 'product.{0}.{1}'.format(self.group_id.code, self.sub_group_id.code))]):
            seq = {
                'name': 'product.{0}.{1}'.format(self.group_id.code, self.sub_group_id.code),
                'implementation': 'standard',
                'code': 'product.{0}.{1}'.format(self.group_id.code, self.sub_group_id.code),
                'prefix': '{0}/{1}/'.format(self.group_id.code, self.sub_group_id.code),
                'padding': 4,
                'number_increment': 1,
                'use_date_range': False,
            }
            obj.create(seq)

    def create_product_stock(self):
        locations = self.env['stock.location'].search([('id', '>', 0)])

        stock_obj = self.env['product.stock']
        for location in locations:
            data = {
                'product_id': self.id,
                'group_id': self.group_id.id,
                'sub_group_id': self.sub_group_id.id,
                'location_id': location.id,
                'quantity': 0
            }
            stock_obj.create()

    # Button Action
    @api.multi
    def trigger_confirm(self):
        self.check_progress_access()
        data = {
            'progress': 'Confirmed',
            'code': self.get_sequence()
        }
        self.write(data)
        self.create_product_stock()

    # Special Button
    def get_sales_price(self):
        view_id = self.env['ir.model.data'].get_object_reference('project_indrajith', 'view_product_sales_tree')[1]
        return {
            'type': 'ir.actions.act_window',
            'name': 'Product Sales Price',
            'view_mode': 'tree',
            'view_type': 'tree,form',
            'view_id': view_id,
            'domain': [('product_id', '=', self.id)],
            'res_model': 'product.sales',
            'target': 'current',
        }

    def get_purchase_price(self):
        view_id = self.env['ir.model.data'].get_object_reference('project_indrajith', 'view_product_purchase_tree')[1]
        return {
            'type': 'ir.actions.act_window',
            'name': 'Product Purchase Price',
            'view_mode': 'tree',
            'view_type': 'tree,form',
            'view_id': view_id,
            'domain': [('product_id', '=', self.id)],
            'res_model': 'product.purchase',
            'target': 'current',
        }

    def get_stock_quantity(self):
        view_id = self.env['ir.model.data'].get_object_reference('project_indrajith', 'view_product_stock_tree')[1]
        return {
            'type': 'ir.actions.act_window',
            'name': 'Stock View',
            'view_mode': 'tree',
            'view_type': 'tree,form',
            'view_id': view_id,
            'domain': [('product_id', '=', self.id)],
            'res_model': 'product.stock',
            'target': 'current',
        }

    # Access Function
    def check_progress_access(self):
        if self.progress in ['draft', False]:
            group_list = ['Product Manager', 'Admin']
        elif self.progress == 'confirmed':
            group_list = []

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
            name = '[{0}] - {1}'.format(record.code, record.name)
            result.append((record.id, name))
        return result

    @api.multi
    def unlink(self):
        self.check_progress_access()
        raise exceptions.ValidationError('Error! You are not authorised to delete this record')

    @api.multi
    def write(self, vals):
        self.check_progress_access()
        res = super(Product, self).write(vals)
        return res

    @api.model
    def create(self, vals):
        self.check_progress_access()
        res = super(Product, self).create(vals)
        return res

    _sql_constraints = [
        ('duplicate_product_name', 'unique (name)', "Duplicate Product Name"),
    ]