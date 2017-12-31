# -*- coding: utf-8 -*-

# No Duplicate in sequence
# On create include requested by, requested on, department and check access
# On write only check access
# On delete check access, no delete when sequence created
# On confirmation sequence created and applied for HOD
# Hod can approve/ cancel
# User can close after HOD approval
# Before cancellation check for any store issue
# Smart Button to show all purchase based on this request

from odoo import fields, models, api, _, exceptions
from datetime import datetime

PROGRESS_INFO = [('draft', 'Draft'),
                 ('wha', 'Waiting For HOD Approval'),
                 ('cancel', 'Cancel'),
                 ('hod_approved', 'HOD Approved'),
                 ('closed', 'Closed')]


class PurchaseIndent(models.Model):
    _name = 'purchase.indent'
    _description = 'Purchase Indent'

    sequence = fields.Char(string='Sequence', readonly=True)
    department_id = fields.Many2one(comodel_name='hospital.department', string='Department')
    location_id = fields.Many2one(comodel_name='stock.location', string='Location', required=True)
    requested_by = fields.Many2one(comodel_name='res.users', string='Requested By', readonly=True)
    requested_on = fields.Date(string='Requested On', readonly=True)
    approved_by = fields.Many2one(comodel_name='res.users', string='Approved By', readonly=True)
    approved_on = fields.Date(string='Approved On', readonly=True)
    progress = fields.Selection(PROGRESS_INFO, default='draft', string='Progress')
    indent_detail = fields.One2many(comodel_name='pi.detail',
                                    string='Purchase Indent Detail',
                                    inverse_name='indent_id')
    comment = fields.Text(string='Comment')

    def default_vals_update(self, vals):
        vals['requested_by'] = self.env.user.id
        vals['requested_on'] = datetime.now().strftime('%Y-%m-%d')
        vals['department_id'] = self.env.user.department_id.id
        return vals

    def check_product_stock_location(self):
        recs = self.indent_detail

        for rec in recs:
            rec.check_product_stock_location()

    def check_store_issue(self):
        recs = self.env['store.issue'].search([('request_id', '=', self.id)])
        if recs:
            raise exceptions.ValidationError('''Error! You can close this record, 
                                                since the store already issue for this request''')

    def check_progress_access(self):
        group_list = []
        if self.progress in ['draft', False]:
            group_list = ['Hospital User', 'Admin']
        elif self.progress == 'wha':
            group_list = ['Hospital HOD', 'Admin']
        elif self.progress == 'hod_approved':
            group_list = ['Hospital User', 'Admin']

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

        sequence = obj.next_by_code('purchase.indent.{0}'.format(department_id.name))
        period = self.env['period.period'].search([('progress', '=', 'open')])
        return '{0}/{1}'.format(sequence, period.name)

    def department_sequence_creation(self, department_id):
        obj = self.env['ir.sequence'].sudo()
        if not obj.search([('code', '=', 'purchase.indent.{0}'.format(department_id.name))]):
            seq = {
                'name': 'purchase.indent.{0}'.format(department_id.name),
                'implementation': 'standard',
                'code': 'purchase.indent.{0}'.format(department_id.name),
                'prefix': 'PI/{0}/'.format(str(department_id.name)),
                'padding': 4,
                'number_increment': 1,
                'use_date_range': False,
            }
            obj.create(seq)

    # Button Action
    @api.multi
    def trigger_wha(self):
        self.check_progress_access()
        self.check_product_stock_location()
        data = {
            'progress': 'wha',
            'requested_on': datetime.now().strftime('%Y-%m-%d'),
            'requested_by': self.env.user.id,
            'department_id': self.env.user.department_id.id,
            'sequence': self.create_sequence(),
        }
        self.write(data)

    @api.multi
    def trigger_hod_approved(self):
        self.check_progress_access()
        data = {
            'progress': 'hod_approved',
            'approved_on': datetime.now().strftime('%Y-%m-%d'),
            'approved_by': self.env.user.id,
        }
        self.write(data)

    @api.multi
    def trigger_cancel(self):
        self.check_progress_access()
        self.check_store_issue()
        self.write({'progress': 'cancel'})

    @api.multi
    def trigger_closed(self):
        self.check_progress_access()
        self.write({'progress': 'closed'})

    # Default Function
    @api.multi
    def unlink(self):
        self.check_progress_access()
        if not self.progress:
            res = super(PurchaseIndent, self).unlink()
        else:
            raise exceptions.ValidationError('Error! You are not authorised to change this record')
        return res

    @api.multi
    def write(self, vals):
        self.check_progress_access()
        res = super(PurchaseIndent, self).write(vals)
        return res

    @api.model
    def create(self, vals):
        self.check_progress_access()
        vals = self.default_vals_update(vals)
        res = super(PurchaseIndent, self).create(vals)
        return res


class PIDetail(models.Model):
    _name = 'pi.detail'
    _description = 'Purchase Indent Detail'

    item_id = fields.Many2one(comodel_name='product.product', string='Item', required=True)
    uom_id = fields.Many2one(comodel_name='product.uom', string='UOM', required=True)
    req_qty = fields.Float(string='Requested Quantity', required=True)
    acc_qty = fields.Float(string='Accepted Quantity')
    indent_id = fields.Many2one(comodel_name='purchase.indent', string='Purchase Indent')
    progress = fields.Char(string='Progress', compute='get_progress', store=False)

    def get_progress(self):
        for rec in self:
            rec.progress = rec.indent_id.progress

    def check_product_stock_location(self):
        stock_obj = self.env['product.stock']
        product_stock = stock_obj.search([('product_id', '=', self.item_id.id),
                                          ('uom_id', '=', self.uom_id.id),
                                          ('location_id', '=', self.indent_id.location_id.id)])

        if not product_stock:
            raise exceptions.ValidationError('Error! Stock Location for the Product: {0} is not available'.format(self.item_id.name))

    _sql_constraints = [
        ('duplicate_product', 'unique (item_id, uom_id, indent_id)', "Duplicate Product"),
    ]