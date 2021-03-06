# -*- coding: utf-8 -*-

# Workflow:
#   create----------->Draft (Hospital User)
#       update : requested_by, requested_on, department_id, sequence
#
#   Draft------------>wha (Hospital User)
#       update : requested_by, requested_on, department_id, sequence
#       need   : product detail and its quantity
#       check product in stock
#
#   wha------------->cancel (Hospital HOD)
#       update : approved_by, approved_on
#
#   wha------------->hod_approved (Hospital HOD)
#       update : approved_by, approved_on
#       need   : accepted quantity
#
#   hod_approved---->closed (Hospital User/ Hospital HOD)


#  Sequence based on department
#  No Product duplication
# Smart Button:
#     Show vendor selection, quotation, purchase order, material receipt based on user permission


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
    _rec_name = 'sequence'

    sequence = fields.Char(string='Sequence', readonly=True)
    department_id = fields.Many2one(comodel_name='hospital.department', string='Department')
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

    def check_atleast_one_product(self):
        recs = self.indent_detail

        qty = 0
        for rec in recs:
            qty = qty + rec.accepted_quantity

        if not qty:
            raise exceptions.ValidationError('Error! Atleast one product need accepted quantity')

    def check_vs_cancellation(self):
        recs = self.env['vendor.selection'].search([('indent_id', '=', self.id)])

        for rec in recs:
            if rec.progress != 'cancel':
                raise exceptions.ValidationError('Error! Please cancel all related vendor selection to cancel this indent')

    # Access Function
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

    # Smart Button
    @api.multi
    def smart_vendor_selection(self):
        view_id = self.env['ir.model.data'].get_object_reference('project_indrajith', 'view_vendor_selection_tree')[1]

        return {
            'type': 'ir.actions.act_window',
            'name': 'Vendor Selection',
            'view_mode': 'tree',
            'view_type': 'form',
            'view_id': view_id,
            'domain': [('indent_id', '=', self.id)],
            'res_model': 'vendor.selection',
            'target': 'current',
        }

    @api.multi
    def smart_quotation_request(self):
        view_id = self.env['ir.model.data'].get_object_reference('project_indrajith', 'view_quotation_request_tree')[1]

        return {
            'type': 'ir.actions.act_window',
            'name': 'Quotation Request',
            'view_mode': 'tree',
            'view_type': 'form',
            'view_id': view_id,
            'domain': [('pi_id', '=', self.id)],
            'res_model': 'quotation.request',
            'target': 'current',
        }

    @api.multi
    def smart_purchase_order(self):
        view_id = self.env['ir.model.data'].get_object_reference('project_indrajith', 'view_purchase_order_tree')[1]

        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Order',
            'view_mode': 'tree',
            'view_type': 'form',
            'view_id': view_id,
            'domain': [('indent_id', '=', self.id)],
            'res_model': 'purchase.order',
            'target': 'current',
        }

    @api.multi
    def smart_material_receipt(self):
        view_id = self.env['ir.model.data'].get_object_reference('project_indrajith', 'view_material_receipt_tree')[1]

        return {
            'type': 'ir.actions.act_window',
            'name': 'Material Receipt',
            'view_mode': 'tree',
            'view_type': 'form',
            'view_id': view_id,
            'domain': [('indent_id', '=', self.id)],
            'res_model': 'material.receipt',
            'target': 'current',
        }

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
            'sequence': self.create_sequence(self.env.user.department_id),
        }
        self.write(data)

    @api.multi
    def trigger_hod_approved(self):
        self.check_progress_access()
        self.check_atleast_one_product()
        data = {
            'progress': 'hod_approved',
            'approved_on': datetime.now().strftime('%Y-%m-%d'),
            'approved_by': self.env.user.id,
        }
        self.write(data)

    @api.multi
    def trigger_cancel(self):
        self.check_progress_access()
        self.check_vs_cancellation()
        self.write({'progress': 'cancel'})

    @api.multi
    def trigger_closed(self):
        self.check_progress_access()
        if not self.comment:
            raise exceptions.ValidationError('Error! Comments required for closing indent')
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
    requested_quantity = fields.Float(string='Requested Quantity', required=True)
    accepted_quantity = fields.Float(string='Accepted Quantity')
    indent_id = fields.Many2one(comodel_name='purchase.indent', string='Purchase Indent')
    progress = fields.Selection(PROGRESS_INFO, string='Progress', related='indent_id.progress')

    def check_product_stock_location(self):
        stock_obj = self.env['product.stock']
        product_stock = stock_obj.search([('product_id', '=', self.item_id.id),
                                          ('uom_id', '=', self.uom_id.id),
                                          ('location_id.name', '=', 'Store')])

        if not product_stock:
            raise exceptions.ValidationError('Error! Stock Location for the Product: {0} is not available'.format(self.item_id.name))

    def check_requested_quantity(self, vals):
        if not vals['requested_quantity']:
            raise exceptions.ValidationError('Error! Requested quantity must need')

    # Access Function
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

    # Default Function
    @api.multi
    def unlink(self):
        self.check_progress_access()
        if not self.progress:
            res = super(PIDetail, self).unlink()
        else:
            raise exceptions.ValidationError('Error! You are not authorised to change this record')
        return res

    @api.multi
    def write(self, vals):
        self.check_progress_access()
        res = super(PIDetail, self).write(vals)
        return res

    @api.model
    def create(self, vals):
        self.check_progress_access()
        self.check_requested_quantity(vals)
        res = super(PIDetail, self).create(vals)
        return res

    _sql_constraints = [
        ('duplicate_product', 'unique (item_id, uom_id, indent_id)', "Duplicate Product"),
    ]