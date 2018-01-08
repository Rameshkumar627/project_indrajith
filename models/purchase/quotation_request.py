# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions
from datetime import datetime


# Worlflow: (No buttons in Quotation request all are in Vendor selection form)
#   create-------------> Draft
#       update: processed by, processed on, sequence and product detail
#
#   Draft--------------> QA
#       call from vendor selection
#       call trigger update 
#       
#   Draft-------------> Cancel
#
# Button:
#   trigger_update: all calculation in quotation request


PROGRESS_INFO = [('draft', 'Draft'),
                 ('qa', 'Quotation Approved'),
                 ('cancel', 'Cancel')]


class QuotationRequest(models.Model):
    _name = 'quotation.request'
    _description = 'Quotation request raised by purchase department'
    _rec_name = 'sequence'

    sequence = fields.Char(string='Sequence', readonly=True)
    pi_id = fields.Many2one(comodel_name='purchase.indent', string='Purchase Indent', readonly=True)
    vs_id = fields.Many2one(comodel_name='vendor.selection', string='Vendor Selection', readonly=True)
    vendor_id = fields.Many2one(comodel_name='hospital.partner', string='Vendor', readonly=True)
    vendor_ref = fields.Char(string='Vendor Ref')
    processed_by = fields.Many2one(comodel_name='res.user', string='Processed By', readonly=True)
    processed_on = fields.Date(string='Processed On', readonly=True)
    request_detail = fields.One2many(comodel_name='vs.quote.detail', inverse_name='request_id', string='Request Detail')
    progress = fields.Selection(PROGRESS_INFO, default='draft', string='Progress')

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

    comment = fields.Text(string='Comment')

    @api.multi
    def trigger_update(self):
        self.check_progress_access()
        recs = self.request_detail

        for rec in recs:
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
        print recs
        self.write(data)

    def create_sequence(self):
        obj = self.env['ir.sequence'].sudo()

        sequence = obj.next_by_code('quotation.request')
        period = self.env['period.period'].search([('progress', '=', 'open')])
        return '{0}/{1}'.format(sequence, period.name)

    def check_progress_access(self):
        group_list = ['procurement User']
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
        raise exceptions.ValidationError('Error! You are not authorised to delete record')

    @api.multi
    def write(self, vals):
        self.check_progress_access()
        res = super(QuotationRequest, self).write(vals)
        return res

    @api.model
    def create(self, vals):
        self.check_progress_access()
        vals['sequence'] = self.create_sequence()
        vals['progress'] = 'draft'
        vals['processed_on'] = datetime.now().strftime('%Y-%m-%d')
        vals['processed_by'] = self.env.user.id
        res = super(QuotationRequest, self).create(vals)
        return res


