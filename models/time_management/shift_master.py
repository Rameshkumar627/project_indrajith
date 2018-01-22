# -*- coding: utf-8 -*-

from odoo import api, fields, models, exceptions
from datetime import datetime

PROGRESS_INFO = [('draft', 'Draft'), ('confirmed', 'Confirmed')]


class Shift(models.Model):

    _name = 'employee.shift'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    from_time = fields.Float(string='From Time', required=True)
    till_time = fields.Float(string='Till Time', required=True)
    duration = fields.Float(string='Duration', store=False, compute='get_duration')
    progress = fields.Selection(PROGRESS_INFO, string='Progress', default='draft')
    generated_by = fields.Many2one(comodel_name='hospital.employee', string='Employee', readonly=True)
    generated_on = fields.Date(string='Created Date', readonly=True)
    comments = fields.Text(string='Comment')

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

    # Access Function
    def check_progress_access(self):
        group_list = ['Time Manager', 'Admin']

        outer_obj = self.env['check.group.access'].browse([('id', '=', 1)])
        if not outer_obj.check_group_access(group_list):
            raise exceptions.ValidationError('Error! You are not authorised to change this record')

    @api.multi
    def trigger_confirm(self):
        self.write({'progress': 'confirmed'})

    @api.multi
    def unlink(self):
        self.check_progress_access()
        raise exceptions.ValidationError('Error! You are not authorised to delete this document')

    @api.multi
    def write(self, vals):
        self.check_progress_access()
        return super(Shift, self).write(vals)

    @api.model
    def create(self, vals):
        self.check_progress_access()
        vals['generated_by'] = self.env.user.id
        vals['generated_on'] = datetime.now().strftime('%Y-%m-%d')
        return super(Shift, self).create(vals)

    _sql_constraints = [
        ('duplicate_shift', 'unique (name)', "Duplicate Shift name"),
        ('duplicate_shift', 'unique (code)', "Duplicate Shift code"),
    ]