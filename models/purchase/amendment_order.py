# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions
from datetime import datetime
from purchase_calculation import PurchaseCalculation as PC


PROGRESS_INFO = [('draft', 'Draft'), ('dpo_raised', 'Direct PO Raised')]


class AmendmentOrder(models.Model):
    _name = 'amendment.order'
    _description = 'Direct Purchase Order'
    _rec_name = 'sequence'

    sequence = fields.Char(string='Sequence', readonly=True)
    date = fields.Date(string='Date', readonly=True)
    po_id = fields.Many2one(comodel_name='purchase.order',
                            domain=[('progress', '=', 'po_raised')],
                            string='Purchase Order',
                            required=True)
    apo_detail = fields.One2many(comodel_name='apo.detail', string='APO Detail', inverse_name='apo_id')
    finalised_by = fields.Many2one(comodel_name='res.users', string='Finalised By', readonly=True)
    progress = fields.Selection(PROGRESS_INFO, string='Progress', default='draft')

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
        recs = self.apo_detail

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

    def check_mr(self, res):
        mrs = self.env['material.receipt'].search([('po_id', '=', res)])

        if mrs:
            raise exceptions.ValidationError('Error! Material Receipt in progress')

    def check_apo_detail(self):
        total = 0
        recs = self.apo_detail

        for rec in recs:
            total = total + rec.total

        if not total:
            raise exceptions.ValidationError('Error! please check line items')

    def check_progress_access(self):
        group_list = []
        if self.progress in ['draft', False]:
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

        sequence = obj.next_by_code('amendment.order')
        period = self.env['period.period'].search([('progress', '=', 'open')])
        return '{0}/{1}'.format(sequence, period.name)

    def create_po(self):

        data = {
            'po_type': 'amendment_order',
            'date': self.po_id.date,
            'indent_id': self.po_id.indent_id.id,
            'qr_id': self.po_id.qr_id.id,
            'finalised_by': self.po_id.finalised_by.id,
        }

        po = self.env['purchase.order'].create(data)
        self.po_id.wrire({'amendment_id': self.po.id, 'progress': 'cancel'})

        recs = self.apo_detail
        for rec in recs:
            data = {
                'item_id': rec.item_id.id,
                'uom_id': rec.uom_id.id,
                'quantity': rec.quantity,
                'unit_price': rec.unit_price,
                'tax_id': rec.tax_id.id,
                'pf': rec.pf,
                'total': rec.total,
                'po_id': po.id,

            }
            po.po_detail.create(data)
        po.trigger_update()
        po.write({'progress': 'po_raised'})

    @api.multi
    def trigger_apo_raised(self):
        self.check_progress_access()
        self.trigger_update()
        self.check_apo_detail()
        self.write({'progress': 'apo_raised',
                    'finalised_by': self.env.user.id})

        self.create_po()

    @api.multi
    def unlink(self):
        self.check_progress_access()
        raise exceptions.ValidationError('Error! You are not authorised to delete this record')

    @api.multi
    def write(self, vals):
        self.check_progress_access()
        res = super(AmendmentOrder, self).write(vals)
        return res

    @api.model
    def create(self, vals):
        self.check_progress_access()
        self.check_mr(vals['po_id'])
        vals['date'] = datetime.now().strftime('%Y-%m-%d')
        vals['sequence'] = self.create_sequence()
        res = super(AmendmentOrder, self).create(vals)
        return res


class APODetail(models.Model):
    _name = 'apo.detail'
    _description = 'Amendment Order Details'

    item_id = fields.Many2one(comodel_name='product.product', string='Item', required=True)
    uom_id = fields.Many2one(comodel_name='product.uom', string='UOM', required=True)
    quantity = fields.Float(string='Quantity', required=True)
    unit_price = fields.Float(string='Unit Price', required=True)
    discount = fields.Float(string='Discount')
    discount_amount = fields.Float(string='Discount Amount', readonly=True)
    amt_after_discount = fields.Float(string='Amount After Discount', readonly=True)
    tax_id = fields.Many2one(comodel_name='product.tax', string='Tax', required=True)
    pf = fields.Float(string='Packing Forwarding', required=True)
    pf_amount = fields.Float(string='Packing Forwading Amount', readonly=True)
    cgst = fields.Float(string='CGST', readonly=True)
    sgst = fields.Float(string='SGST', readonly=True)
    igst = fields.Float(string='IGST', readonly=True)
    tax_amount = fields.Float(string='Tax Amount', readonly=True)
    taxed_amount = fields.Float(string='Taxed Amount', readonly=True)
    un_taxed_amount = fields.Float(string='Untaxed Amount', readonly=True)
    total = fields.Float(string='Total', readonly=True)
    apo_id = fields.Many2one(comodel_name='amendment.order', string='Amendment Order')
    progress = fields.Selection(PROGRESS_INFO, string='Progress', related='apo_id.progress')

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
        if self.progress in ['draft', False]:
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

    @api.multi
    def unlink(self):
        self.check_progress_access()
        raise exceptions.ValidationError('Error! You are not authorised to delete this record')

    @api.multi
    def write(self, vals):
        self.check_progress_access()
        res = super(APODetail, self).write(vals)
        return res

    @api.model
    def create(self, vals):
        self.check_progress_access()
        res = super(APODetail, self).create(vals)
        return res
