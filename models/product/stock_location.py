# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class StockLocation(models.Model):
    _name = 'stock.location'
    _description = 'Stock Location'

    name = fields.Char(string='Location')

