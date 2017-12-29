# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

PROGRESS_INFO = [('open', 'Open'), ('closed', 'Closed')]


class Period(models.Model):
    _name = 'period.period'
    _description = 'Year Period'

    name = fields.Char(string='Name')
    progress = fields.Selection(PROGRESS_INFO, string='Progress')