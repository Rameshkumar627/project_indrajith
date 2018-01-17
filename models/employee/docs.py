# -*- coding: utf-8 -*-

from odoo import api, fields, models, exceptions


class EmployeeDocs(models.Model):

    _name = 'employee.docs'

    name = fields.Char(string='Name', required=True)
    docs = fields.Binary(string='Attachment', required=True)
    employee_id = fields.Many2one(comodel_name='hospital.employee', string='Employee')
    comment = fields.Text(string='Comment')
