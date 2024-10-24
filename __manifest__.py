# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'HR Equipment Maintenance',
    'author': 'prashanth',
    'version': '17.0.0.0',
    'license': 'LGPL-3',
    'category': 'Maintenance',

    'data': ['security/ir.model.access.csv',
             'data/sequence.xml',
             'data/mail_template_allocation_request.xml',
             'data/mail_template_allocation_approved.xml',
             'data/mail_template_equipment_allocated.xml',
             'data/mail_template_equipment_return.xml',
             'data/mail_template_maintenance_request.xml',
             'data/mail_template_maintenance_approved.xml',
             'views/product_template.xml',
             'views/all_allocations.xml',
             'views/maintenance_equipment.xml',
             'views/maintenance_request.xml',
             'views/equipment_transfer_wizard.xml',
             'views/damage_details.xml',
             'views/maintenance_checklist.xml',
             'views/project_task.xml',
             'views/maintenance_menuitem.xml',
             ],

    'depends': ['base',
                'maintenance',
                'account',
                'hr',
                'hr_timesheet',
                'mail',
                'stock',
                'project',
                'purchase',
                ],

    'installable': True,
    'application': True,
    'auto_install': False,
}
