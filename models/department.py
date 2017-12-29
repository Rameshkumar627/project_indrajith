# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class Department(models.Model):
    _name = 'hospital.department'
    _description = 'Hospital Department'

    name = fields.Char(string='Name')
