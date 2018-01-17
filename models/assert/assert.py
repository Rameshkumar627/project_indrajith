# -*- coding: utf-8 -*-


from odoo import models, fields, api, _, exceptions


class Assert(models.Model):
    _name = 'assert.assert'
    _description = 'Assert'

    name = fields.Char(string='Assert')
    sequence = fields.Char(string='Sequence')
    purchase_detail = ''
    notification_detail = ''
    service_detail = ''
    service_info = ''
    active = ''
    account_detail = ''
    product_detail = ''


class AssertPurchaseDetail(models.Model):
    _name = ''
    _description = ''


class AssertProductDetail(models.Model):
    _name = ''
    _description = ''


class AssertNotificationDetail(models.Model):
    _name = ''
    _description = ''


class AssertAccountDetail(models.Model):
    _name = ''
    _description = ''

