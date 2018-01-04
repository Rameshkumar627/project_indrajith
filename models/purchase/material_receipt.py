# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions
from datetime import datetime


PROGRESS_INFO = [('draft', 'Draft'), ('inspected', 'Inspected'), ('cancel', 'Cancel')]


class MaterialReceipt(models.Model):
    _name = 'material.receipt'
    _description = 'Material Receipt'

    sequence = fields.Char(string='Sequence', readonly=True)
    date = fields.Date(string='Date', readonly=True)
    indent_id = fields.Many2one(comodel_name='purchase.indent', string='Purchase Indent', readonly=True)
    qr_id = fields.Many2one(comodel_name='quotation.request', string='Quotation Request', readonly=True)
    po_id = fields.Many2one(comodel_name='purchase.order', string='Purchase Order', readonly=True)
    mr_detail = fields.One2many(comodel_name='mr.detail', string='MR Detail', inverse_name='mr_id')
    received_by = fields.Many2one(comodel_name='res.users', string='Received By', readonly=True)
    inspected_by = fields.Many2one(comodel_name='res.users', string='Inspected By', readonly=True)
    progress = fields.Selection(PROGRESS_INFO, string='Progress')
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

        res = super(MaterialReceipt, self).create(vals)
        return res


class MRDetail(models.Model):
    _name = 'mr.detail'
    _description = 'Material Receipt Details'

    item_id = fields.Many2one(comodel_name='product.product', string='Item', readonly=True)
    uom_id = fields.Many2one(comodel_name='product.uom', string='UOM', readonly=True)
    quantity = fields.Float(string='Quantity', readonly=True)
    tax_id = fields.Many2one(comodel_name='product.tax', string='Tax', readonly=True)
    pf = fields.Float(string='Packing Forwarding', readonly=True)
    others = fields.Float(string='Others', readonly=True)
    total = fields.Float(string='Total', readonly=True)
    mr_id = fields.Many2one(comodel_name='material.receipt', string='Material Receipt')

    requested_quantity = fields.Float(string='Requested Quantity')
    received_quantity = fields.Float(string='Received Quantity')
    accepted_quantity = fields.Float(string='Accepted Quantity')
    balance_quantity = fields.Float(string='Balance Quantity')


