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
    _rec_name = 'sequence'

    sequence = fields.Char(string='Sequence', readonly=True)
    scraped_by = fields.Many2one(comodel_name='res.users', string='Scraped By', readonly=True)
    scraped_on = fields.Date(string='Scraped On', readonly=True)
    progress = fields.Selection(PROGRESS_INFO, string='Progress', default='draft')
    scrap_detail = fields.One2many(comodel_name='ss.detail', string='Store Scrap Detail', inverse_name='scrap_id')
    comment = fields.Text(string='Comment')

    # Logic Function
    def store_stock_move(self):
        store_loc = self.env['stock.location'].search([('name', '=', 'Store')])
        scrap_loc = self.env['stock.location'].search([('name', '=', 'Scrap')])
        recs = self.scrap_detail
        for rec in recs:
            rec.check_stock()

        for rec in recs:
            self.env['product.stock'].stock_move(rec.item_id, rec.uom_id, store_loc, scrap_loc, rec.quantity)

    def check_progress_access(self):
        group_list = []
        if self.progress in ['draft', False]:
            group_list = ['Hospital Store', 'Admin']

        outer_obj = self.env['check.group.access'].browse([('id', '=', 1)])
        if not outer_obj.check_group_access(group_list):
            raise exceptions.ValidationError('Error! You are not authorised to change this record')

    def create_sequence(self):
        obj = self.env['ir.sequence'].sudo()

        sequence = obj.next_by_code('store.scrap')
        period = self.env['period.period'].search([('progress', '=', 'open')])
        return '{0}/{1}'.format(sequence, period.name)

    # Button Function
    @api.multi
    def trigger_scrap(self):
        data = {
            'progress': 'scraped',
            'scraped_on': datetime.now().strftime('%Y-%m-%d'),
            'scraped_by': self.env.user.id,
            'sequence': self.create_sequence(),
        }
        self.store_stock_move()
        self.write(data)

    # Default Function
    @api.multi
    def unlink(self):
        self.check_progress_access()
        if self.sequence:
            raise exceptions.ValidationError('Error! You are not authorised to change this record')
        return super(StoreScrap, self).unlink()

    @api.multi
    def write(self, vals):
        self.check_progress_access()
        return super(StoreScrap, self).write(vals)

    @api.model
    def create(self, vals):
        self.check_progress_access()
        vals['scraped_by'] = self.env.user.id
        vals['scraped_on'] = datetime.now().strftime('%Y-%m-%d')
        return super(StoreScrap, self).create(vals)


class SSDetail(models.Model):
    _name = 'ss.detail'
    _description = 'Store Scrap Detail'

    item_id = fields.Many2one(comodel_name='product.product', string='Item', required=True)
    uom_id = fields.Many2one(comodel_name='product.uom', string='UOM', required=True)
    quantity = fields.Float(string='Quantity', required=True)
    scrap_id = fields.Many2one(comodel_name='store.scrap', string='Store Scrap')
    progress = fields.Selection(PROGRESS_INFO, string='Progress', related='scrap_id.progress')

    @api.constrains('quantity')
    def _validate_quantity(self):
        if self.quantity <= 0:
            raise exceptions.ValidationError("Quantity should be greater than 0")

    def check_stock(self):
        quantity = 0
        stock_obj = self.env['product.stock']
        store_stock = stock_obj.search([('product_id', '=', self.item_id.id),
                                        ('location_id.name', '=', 'Store'),
                                        ('uom_id', '=', self.uom_id.id)])

        if store_stock:
            quantity = store_stock.quantity - self.quantity

        if (quantity < 0) or (store_stock.quantity <= 0):
            raise exceptions.ValidationError('Error! Store Quantity is lesser than scrap quantity')

    _sql_constraints = [
        ('duplicate_product', 'unique (item_id, uom_id, scrap_id)', "Duplicate Product"),
    ]
