# -*- coding: utf-8 -*-

# On creation create vendor selection detail based on indent (qty > 0)
# On generate_quote create quote request based on vendor_ids, no delete of vendor_ids
#     1. check qr_detail by vendor_select_id, pi_id,
# On unlink no unlink
# create, write, unlink needs access rights
#

from odoo import models, fields, api, _, exceptions
from datetime import datetime


PROGRESS_INFO = [('draft', 'Draft'),
                 ('qa', 'Quotation Approved'),
                 ('cancel', 'Cancel')]


class VendorSelection(models.Model):
    _name = 'vendor.selection'
    _description = 'Vendor selection by procurement team'

    date = fields.Date(string='Date', readonly=True)
    indent_id = fields.Many2one(comodel_name='purchase.indent', string='Purchase Indent', required=True)
    progress = fields.Selection(PROGRESS_INFO, default='draft', string='Progress')
    selection_detail = fields.One2many(comodel_name='vs.detail',
                                       inverse_name='selection_id', string='Vendor Selection Details')
    comment = fields.Text(string='Comment')

    def create_quotation_request(self):
        ''' Get all vendors list
            Check quotation request for each vendor available if not create quotation request'''

        vendors_list = []
        recs = self.selection_detail
        for rec in recs:
            for record in rec.quote_detail:
                if record.vendor_id.id not in vendors_list:
                    vendors_list.append(record.vendor_id.id)

        for vendor in vendors_list:
            qr = self.env['quotation.request'].search([('vendor_id', '=', vendor),
                                                       ('vs_id', '=', self.id)])

            if not qr:
                data = {
                    'pi_ref': self.indent_id.id,
                    'vendor_id': vendor,
                    'vs_id': self.id,
                }
                self.env['quotation.request'].create(data)

    def create_qr_detail(self):
        ''' Get all product list
            Check quotation request detail for each vendor available if not create quotation request detail'''

        vs_recs = self.env['vs.quote.detail'].search([('vs_quote_id.selection_id', '=', self.id)])

        for vs_rec in vs_recs:
            qr = self.env['quotation.request'].search([('vendor_id', '=', vs_rec.vendor_id.id),
                                                       ('vs_id', '=', self.id)])
            if len(qr) == 1:
                vs_rec.write({'request_id': qr.id})
            else:
                raise exceptions.ValidationError('Error!')

    # Button Action
    @api.multi
    def generate_quote(self):
        recs = self.selection_detail

        for rec in recs:
            for vendor in rec.vendor_ids:

                # For each vendor check vs_quote_detail (create if not available)
                vs_quotes = self.env['vs.quote.detail'].search([('vs_quote_id', '=', rec.id),
                                                                ('vendor_id', '=', vendor.id)])

                if not vs_quotes:
                    data = {
                        'vs_quote_id': rec.id,
                        'vendor_id': vendor.id,
                        'quantity': rec.quantity,
                    }
                    self.env['vs.quote.detail'].create(data)

        # create quotation request based on vs_quote_detail
        self.create_quotation_request()
        self.create_qr_detail()

    @api.multi
    def quote_approved(self):
        pass

    def check_progress_access(self):
        group_list = []
        if self.progress in ['draft', False]:
            group_list = ['Hospital Purchase', 'Admin']
        elif self.progress == 'qa':
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

    def create_vs_detail(self, res):
        pi_recs = self.env['pi.detail'].search([('indent_id', '=', res.indent_id.id),
                                                ('acc_qty', '>', 0)])

        for rec in pi_recs:
            data = {
                'item_id': rec.item_id.id,
                'uom_id': rec.uom_id.id,
                'quantity': rec.acc_qty,
                'selection_id': res.id,
            }

            self.env['vs.detail'].create(data)

    @api.multi
    def unlink(self):
        raise exceptions.ValidationError('Error! You are not authorised to delete record')

    @api.multi
    def write(self, vals):
        self.check_progress_access()
        res = super(VendorSelection, self).write(vals)
        return res

    @api.model
    def create(self, vals):
        self.check_progress_access()
        vals['date'] = datetime.now().strftime('%Y-%m-%d')
        res = super(VendorSelection, self).create(vals)
        self.create_vs_detail(res)
        return res


class VSDetail(models.Model):
    _name = 'vs.detail'
    _description = 'Vendor Selection Details'

    item_id = fields.Many2one(comodel_name='product.product', string='Item', required=True)
    uom_id = fields.Many2one(comodel_name='product.uom', string='UOM', required=True)
    quantity = fields.Float(string='Quantity', required=True)
    vendor_ids = fields.Many2many(comodel_name='hospital.partner', string='Vendors')
    quote_detail = fields.One2many(comodel_name='vs.quote.detail', inverse_name='vs_quote_id',
                                   string='Quote Detail')
    comment = fields.Text(string='Comment')
    selection_id = fields.Many2one(comodel_name='vendor.selection', string='Vendor Selection')


class VSQuoteDetail(models.Model):
    _name = 'vs.quote.detail'
    _description = 'Vendor Selection Quote Detail'

    quote_ref = fields.Char(string='Quotation', readonly=True)
    vendor_id = fields.Many2one(comodel_name='hospital.partner', string='Vendor', readonly=True)
    quantity = fields.Float(string='Quantity')
    item_id = fields.Many2one(comodel_name='product.product', string='Product', related='vs_quote_id.item_id')
    uom_id = fields.Many2one(comodel_name='product.uom', string='UOM', related='vs_quote_id.uom_id')
    tax_id = fields.Many2one(comodel_name='product.tax', string='Tax', readonly=True)
    pf = fields.Float(string='Packing Forwarding', readonly=True)
    others = fields.Float(string='Others', readonly=True)
    total = fields.Float(string='Total', readonly=True)
    vs_quote_id = fields.Many2one(comodel_name='vs.detail', string='Vendor Selection')
    request_id = fields.Many2one(comodel_name='quotation.request', string='Quotation Request')