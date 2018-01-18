# -*- coding: utf-8 -*-

# Access BY:-
#   Progress :
#       draft        : Hospital User
#       wha          : Hospital HOD
#       hod_approved : Hospital User, Hospital HOD
#       cancel       : No Access
#       closed       : No Access
#
# Name :
#   sequence
#
# Control:
#   sequence unique
#   sequence based on department
#   creation:
#       update: requested_by, requested_on, department_id, need location_id, product detail, required qty
#   button wha:
#       check product_stock (if available)
#       update requested_by, requested_on, department_id, sequence
#   button hod_approved:
#       required product accepted qty
#       update approved_by, approved_on
#   button cancel:
#       check any store issue
#       update approved_by, approved_on
#   button closed:
#       automated close by Hospital store---fully issued
#       force close by Hospital user--------no/ partially issued
#
# Workflow:
#   Draft ---------->wha
#   wha------------->hod_approve/ cancel
#   hod_approved---->closed


from odoo import fields, models, api, _, exceptions
from datetime import datetime

PROGRESS_INFO = [('draft', 'Draft'),
                 ('wha', 'Waiting For HOD Approval'),
                 ('cancel', 'Cancel'),
                 ('hod_approved', 'HOD Approved'),
                 ('closed', 'Closed')]


class StoreRequest(models.Model):
    _name = 'store.request'
    _description = 'Store Request'
    _rec_name = 'sequence'

    sequence = fields.Char(string='Sequence', readonly=True)
    department_id = fields.Many2one(comodel_name='hospital.department', string='Department', readonly=True)
    location_id = fields.Many2one(comodel_name='stock.location', string='Location', required=True)
    requested_by = fields.Many2one(comodel_name='res.users', string='Requested By', readonly=True)
    requested_on = fields.Date(string='Requested On', readonly=True)
    approved_by = fields.Many2one(comodel_name='res.users', string='Approved By', readonly=True)
    approved_on = fields.Date(string='Approved On', readonly=True)
    progress = fields.Selection(PROGRESS_INFO, default='draft', string='Progress')
    request_detail = fields.One2many(comodel_name='sr.detail',
                                     string='Store Request Detail',
                                     inverse_name='request_id')
    comment = fields.Text(string='Comment')

    def check_store_issue(self):
        recs = self.env['store.issue'].search([('request_id', '=', self.id),
                                               ('progress', '!=', 'issued')])
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
            group_list = ['Hospital User', 'Hospital HOD', 'Hospital Store', 'Admin']

        outer_obj = self.env['check.group.access'].browse([('id', '=', 1)])
        if not outer_obj.check_group_access(group_list):
            raise exceptions.ValidationError('Error! You are not authorised to change this record')

    def create_sequence(self, department_id):
        obj = self.env['ir.sequence'].sudo()
        outer_obj = self.env['check.group.access'].browse([('id', '=', 1)])
        outer_obj.store_request_sequence_creation(department_id)

        sequence = obj.next_by_code('store.request.{0}'.format(department_id.name))
        period = self.env['period.period'].search([('progress', '=', 'open')])
        return '{0}/{1}'.format(sequence, period.name)

    # Button Action
    @api.multi
    def trigger_wha(self):
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
        data = {
            'progress': 'hod_approved',
            'approved_on': datetime.now().strftime('%Y-%m-%d'),
            'approved_by': self.env.user.id,
        }
        self.write(data)

    @api.multi
    def trigger_cancel(self):
        self.check_store_issue()
        self.write({'progress': 'cancel'})

    @api.multi
    def trigger_closed(self):
        self.write({'progress': 'closed'})

    @api.multi
    def issue_trigger(self):
        recs = self.request_detail

        status = True
        for rec in recs:
            if not rec.check_issue_satisfied():
                status = False

        if status:
            self.write({'progress': 'closed'})

    @api.multi
    def smart_store_issue(self):
        view_id = self.env['ir.model.data'].get_object_reference('project_indrajith', 'view_store_issue_tree')[1]
        return {
            'type': 'ir.actions.act_window',
            'name': 'Store Issue',
            'view_mode': 'tree',
            'view_type': 'form',
            'view_id': view_id,
            'domain': [('request_id', '=', self.id)],
            'res_model': 'store.issue',
            'target': 'current',
        }

    # Default Function
    @api.multi
    def unlink(self):
        self.check_progress_access()
        if self.sequence:
            raise exceptions.ValidationError('Error! You are not authorised to change this record')
        return super(StoreRequest, self).unlink()

    @api.multi
    def write(self, vals):
        self.check_progress_access()
        return super(StoreRequest, self).write(vals)

    @api.model
    def create(self, vals):
        self.check_progress_access()
        vals['requested_by'] = self.env.user.id
        vals['requested_on'] = datetime.now().strftime('%Y-%m-%d')
        vals['department_id'] = self.env.user.department_id.id
        return super(StoreRequest, self).create(vals)


class SRDetail(models.Model):
    _name = 'sr.detail'
    _description = 'Store Request Detail'

    item_id = fields.Many2one(comodel_name='product.product', string='Item', required=True)
    uom_id = fields.Many2one(comodel_name='product.uom', string='UOM', required=True)
    req_qty = fields.Float(string='Requested Quantity', required=True)
    acc_qty = fields.Float(string='Accepted Quantity')
    request_id = fields.Many2one(comodel_name='store.request', string='Store Request')
    progress = fields.Selection(PROGRESS_INFO, string='Progress', related='request_id.progress')

    def check_issue_satisfied(self):
        status = False
        issued_qty = 0
        issues = self.env['si.detail'].search([('item_id', '=', self.item_id.id),
                                               ('uom_id', '=', self.uom_id.id),
                                               ('issue_id.request_id', '=', self.request_id.id)])

        for issue in issues:
            issued_qty = issued_qty + issue.issuing_qty

        if self.acc_qty > issued_qty:
            raise exceptions.ValidationError('Error! Issue is more than requested quantity')
        if issued_qty == self.acc_qty:
            status = True

        return status

    _sql_constraints = [
        ('duplicate_product', 'unique (item_id, uom_id, request_id)', "Duplicate Product"),
    ]