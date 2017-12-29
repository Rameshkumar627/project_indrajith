# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions
from datetime import datetime


PROGRESS_INFO = [('draft', 'Draft'), ('wha', 'Waiting For HOD'),
                 ('weg', 'Waiting For Management'), ('cancel', 'Cancel'),
                 ('closed', 'Closed')]


class PurchaseIndent(models.Model):
    _name = 'purchase.indent'
    _description = 'Purchase indent raised by user/department acceptation from management'

    date = fields.Date(string='Date', readonly=True)
    sequence = fields.Char(string='Sequence', readonly=True)
    raised_by = fields.Many2one(comodel_name='res.users', string='Raised By', readonly=True)
    raised_on = fields.Date(string='Raised On', readonly=True)
    department_id = fields.Many2one(comodel_name='hospital.department', required=True)
    approved_by = fields.Many2one(comodel_name='res.users', string='Approved By', readonly=True)
    approved_on = fields.Date(string='Approved On', readonly=True)
    progress = fields.Selection(PROGRESS_INFO, string='Progress', default=True, readonly=True )
    indent_detail = fields.One2many(comodel_name='purchase.indent.detail',
                                    inverse_name='indent_id',
                                    string='Indent Details')
    comment = fields.Text(string='Comment')

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

    def default_vals_update(self, vals):
        vals['raised_on'] = datetime.now().strftime('%Y-%m-%d')
        vals['raised_by'] = self.env.user.id
        vals['department_id'] = self.env.user.deparment_id.id

        vals['sequence'] = self.create_sequence(vals['department'])
        return vals

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
        elif self.progress == 'wha':
            group_list = ['Hospital HOD', 'Admin']
        elif self.progress == 'weg':
            group_list = ['Hospital Management', 'Admin']
        elif self.progress in ['cancel', 'closed']:
            group_list = []
        else:
            group_list = []

        if not self.check_group_access(group_list):
            raise exceptions.ValidationError('Error! You are not authourised to change this record')

    @api.multi
    def trigger_wha(self):
        ''' Progress : draft to wha'''

        self.check_progress_access()
        self.write({'progress': 'wha'})

    @api.multi
    def trigger_weg(self):
        ''' Progress : wha to weg'''

        self.check_progress_access()
        self.write({'progress': 'weg'})

    @api.multi
    def trigger_cancel(self):
        ''' Progress : wha, weg to cancel'''

        self.check_progress_access()
        self.write({'progress': 'cancel'})

    @api.model
    def create(self, vals):
        '''Update default values and sequence creation'''
        self.check_progress_access()
        vals = self.default_vals_update(vals)
        res = super(PurchaseIndent, self).create(vals)
        return res


class PurchaseIndentDetail(models.Model):
    _name = 'purchase.indent.detail'
    _description = 'Purchase Indent Details'

    item_id = fields.Many2one(comodel_name='product.product', string='Item', required=True)
    uom_id = fields.Many2one(comodel_name='product.uom', string='UOM', required=True)
    req_qty = fields.Float(string='Requested Quantity', required=True)
    acc_qty = fields.Float(string='Approved Quantity')
    indent_id = fields.Many2one(comodel_name='purchase.indent', string='Indent')


