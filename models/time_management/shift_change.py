# -*- coding: utf-8 -*-

from odoo import api, fields, models, exceptions


PROGRESS = [('wfa', 'Waiting For Approval'), ('approved', 'Approved')]


class ShiftChange(models.Model):

    _name = 'shift.change'

    name = fields.Char(string='Sequence', readonly=True)
    employee_id = fields.Many2one(comodel_name='hospital.employee', string='Employee', readonly=True)
    approvar_id = fields.Many2one(comodel_name='hospital.employee', string='Approvar', readonly=True)
    progress = fields.Selection(PROGRESS, string='Progress')
    date = fields.Date(string='Date', required=True)
    comment = fields.Text(string='Comment')
