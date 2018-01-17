# -*- coding: utf-8 -*-

from odoo import api, fields, models, exceptions


class Contact(models.Model):

    _name = 'hospital.contact'

    name = fields.Char(string='Name', required=True)
    address = fields.Text(string='Address')
    phone = fields.Char(string='Phone')
    email = fields.Char(string='Email')
    employee_id = fields.Many2one(comodel_name='hospital.employee', string='Employee')
    comment = fields.Text(string='Comment')
