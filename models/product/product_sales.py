# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions


class ProductSales(models.Model):
    _name = 'product.sales'
    _description = 'Product Price in certain time'

    product_id = fields.Many2one(comodel_name='product.product', string='Product', readonly=True)
    from_date = fields.Date(string='From Date', required=True)
    till_date = fields.Date(string='Till Date', required=True)
    price = fields.Float(string='Price', required=True)

    def check_date_on_creation(self):
        recs = self.env['product.sales'].search([('product_id', '=', self.product_id)])

        if self.till_date < self.from_date:
            return True

        for rec in recs:
            if rec.from_date < self.from_date < rec.till_date:
                return True

            if rec.from_date < self.till_date < rec.till_date:
                return True

    @api.model
    def create(self, vals):
        rec = self.check_date_on_creation()
        if rec:
            raise exceptions.ValidationError('Please check the dates; Date mismatch')



