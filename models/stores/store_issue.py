# -*- coding: utf-8 -*-


# Access BY:-
#   Progress :
#       draft        : Hospital User
#       issued       : No Access
#
# Name :
#   sequence
#
# Control:
#   sequence unique
#   creation:
#       check any pending on same store request
#       update: store request detail, accepted qty
#   button issued:
#       check stock availability
#       update: issued_by, issued_on
#       stock reduction in stores, stock updation in location_id
#
# Workflow:
#   Draft ---------->issued


from odoo import fields, models, api, _, exceptions
from datetime import datetime

PROGRESS_INFO = [('draft', 'Draft'), ('issued', 'Issued')]


class StoreIssue(models.Model):
    _name = 'store.issue'
    _description = 'Store Issue'
    _rec_name = 'sequence'

    sequence = fields.Char(string='Sequence', readonly=True)
    request_id = fields.Many2one(comodel_name='store.request',
                                 domain='[("progress", "=", "hod_approved")]',
                                 string='Store Request',
                                 required=True)
    department_id = fields.Many2one(comodel_name='hospital.department', string='Department', readonly=True)
    location_id = fields.Many2one(comodel_name='stock.location', string='Location', readonly=True)
    requested_by = fields.Many2one(comodel_name='res.users', string='Requested By', readonly=True)
    requested_on = fields.Date(string='Requested On', readonly=True)
    issued_by = fields.Many2one(comodel_name='res.users', string='Issued By', readonly=True)
    issued_on = fields.Date(string='Issued On', readonly=True)
    progress = fields.Selection(PROGRESS_INFO, default='draft', string='Progress')
    issue_detail = fields.One2many(comodel_name='si.detail',
                                   string='Store Issue Detail',
                                   inverse_name='issue_id')
    comment = fields.Text(string='Comment')

    def check_progress_access(self):
        group_list = []
        if self.progress in ['draft', 'issued', False]:
            group_list = ['Store User', 'Admin']

        outer_obj = self.env['check.group.access'].browse([('id', '=', 1)])
        if not outer_obj.check_group_access(group_list):
            raise exceptions.ValidationError('Error! You are not authorised to change this record')

    def create_sequence(self):
        obj = self.env['ir.sequence'].sudo()

        sequence = obj.next_by_code('store.issue')
        period = self.env['period.period'].search([('progress', '=', 'open')])
        return '{0}/{1}'.format(sequence, period.name)

    def default_vals_update(self, vals):
        sr = self.env['store.request'].search([('id', '=', vals['request_id'])])
        vals['requested_by'] = sr.requested_by.id
        vals['requested_on'] = sr.requested_on
        vals['department_id'] = sr.department_id.id
        vals['location_id'] = sr.location_id.id
        vals['issue_detail'] = []

        for rec in sr.request_detail:
            vals['issue_detail'].append((0, 0, self.issue_detail_data(vals['request_id'], rec.item_id.id,
                                                                      rec.uom_id.id, rec.acc_qty)))

        return vals

    def issue_detail_data(self, request_id, item_id, uom_id, acc_qty):
        already_issued_qty = 0
        issues = self.env['si.detail'].search([('issue_id.request_id', '=', request_id),
                                               ('item_id', '=', item_id),
                                               ('uom_id', '=', uom_id,)])

        for issue in issues:
            already_issued_qty = already_issued_qty + issue.issuing_qty

        data = {'item_id': item_id,
                'uom_id': uom_id,
                'req_qty': acc_qty,
                'already_issued_qty': already_issued_qty}

        return data

    def check_request_pending(self, vals):
        recs = self.env['store.issue'].search([('request_id', '=', vals['request_id']),
                                               ('progress', '!=', 'issued')])
        if recs:
            raise exceptions.ValidationError('Error! Already one issue pending')

    # Logic Function
    def stock_reduction(self):
        store_loc = self.env['stock.location'].search([('name', '=', 'Store')])
        request_loc = self.location_id
        recs = self.issue_detail
        for rec in recs:
            rec.check_stock()

        for rec in recs:
            self.env['product.stock'].stock_move(rec.item_id, rec.uom_id, store_loc, request_loc, rec.issuing_qty)

    def check_quantity(self):
        recs = self.issue_detail

        qty = 0
        for rec in recs:
            qty = qty + rec.issuing_qty

        if not qty:
            raise exceptions.ValidationError('Error! Atleast 1 Quantity should be needed')

    # Button Action
    @api.multi
    def trigger_issued(self):
        self.stock_reduction()
        self.check_quantity()
        data = {
            'progress': 'issued',
            'issued_by': self.env.user.id,
            'issued_on': datetime.now().strftime('%Y-%m-%d'),
            'sequence': self.create_sequence()
        }
        self.write(data)
        self.request_id.issue_trigger()

    # Default Function
    @api.multi
    def unlink(self):
        self.check_progress_access()
        if self.sequence:
            raise exceptions.ValidationError('Error! You are not authorised to change this record')
        return super(StoreIssue, self).unlink()

    @api.multi
    def write(self, vals):
        self.check_progress_access()
        if 'request_id' in vals:
            raise exceptions.ValidationError('Error! You cannot change store request selection after creation')
        return super(StoreIssue, self).write(vals)

    @api.model
    def create(self, vals):
        self.check_progress_access()
        self.check_request_pending(vals)
        vals = self.default_vals_update(vals)
        return super(StoreIssue, self).create(vals)


class SIDetail(models.Model):
    _name = 'si.detail'
    _description = 'Store Issue Detail'

    item_id = fields.Many2one(comodel_name='product.product', string='Item', readonly=True)
    uom_id = fields.Many2one(comodel_name='product.uom', string='UOM', readonly=True)
    req_qty = fields.Float(string='Requested Quantity', readonly=True)
    already_issued_qty = fields.Float(string='Already Issued Quantity', readonly=True)
    issuing_qty = fields.Float(string='Issuing Quantity')
    issue_id = fields.Many2one(comodel_name='store.issue', string='Store Issue')
    progress = fields.Selection(PROGRESS_INFO, string='Progress', related='issue_id.progress')

    @api.constrains('issuing_qty')
    def _validate_quantity(self):
        if (self.already_issued_qty + self.issuing_qty) > self.req_qty:
            raise exceptions.ValidationError("Quantity should not be greater than requested quantity")

    def check_stock(self):
        quantity = 0
        stock_obj = self.env['product.stock']
        store_stock = stock_obj.search([('product_id', '=', self.item_id.id),
                                        ('location_id.name', '=', 'Store'),
                                        ('uom_id', '=', self.uom_id.id)])

        quantity = store_stock.quantity - self.issuing_qty

        if (quantity < 0) or (store_stock.quantity <= 0):
            raise exceptions.ValidationError('Error! Store Quantity is lesser than issue quantity')

