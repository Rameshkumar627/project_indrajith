# -*- coding: utf-8 -*-

from odoo import api, fields, models, exceptions


class Experience(models.Model):

    _name = 'employee.experience'

    name = fields.Char(string='Company Name', required=True)
    position = fields.Char(string='Job Position', required=True)
    from_date = fields.Date(string='From Date', required=True)
    till_date = fields.Date(string='Till Date', required=True)
    relieving_reason = fields.Text(string='Relieving Reason')
    employee_id = fields.Many2one(comodel_name='hospital.employee', string='Employee')
    comment = fields.Text(string='Comment')
