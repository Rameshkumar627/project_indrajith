# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions
from datetime import datetime


PROGRESS_INFO = [('po_raised', 'PO Raised'), ('cancel', 'Cancel')]
PO_TYPE = [('direct_po', 'Direct PO'), ('normal_po', 'Normal PO'), ('amendment_order', 'Amendment Order')]


class PurchaseOrder(models.Model):
    _name = 'purchase.order'
    _description = 'Purchase Order'

    sequence = fields.Char(string='Sequence', readonly=True)
    po_type = fields.Selection(PO_TYPE, string='PO Type', readonly=True)
    date = fields.Date(string='Date', readonly=True)
    indent_id = fields.Many2one(comodel_name='purchase.indent', string='Purchase Indent', readonly=True)
    qr_id = fields.Many2one(comodel_name='quotation.request', string='Quotation Request', readonly=True)
    po_detail = fields.One2many(comodel_name='po.detail', string='PO Detail', inverse_name='po_id')
    finalised_by = fields.Many2one(comodel_name='res.users', string='Finalised By', readonly=True)
    progress = fields.Selection(PROGRESS_INFO, string='Progress')

    igst = fields.Float(string='IGST', readonly=True)
    cgst = fields.Float(string='CGST', readonly=True)
    sgst = fields.Float(string='SGST', readonly=True)
    tax_amount = fields.Float(string='Tax Amount', readonly=True)
    grand_total = fields.Float(string='Grand Total', readonly=True)
    gross_amount = fields.Float(string='Gross Amount', readonly=True)
    net_amount = fields.Float(string='Net Amount', readonly=True)
    others = fields.Float(string='Others')

    comment = fields.Text(string='Comment')

    def trigger_cancel(self):
        self.check_progress_access()
        self.write({'progress': 'cancel'})

    def trigger_cancel(self):
        self.check_progress_access()
        self.write({'progress': 'po_raised'})

    def check_progress_access(self):
        group_list = []
        if self.progress in ['po_raised', False]:
            group_list = ['Hospital Management', 'Admin']

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

    def create_sequence(self):
        obj = self.env['ir.sequence'].sudo()

        sequence = obj.next_by_code('purchase.order')
        period = self.env['period.period'].search([('progress', '=', 'open')])
        return '{0}/{1}'.format(sequence, period.name)

    @api.multi
    def unlink(self):
        self.check_progress_access()
        raise exceptions.ValidationError('Error! You are not authorised to delete this record')

    @api.multi
    def write(self, vals):
        self.check_progress_access()
        res = super(PurchaseOrder, self).write(vals)
        return res

    @api.model
    def create(self, vals):
        self.check_progress_access()
        vals['date'] = datetime.now().strftime('%Y-%m-%d')
        vals['sequence'] = self.create_sequence()
        vals['finalised_by'] = self.env.user.id

        res = super(PurchaseOrder, self).create(vals)
        return res


class PODetail(models.Model):
    _name = 'po.detail'
    _description = 'Purchase Order Details'

    item_id = fields.Many2one(comodel_name='product.product', string='Item', readonly=True)
    uom_id = fields.Many2one(comodel_name='product.uom', string='UOM', readonly=True)
    quantity = fields.Float(string='Quantity', readonly=True)
    tax_id = fields.Many2one(comodel_name='product.tax', string='Tax', readonly=True)
    pf = fields.Float(string='Packing Forwarding', readonly=True)
    others = fields.Float(string='Others', readonly=True)
    total = fields.Float(string='Total', readonly=True)
    tax_amount = fields.Float(string='Tax Amount', readonly=True)
    po_id = fields.Many2one(comodel_name='purchase.order', string='Purchase Order')


