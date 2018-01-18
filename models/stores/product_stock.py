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
        outer_obj = self.env['check.group.access'].browse([('id', '=', 1)])
        if not outer_obj.check_group_access(group_list):
            raise exceptions.ValidationError('Error! You are not authorised to change this record')

    def stock_move(self, product, uom, from_location, to_location, qty):
        product_obj = self.env['product.product'].sudo()
        stock_obj = self.env['product.stock'].sudo()

        if not product_obj.search([('uom_ids', '=', uom.id), ('id', '=', product.id)]):
            raise exceptions.ValidationError('Product UOM not match')

        from_stock_obj = stock_obj.search([('product_id', '=', product.id),
                                           ('location_id', '=', from_location.id),
                                           ('uom_id', '=', uom.id)])

        if not from_stock_obj:
            from_stock_obj = stock_obj.create({'product_id': product.id,
                                               'uom_id': uom.id,
                                               'location_id': from_location.id})

        to_location_obj = stock_obj.search([('product_id', '=', product.id),
                                            ('location_id', '=', to_location.id),
                                            ('uom_id', '=', uom.id)])

        if not to_location_obj:
            to_location_obj = stock_obj.create({'product_id': product.id,
                                                'uom_id': uom.id,
                                                'location_id': to_location.id})

        # Quantity:
        reduce_qty = from_stock_obj.quantity - qty

        if reduce_qty < 0:
            raise exceptions.ValidationError('Error! Quantity is not sufficient to move')
        else:
            from_stock_obj.write({'quantity': from_stock_obj.quantity - qty})
            to_location_obj.write({'quantity': to_location_obj.quantity + qty})

    @api.multi
    def unlink(self):
        raise exceptions.ValidationError('Error! You are not authorised to delete this record')

    @api.model
    def create(self, vals):
        self.check_progress_access()
        res = super(Stock, self).create(vals)
        return res
