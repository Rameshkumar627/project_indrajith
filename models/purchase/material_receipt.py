# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions
from datetime import datetime
from purchase_calculation import PurchaseCalculation as PC


PROGRESS_INFO = [('draft', 'Draft'), ('inspected', 'Inspected')]


class MaterialReceipt(models.Model):
    _name = 'material.receipt'
    _description = 'Material Receipt'
    _rec_name = 'sequence'

    sequence = fields.Char(string='Sequence', readonly=True)
    date = fields.Date(string='Date', readonly=True)
    indent_id = fields.Many2one(comodel_name='purchase.indent', string='Purchase Indent', readonly=True)
    qr_id = fields.Many2one(comodel_name='quotation.request', string='Quotation Request', readonly=True)
    po_id = fields.Many2one(comodel_name='purchase.order', string='Purchase Order', required=True)
    mr_detail = fields.One2many(comodel_name='mr.detail', string='MR Detail', inverse_name='mr_id')
    received_by = fields.Many2one(comodel_name='res.users', string='Received By', readonly=True)
    inspected_by = fields.Many2one(comodel_name='res.users', string='Inspected By', readonly=True)
    progress = fields.Selection(PROGRESS_INFO, string='Progress', default='draft')
    comment = fields.Text(string='Comment')

    grand_total = fields.Float(string='Grand Total', readonly=True)
    overall_discount = fields.Float(string='Overall Discount', default=0)
    discount_amount = fields.Float(string='Discount Amount', readonly=True)
    overall_pf = fields.Float(string='Overall Packing Forwarding', default=0)
    pf_amount = fields.Float(string='Packing Forwading Amount', readonly=True)
    igst = fields.Float(string='IGST', readonly=True)
    cgst = fields.Float(string='CGST', readonly=True)
    sgst = fields.Float(string='SGST', readonly=True)
    tax_amount = fields.Float(string='Tax Amount', readonly=True)
    taxed_amount = fields.Float(string='Taxed Amount', readonly=True)
    un_taxed_amount = fields.Float(string='Untaxed Amount', readonly=True)
    gross_amount = fields.Float(string='Gross Amount', readonly=True)
    round_off = fields.Float(string='Round-Off', readonly=True)
    net_amount = fields.Float(string='Net Amount', readonly=True)

    def check_existing_mr(self, vals):

        recs = self.env['material.receipt'].search([('po_id', '=', vals['po_id'])])
        if recs:
            raise exceptions.ValidationError('Error! Material Receipt for this PO is in progress')

    def product_stock_upgradation(self):
        recs = self.mr_detail

        for rec in recs:
            rec.product_stock_upgradation()

    def trigger_update(self):
        recs = self.mr_detail

        for rec in recs:
            rec.check_quantity()
            rec.trigger_update()

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

    def trigger_inspected(self):
        self.check_progress_access()
        self.trigger_update()
        self.product_stock_upgradation()
        self.write({'progress': 'inspected'})

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

        sequence = obj.next_by_code('material.receipt')
        period = self.env['period.period'].search([('progress', '=', 'open')])
        return '{0}/{1}'.format(sequence, period.name)

    def default_vals_update(self, vals):
        vals['date'] = datetime.now().strftime('%Y-%m-%d')
        vals['sequence'] = self.create_sequence()
        po = self.env['purchase.order'].search([('id', '=', vals['po_id'])])
        vals['qr_id'] = po.qr_id.id
        vals['indent_id'] = po.indent_id.id
        vals['received_by'] = self.env.user.id
        return vals

    def create_mr_detail(self, res):
        recs = self.env['po.detail'].search([('id', '=', res.po_id.id)])

        for rec in recs:
            data = {
                'item_id': rec.item_id.id,
                'uom_id': rec.uom_id.id,
                'mr_id': res.id,
                'requested_quantity': rec.quantity,
                'unit_price': rec.unit_price,
                'discount': rec.discount,
                'tax_id': rec.tax_id.id,
                'pf': rec.pf,
            }

            res.mr_detail.create(data)

    @api.multi
    def unlink(self):
        for rec in self:
            rec.check_progress_access()
            raise exceptions.ValidationError('Error! You are not authorised to delete this record')

    @api.multi
    def write(self, vals):
        self.check_progress_access()
        res = super(MaterialReceipt, self).write(vals)
        return res

    @api.model
    def create(self, vals):
        self.check_progress_access()
        self.check_existing_mr(vals)
        vals = self.default_vals_update(vals)
        res = super(MaterialReceipt, self).create(vals)
        self.create_mr_detail(res)
        return res


class MRDetail(models.Model):
    _name = 'mr.detail'
    _description = 'Material Receipt Details'

    item_id = fields.Many2one(comodel_name='product.product', string='Item', readonly=True)
    uom_id = fields.Many2one(comodel_name='product.uom', string='UOM', readonly=True)
    mr_id = fields.Many2one(comodel_name='material.receipt', string='Material Receipt')

    requested_quantity = fields.Float(string='Requested Quantity', default=0, readonly=True)
    received_quantity = fields.Float(string='Received Quantity', default=0)
    accepted_quantity = fields.Float(string='Accepted Quantity', default=0)
    balance_quantity = fields.Float(string='Balance Quantity', default=0, readonly=True)

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
    progress = fields.Char(string='Progress', compute='get_progress', store=False)

    def get_progress(self):
        for rec in self:
            rec.progress = rec.mr_id.progress

    def check_quantity(self):
        if self.requested_quantity > self.received_quantity:
            raise exceptions.ValidationError('Error! Requested qty is more than received qty')

        if self.received_quantity > self.accepted_quantity:
            raise exceptions.ValidationError('Error! Received qty is more than accepted qty')

        if self.accepted_quantity > self.requested_quantity:
            raise exceptions.ValidationError('Error! Accepted qty is more than requested qty')

        balance_quantity = self.received_quantity - self.accepted_quantity
        self.write({'balance_quantity': balance_quantity})

    def product_stock_upgradation(self):
        stock_obj = self.env['product.stock']
        store_stock = stock_obj.search([('product_id', '=', self.item_id.id),
                                        ('location_id.name', '=', 'Store'),
                                        ('uom_id', '=', self.uom_id.id)])

        # Stock Addition in requested location
        add_quantity = store_stock + self.accepted_quantity
        store_stock.write({'quantity': add_quantity})

    def trigger_update(self):
        price = self.accepted_quantity * self.unit_price

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
        for rec in self:
            rec.check_progress_access()
            raise exceptions.ValidationError('Error! You are not authorised to delete this record')

    @api.multi
    def write(self, vals):
        self.check_progress_access()
        res = super(MRDetail, self).write(vals)
        return res

    @api.model
    def create(self, vals):
        self.check_progress_access()
        res = super(MRDetail, self).create(vals)
        return res


