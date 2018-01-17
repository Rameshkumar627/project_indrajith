# -*- coding: utf-8 -*-

from odoo import api, fields, models, exceptions


PROGRESS = [('wfa', 'Waiting For Approval'), ('approved', 'Approved')]


class ShiftSchedule(models.Model):

    _name = 'shift.schedule'

    name = fields.Char(string='Sequence', readonly=True)
    week_id = fields.Many2one(comodel_name='calender.week', string='Week', required=True)
    shift = fields.Many2one(comodel_name='employee.shift', string='Shift', required=True)
    schedule_detail = fields.One2many(comodel_name='hospital.employee',
                                      inverse_name='schedule_id',
                                      string='Schedule Detail')
    generator_id = fields.Many2one(comodel_name='hospital.employee', string='Approvar', readonly=True)
    approvar_id = fields.Many2one(comodel_name='hospital.employee', string='Approvar', readonly=True)
    comment = fields.Text(string='Comment')


class ScheduleDetail(models.Model):

    _name = 'schedule.detail'

    employee_id = fields.Many2one(comodel_name='hospital.employee', string='Approvar', required=True)
    schedule_id = fields.Many2one(comodel_name='shift.schedule', string='Shift Schedule')
