# -*- coding: utf-8 -*-

from odoo import api, fields, models, exceptions


class AccountBank(models.Model):

    _name = 'account.bank'

    name = fields.Char(string='Name', required=True)
    employee_id = fields.Many2one(comodel_name='hospital.employee', string='Employee')
    comment = fields.Text(string='Comment')
