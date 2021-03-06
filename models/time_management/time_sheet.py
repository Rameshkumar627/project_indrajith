# -*- coding: utf-8 -*-

from odoo import api, fields, models, exceptions


PROGRESS = [('wfa', 'Waiting For Approval'), ('approved', 'Approved')]
TIME_STATUS = [('on_time', 'On Time'), ('late', 'Late')]
DAY_STATUS = [('half_day', 'Half Day'), ('full_day', 'Full Day'), ('absent', 'Absent'), ('holiday', 'Holiday')]


class TimeSheet(models.Model):

    _name = 'time.sheet'

    date = fields.Date(string='Date', readonly=True)
    Progress = fields.Selection(PROGRESS, string='Progress')
    generator_id = fields.Many2one(comodel_name='hospital.employee', string='Generated By', readonly=True)
    approvar_id = fields.Many2one(comodel_name='hospital.employee', string='Approved By', readonly=True)
    sheet_detail = fields.One2many(comodel_name='time.sheet.detail',
                                   inverse_name='detail_id',
                                   string='Time Sheet Detail')


class TimeSheetDetail(models.Model):

    _name = 'time.sheet.detail'

    employee_id = fields.Many2one(comodel_name='hospital.employee', string='Employee', readonly=True)

    expected_from_time = fields.Datetime(string='Expected From Time')
    expected_till_time = fields.Datetime(string='Expected Till Time')
    expected_hours = fields.Float(string='Expected Hours', store=False)

    actual_from_time = fields.Datetime(string='Actual From Time')
    actual_till_time = fields.Datetime(string='Actual Till Time')
    actual_hours = fields.Float(string='Actual Hours', store=False)

    time_status = fields.Selection(TIME_STATUS, string='Time Status')
    day_status = fields.Selection(DAY_STATUS, string='Day Status')

    detail_id = fields.Many2one(comodel_name='time.sheet', string='Time Sheet')

