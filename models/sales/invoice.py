# -*- coding: utf-8 -*-

# Workflow:
#         create --------> Draft
#           update: date, sale by, customer info, product lines
#
#         Draft---------->Paid
#           check product stock
#           Reduce stock if available
#           create journal entries in pharmacy ledger and tax ledger
#
#         Draft---------->cancel
#
#   sequence: INV/{Year}



from odoo import models, fields, api, _, exceptions
from datetime import datetime


PROGRESS_INFO = [('draft', 'Draft'), ('cancel', 'Cancel'), ('paid', 'Paid')]


class Invoice(models.Model):
    _name = 'sale.invoice'
    _description = 'Sales Invoice'

    sequence = fields.Char(string='Sequence', readonly=True)
    date = fields.Date(string='Date', readonly=True)
    sale_by = fields.Many2one(comodel_name='res.users', string='Finalised By', readonly=True)
    invoice_detail = fields.One2many(comodel_name='invoice.detail', inverse_name='invoice_id', string='Invoice detail')
    progress = fields.Selection(PROGRESS_INFO, string='Progress')
    customer_id = fields.Many2one(comodel_name='hospital.partner', string='Customer')
    customer_addresss = ''
    customer_contact = ''
    customer_email = ''

    cgst = fields.Float(string='CGST', readonly=True)
    sgst = fields.Float(string='SGST', readonly=True)
    igst = fields.Float(string='IGST', readonly=True)
    un_taxed_amount = fields.Float(string='Un Taxed Amount', readonly=True)
    tax_amount = fields.Float(string='Taxed Amount', readonly=True)
    discount = fields.Float(string='Discount', required=True)
    gross = fields.Float(string='Gross', readonly=True)
    net = fields.Float(string='Net', readonly=True)


class InvoiceDetail(models.Model):
    _name = 'invoice.detail'
    _description = 'Invoice Detail'

    item_id = fields.Many2one(comodel_name='product.product', string='Item', required=True)
    uom_id = fields.Many2one(comodel_name='product.uom', string='UOM', required=True)
    quantity = fields.Float(string='Quantity', required=True)
    unit_price = fields.Float(string='Unit Price', required=True)
    tax_id = fields.Many2one(comodel_name='product.uom', string='Tax', required=True)
    cgst = fields.Float(string='CGST', readonly=True)
    sgst = fields.Float(string='SGST', readonly=True)
    igst = fields.Float(string='IGST', readonly=True)
    un_taxed_amount = fields.Float(string='Un Taxed Amount', readonly=True)
    tax_amount = fields.Float(string='Taxed Amount', readonly=True)
    discount = fields.Float(string='Discount', required=True)
    total = fields.Float(string='Total', readonly=True)





