# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


PROGRESS_INFO = [('draft', 'Draft'), ('confirmed', 'Confirmed'), ('cancel', 'Cancel')]


class QuotationRequest(models.Model):
    _name = 'quotation.request'
    _description = 'Quaotation request raised by purchase department'

    date = fields.Date(string='Date', reaonly=True)
    sequence = fields.Char(string='Sequence', readonly=True)
    pi_ref = fields.Many2one(comodel_name='purchase.indent', string='Purchase Indent', readonly=True)
    vendor_id = fields.Many2one(comodel_name='hospital.partner', string='Vendor', readonly=True)
    vendor_ref = fields.Char(string='Vendor Ref')
    progress = fields.Selection(PROGRESS_INFO, string='Progress')
    processed_by = fields.Many2one(comodel_name='res.user', string='Processed By', readonly=True)
    processed_on = fields.Date(string='Processed On')
    request_detail = fields.One2many(comodel_name='qr.detail', inverse_name='request_id', string='Request Detail')
    comment = fields.Text(string='Comment')


class QRDetail(models.Model):
    _name = 'qr.detail'
    _description = 'Quoataion request items in detail'

    item_id = fields.Many2one(comodel_name='product.product', string='Product', readonly=True)
    uom_id = fields.Many2one(comodel_name='product.uom', string='UOM', readonly=True)
    quantity = fields.Float(string='Quantity', readonly=True)
    tax_id = fields.Many2one(comodel_name='product.tax', string='Tax')
    pf = fields.Float(string='Packing & Forwarding')
    tax_amount = fields.Float(string='Tax Amount')
    amount = fields.Float(string='Amount')
    request_id = fields.Many2one(comodel_name='quotation.request', string='Quotation Request')


