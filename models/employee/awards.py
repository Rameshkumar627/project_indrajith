# -*- coding: utf-8 -*-

from odoo import api, fields, models, exceptions


class Awards(models.Model):

    _name = 'employee.awards'

    name = fields.Char(string='Name', required=True)
    employee_id = fields.Many2one(comodel_name='hospital.employee', string='Employee')
    comment = fields.Text(string='Comment')
