# -*- coding: utf-8 -*-

from odoo import api, fields, models, exceptions
from datetime import datetime

PROGRESS = [('draft', 'Draft'), ('wfa', 'Waiting For Approval'), ('approved', 'Approved')]


class OverTime(models.Model):

    _name = 'employee.overtime'

    name = fields.Char(string='Sequence', readonly=True)
    generated_by = fields.Many2one(comodel_name='hospital.employee', string='Employee', readonly=True)
    generated_on = fields.Date(string='Created Date', readonly=True)
    approved_by = fields.Many2one(comodel_name='hospital.employee', string='Approved By', readonly=True)
    approved_on = fields.Date(string='Approved Date', readonly=True)
    progress = fields.Selection(PROGRESS, string='Progress')
    date = fields.Date(string='Date', required=True)
    from_time = fields.Float(string='From Time', required=True)
    till_time = fields.Float(string='Till Time', required=True)
    duration = fields.Float(string='Duration', store=False, compute='get_duration')
    comment = fields.Text(string='Comment')

    def get_duration(self):
        outer_obj = self.env['check.group.access'].browse([('id', '=', 1)])
        for rec in self:
            result = 0
            if (rec.till_time - rec.from_time) >= 0:
                rec.duration = rec.till_time - rec.from_time
            else:
                date = "2017-01-0{0} {1}:{2}"
                H, M = outer_obj.float_time_convert(rec.from_time)
                from_date = datetime.strptime(date.format("1", H, M), "%Y-%m-%d %H:%M")
                H, M = outer_obj.float_time_convert(rec.till_time)
                till_date = datetime.strptime(date.format("2", H, M), "%Y-%m-%d %H:%M")
                rec.duration = (till_date - from_date).seconds / 3600

    @api.multi
    def trigger_wfa(self):
        self.write({'generated_by': self.env.user.id,
                    'progress': 'wfa',
                    'generated_on': datetime.now().strftime('%Y-%m-%d')})

    @api.multi
    def trigger_approved(self):
        self.write({'approved_by': self.env.user.id,
                    'progress': 'approved',
                    'approved_on': datetime.now().strftime('%Y-%m-%d')})

    # Access Function
    def check_progress_access(self):
        group_list = []
        if self.progress in ['draft', False]:
            group_list = ['Hospital User', 'Admin']
        elif self.progress == 'wfa':
            group_list = ['Hospital HOD', 'Admin']

        outer_obj = self.env['check.group.access'].browse([('id', '=', 1)])
        if not outer_obj.check_group_access(group_list):
            raise exceptions.ValidationError('Error! You are not authorised to change this record')

    @api.multi
    def unlink(self):
        self.check_progress_access()
        raise exceptions.ValidationError('Error! You are not authorised to delete this document')

    @api.multi
    def write(self, vals):
        self.check_progress_access()
        return super(OverTime, self).write(vals)

    @api.model
    def create(self, vals):
        self.check_progress_access()
        vals['generated_by'] = self.env.user.id
        vals['generated_on'] = datetime.now().strftime('%Y-%m-%d')
        return super(OverTime, self).create(vals)
