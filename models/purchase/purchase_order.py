# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions
from datetime import datetime
from purchase_calculation import PurchaseCalculation as PC


PROGRESS_INFO = [('po_raised', 'PO Raised'), ('cancel', 'Cancel')]
PO_TYPE = [('direct_po', 'Direct PO'), ('normal_po', 'Normal PO'), ('amendment_order', 'Amendment Order')]


class PurchaseOrder(models.Model):
    _name = 'purchase.order'
    _description = 'Purchase Order'
    _rec_name = 'sequence'

    sequence = fields.Char(string='Sequence', readonly=True)
    po_type = fields.Selection(PO_TYPE, string='PO Type', readonly=True)
    date = fields.Date(string='Date', readonly=True)
    indent_id = fields.Many2one(comodel_name='purchase.indent', string='Purchase Indent', readonly=True)
    qr_id = fields.Many2one(comodel_name='quotation.request', string='Quotation Request', readonly=True)
    vendor_id = fields.Many2one(comodel_name='hospital.partner', string='Vendor', readonly=True)
    amendment_id = fields.Many2one(comodel_name='purchase.order', string='Amendment Order', readonly=True)
    po_detail = fields.One2many(comodel_name='po.detail', string='PO Detail', inverse_name='po_id')
    finalised_by = fields.Many2one(comodel_name='res.users', string='Finalised By', readonly=True)
    progress = fields.Selection(PROGRESS_INFO, string='Progress')

    igst = fields.Float(string='IGST', readonly=True)
    cgst = fields.Float(string='CGST', readonly=True)
    sgst = fields.Float(string='SGST', readonly=True)
    tax_amount = fields.Float(string='Tax Amount', readonly=True)
    taxed_amount = fields.Float(string='Taxed amlunt', readonly=True)
    un_taxed_amount = fields.Float(string='Tax Amount', readonly=True)
    overall_discount = fields.Float(string='Discount', readonly=True)
    discount_amount = fields.Float(string='Discount Amount', readonly=True)
    overall_pf = fields.Float(string='Packing Forwarding', readonly=True)
    pf_amount = fields.Float(string='Packing Forwardingf Amount', readonly=True)
    grand_total = fields.Float(string='Grand Total', readonly=True)
    gross_amount = fields.Float(string='Gross Amount', readonly=True)
    round_off = fields.Float(string='Round Off', readonly=True)
    net_amount = fields.Float(string='Net Amount', readonly=True)

    comment = fields.Text(string='Comment')

    @api.multi
    def trigger_update(self):
        self.check_progress_access()
        recs = self.po_detail

        for rec in recs:
            rec.calculate_total()

        igst = cgst = sgst = 0
        tax_amount = taxed_amount = un_taxed_amount = 0
        pf_amount = discount_amount = 0
        total = 0
        for rec in recs:
            igst = igst + rec.igst
            cgst = cgst + rec.cgst
            sgst = sgst + rec.sgst
            tax_amount = tax_amount + rec.tax_amount
            taxed_amount = taxed_amount + rec.taxed_amount
            un_taxed_amount = un_taxed_amount + rec.un_taxed_amount
            pf_amount = pf_amount + rec.pf_amount
            discount_amount = discount_amount + rec.discount_amount
            total = total + rec.total
        pf_amount = pf_amount + self.overall_pf
        discount_amount = discount_amount + self.overall_discount
        gross_amount = total - self.overall_discount + self.overall_pf

        round_off = round(gross_amount, 2)

        data = {
            'igst': igst,
            'cgst': cgst,
            'sgst': sgst,
            'tax_amount': tax_amount,
            'taxed_amount': taxed_amount,
            'un_taxed_amount': un_taxed_amount,
            'pf_amount': pf_amount,
            'discount_amount': discount_amount,
            'grand_total': total,
            'round_off': gross_amount - round_off,
            'gross_amount': gross_amount,
            'net_amount': gross_amount + round_off,
        }
        self.write(data)

    def check_mr_cancellation(self):
        recs = self.env['material.receipt'].search([('po_id', '=', self.id)])
        if recs:
            raise exceptions.ValidationError('Error! Material receipt is generated you cannot cancel this record PO')

    def trigger_cancel(self):
        self.check_progress_access()
        self.check_mr_cancellation()
        self.write({'progress': 'cancel'})

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
    unit_price = fields.Float(string='Unit Price', readonly=True)
    discount = fields.Float(string='Discount')
    discount_amount = fields.Float(string='Discount Amount', readonly=True)
    amt_after_discount = fields.Float(string='Amount After Discount', readonly=True)
    tax_id = fields.Many2one(comodel_name='product.tax', string='Tax', readonly=True)
    pf = fields.Float(string='Packing Forwarding', readonly=True)
    pf_amount = fields.Float(string='Packing Forwading Amount', readonly=True)
    cgst = fields.Float(string='CGST', readonly=True)
    sgst = fields.Float(string='SGST', readonly=True)
    igst = fields.Float(string='IGST', readonly=True)
    tax_amount = fields.Float(string='Tax Amount', readonly=True)
    taxed_amount = fields.Float(string='Taxed Amount', readonly=True)
    un_taxed_amount = fields.Float(string='Untaxed Amount', readonly=True)
    total = fields.Float(string='Total', readonly=True)
    po_id = fields.Many2one(comodel_name='purchase.order', string='Purchase Order')
    progress = fields.Selection(PROGRESS_INFO, string='Progress', related='po_id.progress')

    def calculate_total(self):
        price = self.quantity * self.unit_price

        pc_obj = PC()
        discount_amount = pc_obj.calculate_percentage(price, self.discount)

        amt_after_discount = price - discount_amount
        igst, cgst, sgst = pc_obj.calculate_tax(amt_after_discount, self.tax_id.tax, self.tax_id.name)

        tax_amount = igst + cgst + sgst
        pf_amount = pc_obj.calculate_percentage(amt_after_discount, self.pf)

        total = amt_after_discount + tax_amount + pf_amount

        data = {'discount_amount': discount_amount,
                'amt_after_discount': amt_after_discount,
                'pf_amount': pf_amount,
                'igst': igst,
                'cgst': cgst,
                'sgst': sgst,
                'tax_amount': tax_amount,
                'taxed_amount': 0,
                'un_taxed_amount': 0,
                'total': total
                }

        self.write(data)

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

    @api.model
    def create(self, vals):
        self.check_progress_access()
        res = super(PODetail, self).create(vals)
        return res
