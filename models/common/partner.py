# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class Partner(models.Model):
    _name = 'hospital.partner'
    _description = 'Hospital Partner'

    name = fields.Char(string='Name')