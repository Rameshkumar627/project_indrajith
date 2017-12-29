# -*- coding: utf-8 -*-

from odoo import fields, models, api, _, exceptions
from datetime import datetime

PROGRESS_INFO = [('draft', 'Draft'), ('wha', 'Waiting For HOD Approval'), ('hod_approved', 'HOD Approved'), 
                 ('cancel', 'Cancel'), ('closed', 'Closed')]


class StoreRequest(models.Model):
    _name = 'store.request'
    _description = 'Store Request'

    date = fields.Date(string='Date', readonly=True)
    sequence = fields.Char(string='Sequence')
    requested_by = fields.Many2one(comodel_name='res.users', string='Requested By', readonly=True)
    requested_on = fields.Date(string='Requested On', readonly=True)
    approved_by = fields.Many2one(comodel_name='res.users', string='Approved By', readonly=True)
    approved_on = fields.Date(string='Approved On', readonly=True)
    progress = fields.Selection(PROGRESS_INFO, default='draft', string='Progress')
    request_detail = fields.One2many(comodel_name='sr.detail',
                                     string='Store Request Detail',
                                     inverse_name='request_id')
    comment = fields.Text(string='Comment')

    def check_progress_access(self):
        if self.progress == 'draft':
            group_list = ['Hospital User', 'Admin']
        elif self.progress == 'wha':
            group_list = ['Hospital HOD', 'Admin']
        elif self.progress == 'hod_approved':
            group_list = []
        elif self.progress in ['cancel', 'closed']:
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

    def create_sequence(self, department_id):
        obj = self.env['ir.sequence'].sudo()
        self.department_sequence_creation(department_id)

        sequence = obj.next_by_code('purchase.request.{0}'.format(department_id.name))
        period = self.env['period.period'].search([('progress', '=', 'open')])
        return '{0}/{1}'.format(sequence, period.name)

    def department_sequence_creation(self, department_id):
        obj = self.env['ir.sequence'].sudo()
        if not obj.search([('code', '=', 'purchase.indent.{0}'.format(department_id.name))]):
            seq = {
                'name': department_id.name,
                'implementation': 'standard',
                'code': 'purchase.request.{0}'.format(department_id.name),
                'prefix': 'PI/{0}/'.format(str(department_id.name)),
                'padding': 4,
                'number_increment': 1,
                'use_date_range': False,
            }
            obj.create(seq)

    @api.multi
    def trigger_wha(self):
        self.check_progress_access()
        self.write({'progress': 'wha'})

    @api.multi
    def trigger_hod_approved(self):
        self.check_progress_access()
        self.write({
            'progress': 'hod_approved',
            'requested_on': datetime.now().strftime('%Y-%m-%d'),
            'requested_by': self.env.user.id,
        })

    @api.multi
    def trigger_cancel(self):
        self.check_progress_access()
        self.write({'progress': 'cancel'})

    @api.multi
    def trigger_closed(self):
        self.check_progress_access()
        self.write({'progress': 'closed'})

    def default_vals_update(self, vals):
        vals['requested_on'] = datetime.now().strftime('%Y-%m-%d') 
        vals['requested_by'] = self.env.user.id
        vals['sequence'] = self.create_sequence()
        vals['date'] = datetime.now().strftime('%Y-%m-%d')
        return vals

    @api.model
    def create(self, vals):
        self.check_progress_access()
        vals = self.default_vals_update(vals)
        res = super(StoreRequest, self).create(vals)
        return res


class SRDetail(models.Model):
    _name = 'sr.detail'
    _description = 'Store Request Detail'

    item_id = fields.Many2one(comodel_name='product.product', string='Item')
    uom_id = fields.Many2one(comodel_name='product.uom', string='UOM')
    req_qty = fields.Float(string='Requested Quantity')
    acc_qty = fields.Float(string='Accepted Quantity')
    request_id = fields.Many2one(comodel_name='store.request', string='Store Request')
