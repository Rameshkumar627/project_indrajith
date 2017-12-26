# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


PROGRESS_INFO = [('draft', 'Draft'), ('wha', 'Waiting For HOD'), ('weg', 'Waiting For Management'), ('cancel', 'Cancel')]

class PurchaseIndent(models.Model):
    _name = 'purchase.indent'
    _description = 'Purchase indent raised by user/department acceptation from management'

    date = fields.Date(string='Date', readonly=True)
    sequence = fields.Char(string='Sequence', readonly=True)
    raised_by = fields.Many2one(comodel_name='res.user', string='Raised By', readonly=True)
    raised_on = fields.Date(string='Raised On')
    approved_by = fields.Many2one(comodel_name='res.user', string='Approved By', readonly=True)
    approved_on = fields.Date(string='Approved On')
    progress = fields.Selection(PROGRESS_INFO, string='Progress', default=True, readonly=True )
    indent_detail = fields.One2many(comodel_name='purchase.indent.detail', inverse_name='indent_id', string='Indent Details')
    comment = fields.Text(string='Comment')


class PurchaseIndentDetail(models.Model):
    _name = 'purchase.indent.detail'
    _description = 'Purchase Indent Details'

    item_id = fields.Many2one(comodel_name='product.product', string='Item', required=True)
    uom_id = fields.Many2one(comodel_name='product.uom', string='UOM', required=True)
    req_qty = fields.Float(string='Requested Quantity', required=True)
    acc_qty = fields.Float(string='Approved Quantity')


