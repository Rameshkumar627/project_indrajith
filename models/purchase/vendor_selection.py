# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions


PROGRESS_INFO = [('draft', 'Draft'), ('qrg', 'Quotation Request Generated')]


class VendorSelection(models.Model):
    _name = 'vendor.selection'
    _description = 'Vendor selection by procurement team'

    date = fields.Date(string='Date', readonly=True)
    indent_id = fields.Many2one(comodel_name='purchase.indent', string='Purchase Indent')
    selection_detail = fields.One2many(comodel_name='vendor.selection.detail',
                                       inverse_name='selection_id', string='Vendor Selection Details')
    comment = fields.Text(string='Comment')

    def check_group_access(self, group_list):
        ''' Check if current user in the group list return True'''
        group_ids = self.env.user.groups_id
        status = False
        for group in group_ids:
            if group.name in group_list:
                status = True
        return status

    def check_progress_access(self):
        if self.progress == 'draft':
            group_list = ['Hospital User', 'Admin']
        elif self.progress == 'qrg':
            group_list = ['Hospital Purchase Department', 'Admin']
        else:
            group_list = []

        if not self.check_group_access(group_list):
            raise exceptions.ValidationError('Error! You are not authourised to change this record')

    def create_qrg(self):
        '''Create QR based on the input selection'''
        pass

    @api.multi
    def trigger_qrg(self):
        ''' Progress : draft to qrg'''

        self.check_progress_access()
        self.create_qrg()
        self.write({'progress': 'qrg'})

    @api.model
    def create(self, vals):
        self.check_progress_access()
        res = super(VendorSelection, self).create(vals)
        return res


class VendorSelectionDetail(models.Model):
    _name = 'vendor.selection.detail'
    _description = 'Vendor Selection Details'

    item_id = fields.Many2one(comodel_name='product.product', string='Item', required=True)
    uom_id = fields.Many2one(comodel_name='product.uom', string='UOM', required=True)
    qty = fields.Float(string='Quantity', required=True)
    vendor_ids = fields.Many2many(comodel_name='Vendor', string='Vendors')
    selection_id = fields.Many2one(comodel_name='vendor.selection', string='Vendor Selection')
