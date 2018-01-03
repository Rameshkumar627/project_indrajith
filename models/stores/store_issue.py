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
    request_id = fields.Many2one(comodel_name='store.request', string='Store Request', reaquired=True)
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

    # Logic Function
    def stock_reduction(self):
        recs = self.issue_detail
        for rec in recs:
            rec.check_stock()

        for rec in recs:
            rec.stock_reduction()

    @api.multi
    def trigger_issued(self):
        self.check_progress_access()
        self.stock_reduction()
        data = {
            'progress': 'issued',
            'issued_by': self.env.user.id,
            'issued_on': datetime.now().strftime('%Y-%m-%d'),
            'sequence': self.create_sequence()
        }
        self.write(data)

    def check_progress_access(self):
        group_list = []
        if self.progress in ['draft', 'issued']:
            group_list = ['Store User', 'Admin']

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

        sequence = obj.next_by_code('store.issue')
        period = self.env['period.period'].search([('progress', '=', 'open')])
        return '{0}/{1}'.format(sequence, period.name)

    def default_vals_update(self, vals):
        sr = self.env['store.request'].search([('id', '=', vals['request_id'])])
        vals['requested_by'] = sr.requested_by.id
        vals['requested_on'] = sr.requested_on
        vals['department_id'] = sr.department_id.id
        vals['location_id'] = sr.location_id.id

        return vals

    def issue_detail_creation(self, si):
        for rec in si.request_id.request_detail:
            issues = self.env['si.detail'].search([('issue_id.request_id', '=', si.request_id.id),
                                                   ('item_id', '=', rec.item_id.id),
                                                   ('uom_id', '=', rec.uom_id.id,)])
            already_issued_qty = 0
            for issue in issues:
                already_issued_qty = already_issued_qty + issue.issuing_qty

            data = {
                'item_id': rec.item_id.id,
                'uom_id': rec.uom_id.id,
                'req_qty': rec.acc_qty,
                'already_issued_qty': already_issued_qty,
                'issue_id': si.id
            }

            si.create(data)

    def check_request_pending(self, vals):
        recs = self.env['store.issue'].search([('request_id', '=', vals['request_id']),
                                               ('progress', '!=', 'issued')])
        if recs:
            raise exceptions.ValidationError('Error! Already one issue pending')

    @api.multi
    def unlink(self):
        self.check_progress_access()
        if not self.progress:
            res = super(StoreIssue, self).unlink()
        return res

    @api.multi
    def write(self, vals):
        self.check_progress_access()
        res = super(StoreIssue, self).write(vals)
        return res

    @api.model
    def create(self, vals):
        self.check_progress_access()
        self.check_request_pending(vals)
        vals = self.default_vals_update(vals)
        res = super(StoreIssue, self).create(vals)
        self.issue_detail_creation(res)
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
    progress = fields.Char(string='Progress', compute='get_progress', store=False)

    def get_progress(self):
        for rec in self:
            rec.progress = rec.request_id.progress

    def check_stock(self):
        stock_obj = self.env['product.stock']
        store_stock = stock_obj.search([('product_id', '=', self.item_id.id),
                                        ('location_id.name', '=', 'Store'),
                                        ('uom_id', '=', self.uom_id.id)])

        reduce_quantity = store_stock.quantity - self.issuing_qty

        if reduce_quantity <= 0:
            raise exceptions.ValidationError('Error! Store Quantity is lesser than issue quantity')

    def stock_reduction(self):
        stock_obj = self.env['product.stock']

        location_stock_obj = stock_obj.search([('product_id', '=', self.item_id.id),
                                               ('location_id.name', '=', self.issue_id.location_id.id),
                                               ('uom_id', '=', self.uom_id.id)])

        store_stock = stock_obj.search([('product_id', '=', self.item_id.id),
                                        ('location_id.name', '=', 'Store'),
                                        ('uom_id', '=', self.uom_id.id)])

        # Stock Reduction
        reduce_quantity = store_stock.quantity - self.issuing_qty
        store_stock.write({'quantity': reduce_quantity})

        # Stock Addition in requested location
        add_quantity = location_stock_obj + self.issuing_qty
        location_stock_obj.write({'quantity': add_quantity})
