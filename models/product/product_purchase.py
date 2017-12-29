# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ProductPurchase(models.Model):
    _name = 'product.purchase'
    _description = 'Product Purchase Information'

    product_id = fields.Many2one(comodel='product.purchase', string='Product', readonly=True)
    vendor_id = fields.Many2one(comodel='hospital.partner', string='Vendor', readonly=True)
    po_ref = fields.Char(string='Purchase Order ref', readonly=True)
    date = fields.Date(string='Date', readonly=True)
    price = fields.Float(string='Price', readonly=True)
    
