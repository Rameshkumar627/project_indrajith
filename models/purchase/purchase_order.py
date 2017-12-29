# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions
from datetime import datetime


PROGRESS_INFO = [('draft', 'Draft'), ('finalised', 'Finalised'), ('cancel', 'Cancel')]
PO_TYPE = [('direct_po', 'Direct PO'), ('normal_po', 'Normal PO'), ('amendment_order', 'Amendment Order')]


class PurchaseOrder(models.Model):
    _name = 'purchase.order'
    _description = 'Purchase Order'

    sequence = fields.Char(string='Sequence', readonly=True)
    po_type = fields.Selection(PO_TYPE, string='PO Type')
    date = fields.Date(string='Date', readonly=True)
    indent_id = fields.Many2one(comodel_name='purchase.indent', string='Purchase Indent')
    qr_id = fields.Many2one(comodel_name='quotation.request', string='Quotation Request')
    po_detail = fields.One2many(comodel_name='po.detail', string='PO Detail', inverse_name='po_id')
    finalised_by = fields.Many2one(comodel_name='res.users', string='Finalised By', readonly=True)
    finalised_on = fields.Date(string='Finalised On', readonly=True)
    comment = fields.Text(string='Comment')

    def create_sequence(self):
        obj = self.env['ir.sequence'].sudo()
        self.department_sequence_creation()

        sequence = obj.next_by_code('purchase.order')
        period = self.env['period.period'].search([('progress', '=', 'open')])
        return '{0}/{1}'.format(sequence, period.name)

    def department_sequence_creation(self):
        obj = self.env['ir.sequence'].sudo()
        if not obj.search([('code', '=', 'purchase.order')]):
            seq = {
                'name': 'Purchase Order',
                'implementation': 'standard',
                'code': 'purchase.order',
                'prefix': 'PO/',
                'padding': 4,
                'number_increment': 1,
                'use_date_range': False,
            }
            obj.create(seq)

    def default_vals_update(self, vals):
        vals['date'] = datetime.now().strftime('%Y-%m-%d')
        vals['sequence'] = self.create_sequence()
        return vals

    @api.model
    def create(self, vals):
        self.check_progress_access()
        vals = self.default_vals_update(vals)
        res = super(PurchaseOrder, self).create(vals)
        return res


class PODetail(models.Model):
    _name = 'po.detail'
    _description = 'Purchase Order Details'

    item_id = fields.Many2one(comodel_name='product.product', string='Item')
    uom_id = fields.Many2one(comodel_name='product.uom', string='UOM')
    quantity = fields.Float(string='Quantity')
    tax_id = fields.Many2one(comodel_name='product.tax', string='Tax')
    pf = fields.Float(string='Packing Forwarding')
    others = fields.Float(string='Others')
    total = fields.Float(string='Total')
    po_id = fields.Many2one(comodel_name='purchase.order', string='Purchase Order')


