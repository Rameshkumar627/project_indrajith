# -*- coding: utf-8 -*-

from odoo import api, fields, models, exceptions


class Shift(models.Model):

    _name = 'employee.shift'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    from_time = fields.Float(string='From Time', required=True)
    till_time = fields.Float(string='Till Time', required=True)
    duration = fields.Float(string='Duration', store=False)
    comments = fields.Text(string='Comment')
