# -*- coding: utf-8 -*-

# Workflow:
#   create----------->Draft (procurement User)
#       update : date
#       create quote_detail (accepted_qty > 0)
#
#   Button: generate_quote
#       need   : vendor for each product
#       create vs_quote_detail
#       create quotation_request
#       map vs_quote_detail and quotation_request
#
#   draft------------>qa (procurement User, Manageent)
#       require vs_quote_detail comment (if no accepted qty for 1 product, to 1 user )
#       create purchase_order and pr_detail
#       Button: generate_quote invisible
#
#   draft------------->cancel (procurement User, Hospital Management)
#

# No unlink


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

    def create_purchase_order(self):
        recs = self.env['vs.quote.detail'].search([('vs_quote_id.selection_id', '=', self.id), ('accepted_quantity', '>', 0)])

        vendor_list = []
        for rec in recs:
            if rec.vendor_id.id not in vendor_list:
                vendor_list.append(rec.vendor_id.id)

        for vendor in vendor_list:
            records = self.env['vs.quote.detail'].search([('vs_quote_id.selection_id', '=', self.id),
                                                          ('accepted_quantity', '>', 0),
                                                          ('vendor_id', '=', vendor)])

            for record in records:
                po = self.env['purchase.order'].search([('indent_id', '=', self.indent_id.id),
                                                        ('qr_id', '=', record.request_id.id)])
                if not po:
                    data = {
                        'po_type': 'normal_po',
                        'indent_id': self.indent_id.id,
                        'qr_id': record.request_id.id,
                    }
                    po = self.env['purchase.order'].create(data)
                po_detail = self.env['po.detail'].search([('item_id', '=', record.item_id.id),
                                                          ('uom_id', '=', record.uom_id.id)])

                if not po_detail:
                    data = {
                        'item_id': record.item_id.id,
                        'uom_id': record.uom_id.id,
                        'quantity': record.accepted_quantity,
                        'tax_id': record.tax_id.id,
                        'pf': record.pf,
                        'others': record.others,
                        'total': record.total,

                    }
                    self.env['po.detail'].create(data)

    def check_vs_quote_detail(self):
        records = self.selection_detail

        for record in records:
            qty = 0
            for rec in record.quote_detail:
                qty = qty + rec.accepted_quantity
            if not qty:
                if not rec.comment:
                    raise exceptions.ValidationError('Error! Required comments if no quantity is given')

    def create_quotation_request(self):

        vendors_list = []
        recs = self.selection_detail
        for rec in recs:
            for record in rec.quote_detail:
                if record.vendor_id.id not in vendors_list:
                    vendors_list.append(record.vendor_id.id)

        #  Check vendor
        for vendor in vendors_list:
            qr = self.env['quotation.request'].search([('vendor_id', '=', vendor),
                                                       ('vs_id', '=', self.id)])

            vs_rec = self.env['vs.quote.detail'].search([('vs_quote_id.selection_id', '=', self.id),
                                                         ('vendor_id', '=', vendor)])

            if not qr:
                data = {
                    'pi_ref': self.indent_id.id,
                    'vendor_id': vendor,
                    'vs_id': self.id,
                    'progress': 'draft',
                }
                qr = self.env['quotation.request'].create(data)

            for vs_re in vs_rec:
                vs_re.write({'request_id': qr.id})

    # Button Action
    @api.multi
    def trigger_generate_vs_quote_detail(self):
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
                        'requested_quantity': rec.requested_quantity,
                    }
                    self.env['vs.quote.detail'].create(data)

        # create quotation request based on vs_quote_detail
        self.create_quotation_request()

    @api.multi
    def trigger_quote_approved(self):
        self.check_vs_quote_detail()
        self.create_purchase_order()
        data = {'progress': 'qa'}
        self.write(data)
        recs = self.env['quotation.request'].search([('vs_id', '=', self.id)])
        for rec in recs:
            rec.write(data)

    def check_progress_access(self):
        group_list = []
        if self.progress in ['draft', False]:
            group_list = ['procurement User', 'Admin']
        elif self.progress == 'qa':
            group_list = ['procurement User', 'Hospital Management', 'Admin']

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
                                                ('accepted_quantity', '>', 0)])

        for rec in pi_recs:
            data = {
                'item_id': rec.item_id.id,
                'uom_id': rec.uom_id.id,
                'quantity': rec.accepted_quantity,
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

    item_id = fields.Many2one(comodel_name='product.product', string='Item', readonly=True)
    uom_id = fields.Many2one(comodel_name='product.uom', string='UOM', readonly=True)
    requested_quantity = fields.Float(string='Quantity', readonly=True)
    vendor_ids = fields.Many2many(comodel_name='hospital.partner', string='Vendors')
    quote_detail = fields.One2many(comodel_name='vs.quote.detail', inverse_name='vs_quote_id',
                                   string='Quote Detail')
    comment = fields.Text(string='Comment')
    selection_id = fields.Many2one(comodel_name='vendor.selection', string='Vendor Selection')
    progress = fields.Char(string='Progress', compute='get_progress', store=False)

    def get_progress(self):
        for rec in self:
            rec.progress = rec.selection_id.progress

    def check_progress_access(self):
        group_list = []
        if self.progress in ['draft', False]:
            group_list = ['procurement User', 'Admin']
        elif self.progress == 'qa':
            group_list = ['procurement User', 'Hospital Management', 'Admin']

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
        res = super(VSDetail, self).write(vals)
        return res

    @api.model
    def create(self, vals):
        self.check_progress_access()
        res = super(VSDetail, self).create(vals)
        return res


class VSQuoteDetail(models.Model):
    _name = 'vs.quote.detail'
    _description = 'Vendor Selection Quote Detail'

    vendor_id = fields.Many2one(comodel_name='hospital.partner', string='Vendor', readonly=True)
    requested_quantity = fields.Float(string='Requested Quantity', default=0)
    accepted_quantity = fields.Float(string='Accepted Quantity', default=0)
    item_id = fields.Many2one(comodel_name='product.product', string='Product', related='vs_quote_id.item_id')
    uom_id = fields.Many2one(comodel_name='product.uom', string='UOM', related='vs_quote_id.uom_id')
    tax_id = fields.Many2one(comodel_name='product.tax', string='Tax', required=True)
    discount = fields.Float(string='Discount', default=0, readonly=True)
    pf = fields.Float(string='Packing Forwarding', default=0)
    others = fields.Float(string='Others', default=0)
    total = fields.Float(string='Total', default=0, readonly=True)

    igst = fields.Float(string='IGST', default=0, readonly=True)
    cgst = fields.Float(string='CGST', default=0, readonly=True)
    sgst = fields.Float(string='SGST', default=0, readonly=True)
    tax_amount = fields.Float(string='Tax Amount', default=0, readonly=True)

    vs_quote_id = fields.Many2one(comodel_name='vs.detail', string='Vendor Selection')
    request_id = fields.Many2one(comodel_name='quotation.request', string='Quotation Request')
    progress = fields.Char(string='Progress', compute='get_progress', store=False)

    def get_progress(self):
        for rec in self:
            rec.progress = rec.vs_quote_id.selection_id.progress

    def check_progress_access(self):
        group_list = []
        if self.progress in ['draft', False]:
            group_list = ['procurement User', 'Admin']
        elif self.progress == 'qa':
            group_list = ['procurement User', 'Hospital Management', 'Admin']

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
        res = super(VSQuoteDetail, self).write(vals)
        return res

    @api.model
    def create(self, vals):
        self.check_progress_access()
        res = super(VSQuoteDetail, self).create(vals)
        return res

    _sql_constraints = [
        ('duplicate_product', 'unique (item_id, uom_id, request_id, vendor_id)', "Duplicate Product"),
    ]