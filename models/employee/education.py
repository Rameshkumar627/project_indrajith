# -*- coding: utf-8 -*-

from odoo import api, fields, models, exceptions


class Education(models.Model):

    _name = 'employee.education'

    name = fields.Char(string='Name', required=True)
    institution = fields.Char(string='Institution', readonly=True)
    percentage = fields.Char(string='Percentage', readonly=True)
    employee_id = fields.Many2one(comodel_name='hospital.employee', string='Employee')
    comment = fields.Text(string='Comment')
