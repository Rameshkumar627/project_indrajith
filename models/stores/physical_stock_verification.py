# -*- coding: utf-8 -*-

# No Date-time overlap
# No Backdated record
# Update PSV Detail on button click
# All fields readonly except Actual Quantity
# Print Out
# Update Product Stock on button click
# Except fist time remaining all other time till_date is next record start date

# Workflow:
#       create------>draft
#
#       draft------->confirm
#           update: created by, created on
#           need  : from date, till date
#           check date:
#               from date > till date
#               no dates overlap
#               no dates innerlap, exterlap
#               no pending records
#               update  : sequence
#               require : actual quantity and comments (if more or less)
#       confirm----->approved
#           stock update from old value to new value

from odoo import models, fields, api, _, exceptions
from datetime import datetime

PROGRESS_INFO = [('draft', 'Draft'), ('confirmed', 'Confirmed'), ('approved', 'Approved')]


class PhysicalStockVerification(models.Model):
    _name = 'physical.stock.verification'
    _description = 'Physical Stock Verification'

    from_date = fields.Date(string='From Date', readonly=True)
    till_date = fields.Date(string='Till Date', required=True)
    sequence = fields.Char(string='Sequence', readonly=True)
    progress = fields.Selection(PROGRESS_INFO, string="Progress")
    psv_detail = fields.One2many(comodel_name='psv.detail', string='PSV Detail')

    def check_current_date(self):
        ''' No Backdated
            No Datetime Overlap '''
        from_date = datetime.strptime(self.from_date, '%Y-%m-%d')
        till_date = datetime.strptime(self.till_date, '%Y-%m-%d')
        if from_date > till_date:
            raise exceptions.ValidationError('Error! Please check date')

    def check_existing_date(self):
        recs = self.env['physical.stock.verification'].search([])

        for rec in recs:
            old_from_date = datetime.strptime(rec.from_date, '%Y-%m-%d')
            old_till_date = datetime.strptime(rec.till_date, '%Y-%m-%d')

            condition = [old_from_date > self.from_date, old_till_date > self.from_date,
                         old_from_date > self.till_date, old_till_date > self.till_date]

            for condi in condition:
                if condi:
                    raise exceptions.ValidationError('Error! Please check date')

    def check_pending_records(self):
        recs = self.env['physical.stock.verification'].search([('progress', '!=', 'approved'),
                                                               ('id', '!=', self.id)])
        if recs:
            raise exceptions.ValidationError('Error! Already one verification is pending')

    def create_psv_detail(self):
        pass

    @api.multi
    def trigger_draft(self):
        self.create_psv_detail()
        self.write({'progress': 'confirmed',
                    'sequence': 0})

    @api.multi
    def trigger_confirmed(self):
        self.check_current_date()
        self.check_existing_date()
        self.check_pending_records()
        self.write({'progress': 'confirmed'})

    @api.multi
    def trigger_approved(self):
        self.check_pending_records()
        self.update_product_stock()
        self.write({'progress': 'approved'})


class PSVDetail(models.Model):
    _name = 'psv.detail'
    _description = 'Physical Stock Verification Detail'

    product_id = fields.Many2one(comodel_name='product.product', string='Product', readonly=True)
    uom_id = fields.Many2one(comodel_name='product.uom', string='UOM', readonly=True)
    group_id = fields.Many2one(comodel_name='product.group', string='Product Group', related='product_id.group_id')
    sub_group_id = fields.Many2one(comodel_name='product.group', string='Product Sub Group',
                                   related='product_id.sub_group_id')
    location_id = fields.Many2one(comodel_name='stock.location', string='Location', readonly=True)
    available_quantity = fields.Float(string='Available Quantity', readonly=True)
    actual_quantity = fields.Float(string='Actual Quantity')
    comment = fields.Text(string='Comment')
    psv_id = fields.Many2one(comodel_name='physical.stock.verification',
                             string='Physical Stock Verification')

