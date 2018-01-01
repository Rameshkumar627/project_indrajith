# -*- coding: utf-8 -*-

# On creation create vendor selection detail based on indent (qty > 0)
# On write create quote request based on vendor_ids, no delete of vendor_ids
# On unlink no unlink
# create, write, unlink needs access rights
#

from odoo import models, fields, api, _, exceptions
from datetime import datetime


PROGRESS_INFO = [('draft', 'Draft'),
                 ('qa', 'Quotation Approved')]


class VendorSelection(models.Model):
    _name = 'vendor.selection'
    _description = 'Vendor selection by procurement team'

    date = fields.Date(string='Date', readonly=True)
    indent_id = fields.Many2one(comodel_name='purchase.indent', string='Purchase Indent', required=True)
    progress = fields.Selection(PROGRESS_INFO, default='draft', string='Progress')
    selection_detail = fields.One2many(comodel_name='vs.detail',
                                       inverse_name='selection_id', string='Vendor Selection Details')
    comment = fields.Text(string='Comment')

    # Button Action
    @api.multi
    def generate_quote(self):
        recs = self.selection_detail
        qr_obj = self.env['quotation.request']
        qr_detail_obj = self.env['qr.detail']

        for rec in recs:
            for vendor in rec.vendor_ids:

                # For each vendor check quotation request (create if not available)
                quote = qr_obj.search([('pi_ref', '=', self.indent_id.id),
                                       ('vendor_id', '=', vendor.id),
                                       ('vs_id', '=', self.id )])
                if not quote:
                    qr_data = {
                        'pi_ref': self.indent_id.id,
                        'vendor_id': vendor.id,
                        'vs_id': self.id,
                    }
                    qr_rec = qr_obj.create(qr_data)
                else:
                    qr_rec = quote

                # For each vendor check quotation_detail (create if not available)
                quote_detail = qr_detail_obj.search([('item_id', '=', rec.item_id.id),
                                                     ('uom_id', '=', rec.uom_id.id),
                                                     ('request_id', '=', qr_rec.id)])
                if not quote_detail:
                    qr_detail_data = {
                        'item_id': rec.item_id.id,
                        'uom_id': rec.uom_id.id,
                        'quantity': rec.quantity,
                        'request_id': qr_rec.id,
                    }
                    qr_rec.request_detail.create(qr_detail_data)

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
        obj = self.env['vs.detail']
        pi_recs = self.env['pi.detail'].search([('indent_id', '=', res.indent_id.id),
                                                ('acc_qty', '>', 0)])

        for rec in pi_recs:
            data = {
                'item_id': rec.item_id.id,
                'uom_id': rec.uom_id.id,
                'quantity': rec.acc_qty,
                'selection_id': res.id,
            }

            print data, "------------->>>>>"
            obj.create(data)

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
        print res
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
    tax_id = fields.Many2one(comodel_name='product.tax', string='Tax', readonly=True)
    pf = fields.Float(string='Packing Forwarding', readonly=True)
    others = fields.Float(string='Others', readonly=True)
    total = fields.Float(string='Total', readonly=True)
    vs_quote_id = fields.Many2one(comodel_name='vs.detail', string='Vendor Selection')
