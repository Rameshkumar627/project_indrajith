# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions
from datetime import datetime


PROGRESS_INFO = [('draft', 'Draft'),
                 ('qa', 'Quotation Approved'),
                 ('cancel', 'Cancel')]


class QuotationRequest(models.Model):
    _name = 'quotation.request'
    _description = 'Quaotation request raised by purchase department'

    sequence = fields.Char(string='Sequence', readonly=True)
    pi_id = fields.Many2one(comodel_name='purchase.indent', string='Purchase Indent', readonly=True)
    vendor_id = fields.Many2one(comodel_name='hospital.partner', string='Vendor', readonly=True)
    vs_id = fields.Many2one(comodel_name='vendor.selection', string='Vendor Selection', readonly=True)
    vendor_ref = fields.Char(string='Vendor Ref')
    processed_by = fields.Many2one(comodel_name='res.user', string='Processed By', readonly=True)
    processed_on = fields.Date(string='Processed On')
    request_detail = fields.One2many(comodel_name='vs.quote.detail', inverse_name='request_id', string='Request Detail')
    progress = fields.Selection(PROGRESS_INFO, default='draft', string='Progress')

    igst = fields.Float(string='IGST', readonly=True)
    cgst = fields.Float(string='CGST', readonly=True)
    sgst = fields.Float(string='SGST', readonly=True)
    tax_amount = fields.Float(string='Tax Amount', readonly=True)
    grand_total = fields.Float(string='Grand Total', readonly=True)
    gross_amount = fields.Float(string='Gross Amount', readonly=True)
    net_amount = fields.Float(string='Net Amount', readonly=True)
    others = fields.Float(string='Others')

    comment = fields.Text(string='Comment')

    @api.multi
    def trigger_update(self):
        pass

    def create_sequence(self):
        obj = self.env['ir.sequence'].sudo()
        self.department_sequence_creation()

        sequence = obj.next_by_code('quotation.request')
        period = self.env['period.period'].search([('progress', '=', 'open')])
        return '{0}/{1}'.format(sequence, period.name)

    def department_sequence_creation(self):
        obj = self.env['ir.sequence'].sudo()
        if not obj.search([('code', '=', 'quotation.request')]):
            seq = {
                'name': 'quotation.request',
                'implementation': 'standard',
                'code': 'quotation.request',
                'prefix': 'QRG/',
                'padding': 4,
                'number_increment': 1,
                'use_date_range': False,
            }
            obj.create(seq)

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
        res = super(QuotationRequest, self).create(vals)
        return res


