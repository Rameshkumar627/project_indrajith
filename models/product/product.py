# -*- coding: utf-8 -*-

# Not a duplicate name
# Not a duplicate code
# Write and Delete prohibited after Product Creation (due to sequence)
# create, write, delete Permission restricted to user group
# Special Button for sale/ Purchase/ Stock
# All User have read permission on Product
# Stock for each location and UOM is created on button click(create_product_stock)

# Note Stock location: Store is hard coded

from odoo import models, fields, api, _, exceptions


class Product(models.Model):
    _name = 'product.product'
    _description = 'Product Master'

    group_id = fields.Many2one(comodel_name='product.group', string='Product Group', required=True)
    sub_group_id = fields.Many2one(comodel_name='product.sub.group', string='Product Sub Group', required=True)
    name = fields.Char(string='Product', required=True)
    code = fields.Char(string='Code', reaonly=True)
    uom_ids = fields.Many2many(comodel_name='product.uom', string='Product UOM', required=True)
    location_ids = fields.Many2many(comodel_name='stock.location', string='Stock Location', required=True)
    active = fields.Boolean(string='Active', default=True)

    def get_sequence(self, group_id, sub_group_id):
        obj = self.env['ir.sequence'].sudo()

        group = self.env['product.group'].search([('id', '=', group_id)])
        sub_group = self.env['product.sub.group'].search([('id', '=', sub_group_id)])

        self.sequence_creation(group, sub_group)

        sequence = obj.next_by_code('product.{0}.{1}'.format(group.code, sub_group.code))
        return '{0}'.format(sequence)

    def sequence_creation(self, group, sub_group):
        obj = self.env['ir.sequence'].sudo()
        if not obj.search([('code', '=', 'product.{0}.{1}'.format(group.code, sub_group.code))]):
            seq = {
                'name': 'product.{0}.{1}'.format(group.code, sub_group.code),
                'implementation': 'standard',
                'code': 'product.{0}.{1}'.format(group.code, sub_group.code),
                'prefix': '{0}/{1}/'.format(group.code, sub_group.code),
                'padding': 4,
                'number_increment': 1,
                'use_date_range': False,
            }
            obj.create(seq)

    @api.multi
    def create_product_stock(self):
        stock_obj = self.env['product.stock']
        recs = self.uom_ids

        for rec in recs:
            # Hard Code to create default stock in store
            stock_obj.create({
                'product_id': self.id,
                'uom_id': rec.id,
                'location_id': 3,
                'quantity': 0
            })

            for location in self.location_ids:
                record = stock_obj.search([('product_id', '=', self.id),
                                           ('uom_id', '=', rec.id),
                                           ('location_id', '=', location.id)])
                if not record:
                    data = {
                        'product_id': self.id,
                        'uom_id': rec.id,
                        'location_id': location.id,
                        'quantity': 0
                    }
                    stock_obj.create(data)

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

        # sequence creation
        vals['code'] = self.get_sequence(vals['group_id'], vals['sub_group_id'])

        res = super(Product, self).create(vals)
        return res

    _sql_constraints = [
        ('duplicate_product_name', 'unique (name)', "Duplicate Product Name"),
        ('duplicate_product_name', 'unique (code)', "Duplicate Product Code"),
    ]