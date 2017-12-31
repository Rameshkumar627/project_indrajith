# -*- coding: utf-8 -*-

# create, write, unlink check access
# No unlink after scraped
# On creation scraped by, scraped on is noted
# On confirmation product is scraped (from location: store) to reduce stock

from odoo import fields, models, api, _, exceptions
from datetime import datetime

PROGRESS_INFO = [('draft', 'Draft'), ('scraped', 'Scraped')]


class StoreScrap(models.Model):
    _name = 'store.scrap'
    _description = 'Store Scrap'

    sequence = fields.Char(string='Sequence', readonly=True)
    scraped_by = fields.Many2one(comodel_name='res.users', string='Scraped By', readonly=True)
    scraped_on = fields.Date(string='Scraped On', readonly=True)
    progress = fields.Selection(PROGRESS_INFO, string='Progress', default='draft')
    scrap_detail = fields.One2many(comodel_name='ss.detail', string='Store Scrap Detail', inverse_name='scrap_id')
    comment = fields.Text(string='Comment')

    def default_vals_update(self, vals):
        vals['scraped_by'] = self.env.user.id
        vals['scraped_on'] = datetime.now().strftime('%Y-%m-%d')
        return vals

    # Logic Function
    def store_reduction(self):
        recs = self.scrap_detail
        for rec in recs:
            rec.stock_reduction()

    # Access Function
    def check_progress_access(self):
        group_list = []
        if self.progress in ['draft', False]:
            group_list = ['Hospital Store', 'Admin']

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

        sequence = obj.next_by_code('store.scrap')
        period = self.env['period.period'].search([('progress', '=', 'open')])
        return '{0}/{1}'.format(sequence, period.name)

    def department_sequence_creation(self):
        obj = self.env['ir.sequence'].sudo()
        if not obj.search([('code', '=', 'store.scrap')]):
            seq = {
                'name': 'Store Scrap',
                'implementation': 'standard',
                'code': 'store.scrap',
                'prefix': 'SS/',
                'padding': 4,
                'number_increment': 1,
                'use_date_range': False,
            }
            obj.create(seq)

    # Button Function
    @api.multi
    def trigger_scrap(self):
        self.check_progress_access()
        data = {
            'progress': 'scraped',
            'scraped_on': datetime.now().strftime('%Y-%m-%d'),
            'scraped_by': self.env.user.id,
            'sequence': self.create_sequence(),
        }
        self.store_reduction()
        self.write(data)

    # Default Function
    @api.multi
    def unlink(self):
        self.check_progress_access()
        if not self.progress:
            res = super(StoreScrap, self).unlink()
        else:
            raise exceptions.ValidationError('Error! You are not authorised to change this record')
        return res

    @api.multi
    def write(self, vals):
        self.check_progress_access()
        res = super(StoreScrap, self).write(vals)
        return res

    @api.model
    def create(self, vals):
        self.check_progress_access()
        vals = self.default_vals_update(vals)
        res = super(StoreScrap, self).create(vals)
        return res


class SSDetail(models.Model):
    _name = 'ss.detail'
    _description = 'Store Scrap Detail'

    item_id = fields.Many2one(comodel_name='product.product', string='Item', required=True)
    uom_id = fields.Many2one(comodel_name='product.uom', string='UOM', required=True)
    quantity = fields.Float(string='Quantity', required=True)
    scrap_id = fields.Many2one(comodel_name='store.scrap', string='Store Scrap')
    progress = fields.Char(string='Progress', compute='get_progress', store=False)

    def get_progress(self):
        for rec in self:
            rec.progress = rec.request_id.progress

    def stock_reduction(self):
        stock_obj = self.env['product.stock']
        stock = stock_obj.search([('product_id', '=', self.item_id.id),
                                  ('location_id.name', '=', 'Store'),
                                  ('uom_id', '=', self.uom_id.id)])

        quantity = stock.quantity - self.quantity
        if quantity <= 0:
            raise exceptions.ValidationError('Error! Store Quantity is lesser than scrap quantity')
        else:
            stock.write({'quantity': quantity})
