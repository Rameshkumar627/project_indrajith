# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class Users(models.Model):
    _inherit = 'res.users'
    _description = 'Hospital Department'

    department_id = fields.Many2one(comodel_name='hospital.department', string='Department')
