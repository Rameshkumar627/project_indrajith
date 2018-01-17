# -*- coding: utf-8 -*-

from odoo import api, fields, models, exceptions


class TimeSheetPolicy(models.Model):

    _name = 'time.sheet.policy'

    name = fields.Char(string='Name', required=True)
    policy = fields.Html(string='Time Sheet Policy', required=True)
    comment = fields.Text(string='Comment')
