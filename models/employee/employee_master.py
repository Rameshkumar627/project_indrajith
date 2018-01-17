# -*- coding: utf-8 -*-

from odoo import api, fields, models, exceptions


BLOOD_GROUP = [('a+', 'A+'), ('b+', 'B+'), ('ab+', 'AB+'), ('o+', 'O+'),
               ('a-', 'A-'), ('b-', 'B-'), ('ab-', 'AB-'), ('o-', 'O-')]
STATUS = [('draft', 'Draft'), ('confirmed', 'Confirmed')]
SEX = [('male', 'Male'), ('female', 'Female'), ('transgender', 'Transgender')]
MARITAL_STATUS = [('single', 'Single'), ('married', 'Married'), ('divorced', 'Divorced')]
TYPE = [('permanent', 'Permanent'), ('temporary', 'Temporary'), ('consultant', 'Consultant')]


class Employee(models.Model):

    _name = 'hospital.employee'

    # Official Information
    image = fields.Binary(string='Image')
    name = fields.Char(string='Employee Name', required=True)
    position = fields.Char(string='Job Position')
    is_doctor = fields.Boolean(string='Is Doctor')
    employee_uid = fields.Char(string='Employee ID')
    type_id = fields.Selection(TYPE, string='Employee Type', required=True)
    date_of_join = fields.Date(string='Date Of Joining')
    date_of_exit = fields.Date(string='Date Of Exit')
    phone_primary = fields.Char(string='Phone Primary')
    phone_secondary = fields.Char(string='Phone Secondary')
    email = fields.Char(string='Email', required=True)
    direct_reportee_id = fields.Many2one(comodel_name='hospital.employee', string='Direct Reportee', index=True)
    subordinate_ids = fields.One2many(comodel_name='hospital.employee',
                                      inverse_name='direct_reportee_id',
                                      string='Subordinates')
    date_of_birth = fields.Date(string='Date Of Birth')
    age = fields.Integer(string='Age', readonly=True)
    sex = fields.Selection(SEX, string='Sex')
    marital_status = fields.Selection(MARITAL_STATUS, string='Marital Status')
    status = fields.Selection(STATUS, default='draft', string='Status')
    permission_approvar_id = fields.Many2one(comodel_name='hospital.employee', string='Permission Approvar')
    leave_approvar_id = fields.Many2one(comodel_name='hospital.employee', string='Leave Approvar')
    overtime_approvar_id = fields.Many2one(comodel_name='hospital.employee', string='Overtime Approvar')

    # Personnel Info
    allergic_towards = fields.Char(string='Allergic Towards')
    blood_group = fields.Selection(BLOOD_GROUP, string='Blood Group')
    emergency_contact = fields.Many2one(comodel_name='human.contact', string='Emergency Contact')
    contact_address = fields.One2many(comodel_name='human.contact',
                                      inverse_name='employee_id',
                                      string='Contact Address')

    # Experience Info
    education = fields.One2many(comodel_name='employee.education',
                                inverse_name='employee_id',
                                string='Education')
    experience = fields.One2many(comodel_name='employee.experience',
                                 inverse_name='employee_id',
                                 string='Experience')
    awards = fields.One2many(comodel_name='employee.awards',
                             inverse_name='employee_id',
                             string='Awards/Certification')

    # Accounts Info
    pan = fields.Char(string='PAN', required=True)
    aadhar_card = fields.Char(string='Aadhar Card')
    driving_license = fields.Char(string='Driving License')
    bank_name = fields.Many2one(comodel_name='account.bank', string='Bank')
    account_no = fields.Char(string='Bank Account No')
    medical_insurance = fields.Char(string='Medical Insurance')

    # Documents Attached
    docs = fields.One2many(comodel_name='employee.documents',
                           inverse_name='hospital_docs_id',
                           string='Documents')

    active = fields.Boolean(string='Active', default=True)

