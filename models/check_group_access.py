# -*- coding: utf-8 -*-

from odoo import fields, models, api, _, exceptions
from datetime import datetime
import math


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

    def days_in_date(self, from_date, till_date):
        if not isinstance(from_date, datetime):
            from_date = datetime.strptime(from_date, "%Y-%m-%d")
        if not isinstance(till_date, datetime):
            till_date = datetime.strptime(till_date, "%Y-%m-%d")

        return (till_date - from_date).days

    def check_date(self, from_date, till_date):
        '''Check from date < till date'''
        result = False
        if not isinstance(from_date, datetime):
            from_date = datetime.strptime(from_date, "%Y-%m-%d")
        if not isinstance(till_date, datetime):
            till_date = datetime.strptime(till_date, "%Y-%m-%d")

        if (till_date - from_date).days >= 0:
            result = True

        return result

    def float_time_convert(self, float_val):
        factor = float_val < 0 and -1 or 1
        val = abs(float_val)
        return (factor * int(math.floor(val)), int(round((val % 1) * 60)))



