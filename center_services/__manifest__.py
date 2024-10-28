{
  'name': 'Center Services',
  'author': 'Developed by SSTC for Technical Solution Developer: Noralden Mohammed & Amal Yassir & Buthaina Mohammed ',
  'description' : """
Center Services Management Systems
==================================
With this module, Odoo helps you managing all your Services, the
contracts associated to well services, costs
and many other features necessary to the management of your center
of Service""",
  'depends': ['base','mail','web','sale_management','om_account_accountant','contacts','purchase','stock','point_of_sale'],
  'data': [
        "security/ir.model.access.csv",
        "security/security.xml",
        "data/sequence.xml",
        "data/sequenced.xml",
        "data/sequences.xml",
        "wizard/cancel_certificate_service.xml",
        "wizard/cancel_technical_service.xml",
        "wizard/cancel_device_service.xml",
        "wizard/service_report.xml",
        "wizard/cancel_immediate_service.xml",
        "view/immediate_service.xml",
        "view/device_maintenance.xml",
        "view/technical_support.xml",
        "view/service.xml",
        "view/device.xml",
        "view/connection.xml",
        "view/contact.xml",
        "view/certificate_management.xml",
        "view/account_move.xml",
        "view/certificate_service.xml",
        "view/menu.xml",
        "report/invoice.xml",

  ],
 # 'assets': {
 #         'web.assets_backend': [
 #             'center_services/static/src/css/custom_navbar.css',
 #         ],
 #     },
  'application': True,
  'installable': True,
}