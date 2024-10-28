{
    'name': 'Fleet Management Dashboard',
    'version': '1.0',
    'category': 'Fleet',
    'summary': 'Manage fleet vehicles, fuel usage, and services',
    'description': """
        Fleet Management Dashboard
        ==========================
        Manage fleet vehicles, track fuel usage, driver info, and vehicle costs.
    """,
    'author': 'Your Name',
    'depends': ['base', 'spreadsheet_dashboard'],
    'data': [
        'views/fleet_views.xml',
        'views/dashboard.xml',
    ],
    'installable': True,
    'auto_install': False,
}
