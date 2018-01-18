# -*- coding: utf-8 -*-

# stock move from location to store described in store request
# No unlink after sequence
# create, write, unlink needs access
# check stock before reduction(reduction in location, addition in store)
# On creation update requested by, requested on, department, location, product and already issued quantity

from odoo import fields, models, api, _, exceptions
from datetime import datetime

PROGRESS_INFO = [('draft', 'Draft'), ('returned', 'Returned')]


class StoreReturn(models.Model):
    _name = 'store.return'
    _description = 'Store Return'

    sequence = fields.Char(string='Sequence', readonly=True)
    request_id = fields.Many2one(comodel_name='store.request',
                                 domain='[("progress", "=", "closed")]',
                                 string='Store Request',
                                 required=True)
    department_id = fields.Many2one(comodel_name='hospital.department', string='Department', readonly=True)
    location_id = fields.Many2one(comodel_name='stock.location', string='Location', readonly=True)
    requested_by = fields.Many2one(comodel_name='res.users', string='Requested By', readonly=True)
    requested_on = fields.Date(string='Requested On', readonly=True)
    returned_by = fields.Many2one(comodel_name='res.users', string='Returned By', readonly=True)
    returned_on = fields.Date(string='Returned On', readonly=True)
    progress = fields.Selection(PROGRESS_INFO, default='draft', string='Progress')
    return_detail = fields.One2many(comodel_name='srn.detail',
                                    string='Store Return Detail',
                                    inverse_name='return_id')
    comment = fields.Text(string='Comment')

    # Logic Function
    def stock_reduction(self):
        store_loc = self.env['stock.location'].search([('name', '=', 'Store')])
        return_loc = self.location_id
        recs = self.return_detail
        for rec in recs:
            rec.check_stock()

        for rec in recs:
            self.env['product.stock'].stock_move(rec.item_id, rec.uom_id, return_loc, store_loc, rec.returning_qty)

    # Button Action
    @api.multi
    def trigger_return(self):
        self.stock_reduction()
        data = {
            'progress': 'returned',
            'returned_by': self.env.user.id,
            'returned_on': datetime.now().strftime('%Y-%m-%d'),
            'sequence': self.create_sequence()
        }
        self.write(data)

    def check_progress_access(self):
        group_list = []
        if self.progress in ['draft', 'returned']:
            group_list = ['Store User', 'Admin']

        outer_obj = self.env['check.group.access'].browse([('id', '=', 1)])
        if not outer_obj.check_group_access(group_list):
            raise exceptions.ValidationError('Error! You are not authorised to change this record')

    def create_sequence(self):
        obj = self.env['ir.sequence'].sudo()

        sequence = obj.next_by_code('store.return')
        period = self.env['period.period'].search([('progress', '=', 'open')])
        return '{0}/{1}'.format(sequence, period.name)

    def default_vals_update(self, vals):
        sr = self.env['store.request'].search([('id', '=', vals['request_id'])])
        vals['requested_by'] = sr.requested_by.id
        vals['requested_on'] = sr.requested_on
        vals['department_id'] = sr.department_id.id
        vals['location_id'] = sr.location_id.id

        for rec in sr.request_detail:
            vals['return_detail'].append((0, 0, self.return_detail_data(vals['request_id'], rec.item_id.id,
                                                                        rec.uom_id.id)))

        return vals

    def return_detail_data(self, request_id, item_id, uom_id):
        already_return_qty = already_issued_qty = 0
        returneds = self.env['srn.detail'].search([('return_id.request_id', '=', request_id),
                                                   ('item_id', '=', item_id),
                                                   ('uom_id', '=', uom_id,)])

        for returned in returneds:
            already_return_qty = already_return_qty + returned.returning_qty

        issues = self.env['si.detail'].search([('issue_id.request_id', '=', request_id),
                                               ('item_id', '=', item_id),
                                               ('uom_id', '=', uom_id,)])

        for issue in issues:
            already_issued_qty = already_issued_qty + issue.issuing_qty

        data = {'item_id': item_id,
                'uom_id': uom_id,
                'issued_qty': already_issued_qty,
                'already_return_qty': already_return_qty}

        return data

    def check_request_pending(self, vals):
        recs = self.env['store.return'].search([('request_id', '=', vals['request_id']),
                                                ('progress', '!=', 'returned')])
        if recs:
            raise exceptions.ValidationError('Error! Already one return pending')

    # Default Action
    @api.multi
    def unlink(self):
        self.check_progress_access()
        if self.sequence:
            raise exceptions.ValidationError('Error! You are not authorised to change this record')
        return super(StoreReturn, self).unlink()

    @api.multi
    def write(self, vals):
        self.check_progress_access()
        if 'request_id' in vals:
            raise exceptions.ValidationError('Error! You cannot change store request selection after creation')
        return super(StoreReturn, self).write(vals)

    @api.model
    def create(self, vals):
        self.check_progress_access()
        self.check_request_pending(vals)
        vals = self.default_vals_update(vals)
        return super(StoreReturn, self).create(vals)


class SRNDetail(models.Model):
    _name = 'srn.detail'
    _description = 'Store Return Detail'

    item_id = fields.Many2one(comodel_name='product.product', string='Item', readonly=True)
    uom_id = fields.Many2one(comodel_name='product.uom', string='UOM', readonly=True)
    already_return_qty = fields.Float(string='Already Return Quantity', readonly=True)
    issued_qty = fields.Float(string='Issued Quantity', readonly=True)
    returning_qty = fields.Float(string='Returning Quantity')
    return_id = fields.Many2one(comodel_name='store.return', string='Store Return')
    progress = fields.Selection(PROGRESS_INFO, string='Progress', related='return_id.progress')

    @api.constrains('returning_qty')
    def _validate_quantity(self):
        if (self.already_return_qty + self.returning_qty) > self.issued_qty:
            raise exceptions.ValidationError("Quantity should not be greater than issued quantity")

    def check_stock(self):
        quantity = 0
        stock_obj = self.env['product.stock']
        location_stock = stock_obj.search([('product_id', '=', self.item_id.id),
                                           ('location_id.name', '=', self.return_id.location_id.id),
                                           ('uom_id', '=', self.uom_id.id)])

        quantity = location_stock.quantity - self.returning_qty

        if (quantity < 0) or (location_stock.quantity <= 0):
            raise exceptions.ValidationError('Error! Available Quantity is lesser than return quantity')
