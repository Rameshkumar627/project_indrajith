# -*- coding: utf-8 -*-

from odoo import api, fields, models, exceptions

PROGRESS_INFO = [('draft', 'Draft'), ('confirmed', 'Confirmed')]


class HospitalYear(models.Model):

    _name = 'hospital.year'

    name = fields.Char(string='Year', required=True)
