# -*- coding: utf-8 -*-

# No Date-time overlap
# No Backdated record
# Update PSV Detail on button click
# All fields readonly except Actual Quantity
# Print Out
# Update Product Stock on button click
# Except fist time remaining all other time till_date is next record start date

from odoo import models, fields, api, _, exceptions


class PhysicalStockVerification(models.Model):
    _name = 'physical.stock.verification'
    _description = 'Physical Stock Verification'

    from_date = fields.Date(string='From Date', readonly=True)
    till_date = fields.Date(string='Till Date', required=True)
    sequence = fields.Char(string='Sequence', readonly=True)
    psv_detail = fields.One2many(comodel_name='psv.detail', string='PSV Detail')


class PSVDetail(models.Model):
    _name = 'psv.detail'
    _description = 'Physical Stock Verification Detail'

    product_id = fields.Many2one(comodel_name='product.product', string='Product', readonly=True)
    uom_id = fields.Many2one(comodel_name='product.uom', string='UOM', readonly=True)
    group_id = fields.Many2one(comodel_name='product.group', string='Product Group', related='product_id.group_id')
    sub_group_id = fields.Many2one(comodel_name='product.group', string='Product Sub Group',
                                   related='product_id.sub_group_id')
    location_id = fields.Many2one(comodel_name='stock.location', string='Location', readonly=True)
    available_quantity = fields.Float(string='Available Quantity', readonly=True)
    actual_quantity = fields.Float(string='Actual Quantity')
    comment = fields.Text(string='Comment')
    psv_id = fields.Many2one(comodel_name='physical.stock.verification',
                             string='Physical Stock Verification')

