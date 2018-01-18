# -*- coding: utf-8 -*-

from odoo import fields, models, api, _, exceptions


class CheckGroupAccess(models.Model):
    _name = 'check.group.access'
    _description = 'Check Group Access'

    name = fields.Char(string='Name')

    def check_group_access(self, group_list):
        ''' Check if current user in the group list return True'''
        group_ids = self.env.user.groups_id
        status = False
        for group in group_ids:
            if group.name in group_list:
                status = True
        return status

    def store_request_sequence_creation(self, department_id):
        obj = self.env['ir.sequence'].sudo()
        if not obj.search([('code', '=', 'store.request.{0}'.format(department_id.name))]):
            seq = {
                'name': 'store.request.{0}'.format(department_id.name),
                'implementation': 'standard',
                'code': 'store.request.{0}'.format(department_id.name),
                'prefix': 'SR/{0}/'.format(str(department_id.name)),
                'padding': 4,
                'number_increment': 1,
                'use_date_range': False,
            }
            obj.create(seq)



