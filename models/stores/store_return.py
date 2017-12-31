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
    request_id = fields.Many2one(comodel_name='store.request', string='Store Request', reaquired=True)
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
        recs = self.return_detail
        for rec in recs:
            rec.check_stock()

        for rec in recs:
            rec.stock_reduction()

    @api.multi
    def trigger_issued(self):
        self.check_progress_access()
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

        sequence = obj.next_by_code('store.return')
        period = self.env['period.period'].search([('progress', '=', 'open')])
        return '{0}/{1}'.format(sequence, period.name)

    def department_sequence_creation(self):
        obj = self.env['ir.sequence'].sudo()
        if not obj.search([('code', '=', 'store.return')]):
            seq = {
                'name': 'Store Return',
                'implementation': 'standard',
                'code': 'store.return',
                'prefix': 'SRN/',
                'padding': 4,
                'number_increment': 1,
                'use_date_range': False,
            }
            obj.create(seq)

    def default_vals_update(self, vals):
        sr = self.env['store.request'].search([('id', '=', vals['request_id'])])
        vals['requested_by'] = sr.requested_by.id
        vals['requested_on'] = sr.requested_on
        vals['department_id'] = sr.department_id.id
        vals['location_id'] = sr.location_id.id

        return vals

    def return_detail_creation(self, srn):
        for rec in srn.request_id.request_detail:

            data = {
                'item_id': rec.item_id.id,
                'uom_id': rec.uom_id.id,
                'return_id': srn.id,
                }

            srn.create(data)

    @api.multi
    def unlink(self):
        self.check_progress_access()
        if not self.progress:
            res = super(StoreReturn, self).unlink()
        return res

    @api.multi
    def write(self, vals):
        self.check_progress_access()
        res = super(StoreReturn, self).write(vals)
        return res

    @api.model
    def create(self, vals):
        self.check_progress_access()
        vals = self.default_vals_update(vals)
        res = super(StoreReturn, self).create(vals)
        self.return_detail_creation(res)
        return res


class SRNDetail(models.Model):
    _name = 'srn.detail'
    _description = 'Store Return Detail'

    item_id = fields.Many2one(comodel_name='product.product', string='Item', readonly=True)
    uom_id = fields.Many2one(comodel_name='product.uom', string='UOM', readonly=True)
    returning_qty = fields.Float(string='Issuing Quantity')
    return_id = fields.Many2one(comodel_name='store.return', string='Store Return')
    progress = fields.Char(string='Progress', compute='get_progress', store=False)

    def get_progress(self):
        for rec in self:
            rec.progress = rec.request_id.progress

    def check_stock(self):
        stock_obj = self.env['product.stock']
        location_stock = stock_obj.search([('product_id', '=', self.item_id.id),
                                           ('location_id.name', '=', self.return_id.location_id.id),
                                           ('uom_id', '=', self.uom_id.id)])

        reduce_quantity = location_stock.quantity - self.returning_qty

        if reduce_quantity <= 0:
            raise exceptions.ValidationError('Error! Stock Location Quantity is lesser than Returning quantity')

    def stock_addition(self):
        stock_obj = self.env['product.stock']

        location_stock_obj = stock_obj.search([('product_id', '=', self.item_id.id),
                                               ('location_id.name', '=', self.return_id.location_id.id),
                                               ('uom_id', '=', self.uom_id.id)])

        store_stock = stock_obj.search([('product_id', '=', self.item_id.id),
                                        ('location_id.name', '=', 'Store'),
                                        ('uom_id', '=', self.uom_id.id)])

        # Stock Addition in Store
        add_quantity = store_stock.quantity + self.returning_qty
        store_stock.write({'quantity': add_quantity})

        # Stock Reduction in requested location
        reduce_quantity = location_stock_obj - self.returning_qty
        location_stock_obj.write({'quantity': reduce_quantity})
