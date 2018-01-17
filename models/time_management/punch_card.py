# -*- coding: utf-8 -*-

from odoo import api, fields, models, exceptions


class PunchCard(models.Model):

    _name = 'punch.card'

    time = fields.Datetime(string='Date', readonly=True)
    employee_id = fields.Many2one(comodel_name='hospital.employee', string='Employee', readonly=True)
