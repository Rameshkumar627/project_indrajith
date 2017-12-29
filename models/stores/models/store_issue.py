# -*- coding: utf-8 -*-

from odoo import fields, models, api, _, exceptions
from datetime import datetime

PROGRESS_INFO = [('draft', 'Draft'), ('issued', 'Issued'), ('cancel', 'Cancel')]


class StoreIssue(models.Model):
    _name = 'store.issue'
    _description = 'Store Issue'

    date = fields.Date(string='Date', readonly=True)
    sequence = fields.Char(string='Sequence')
    requested_by = fields.Many2one(comodel_name='res.users', string='Requested By', readonly=True)
    requested_on = fields.Date(string='Requested On', readonly=True)
    processed_by = fields.Many2one(comodel_name='res.users', string='Processed By', readonly=True)
    processed_on = fields.Date(string='Processed On', readonly=True)
    progress = fields.Selection(PROGRESS_INFO, default='draft', string='Progress')
    request_detail = fields.One2many(comodel_name='si.detail',
                                     string='Store Request Detail',
                                     inverse_name='issue_id')
    comment = fields.Text(string='Comment')

    def stock_updation(self):
        pass

    def stock_reduction(self):
        self.check_stock()
        pass

    def check_stock(self):
        recs = self.request_detail
        for rec in recs:
            rec.check_stcok()

    @api.multi
    def trigger_cancel(self):
        self.check_progress_access()
        self.stock_reduction()
        self.write({'progress': 'cancel'})

    @api.multi
    def trigger_issued(self):
        self.check_progress_access()
        self.stock_reduction()
        self.write({'progress': 'issued',
                    'processed_by': self.env.user.id,
                    'processed_on': datetime.now().strftime('%Y-%m-%d')})

    def check_progress_access(self):
        if self.progress in ['draft', 'issued']:
            group_list = ['Store User', 'Admin']
        elif self.progress == 'cancel':
            group_list = []

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
        self.department_sequence_creation()

        sequence = obj.next_by_code('store.issue')
        period = self.env['period.period'].search([('progress', '=', 'open')])
        return '{0}/{1}'.format(sequence, period.name)

    def department_sequence_creation(self):
        obj = self.env['ir.sequence'].sudo()
        if not obj.search([('code', '=', 'store.issue')]):
            seq = {
                'name': 'Store Isssue',
                'implementation': 'standard',
                'code': 'store.issue',
                'prefix': 'SI/',
                'padding': 4,
                'number_increment': 1,
                'use_date_range': False,
            }
            obj.create(seq)

    def default_vals_update(self, vals):
        vals['sequence'] = self.create_sequence()
        vals['date'] = datetime.now().strftime('%Y-%m-%d')
        return vals

    @api.model
    def create(self, vals):
        self.check_progress_access()
        vals = self.default_vals_update(vals)
        res = super(StoreIssue, self).create(vals)
        return res


class SIDetail(models.Model):
    _name = 'si.detail'
    _description = 'Store Issue Detail'

    item_id = fields.Many2one(comodel_name='product.product', string='Item', readonly=True)
    uom_id = fields.Many2one(comodel_name='product.uom', string='UOM', readonly=True)
    req_qty = fields.Float(string='Requested Quantity', readonly=True)
    already_issued_qty = fields.Float(string='Already Issued Quantity', readonly=True)
    issuing_qty = fields.Float(string='Issuing Quantity')
    issue_id = fields.Many2one(comodel_name='store.issue', string='Store Issue')

    def check_stock(self):
        pass
