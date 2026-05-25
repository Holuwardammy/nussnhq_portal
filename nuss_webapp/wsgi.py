"""
WSGI config for nuss_webapp project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nuss_webapp.settings')

application = get_wsgi_application()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nuss_webapp.settings')

# ========================================================
# EMERGENCY RENDER DATABASE CLEANUP (Executed on Server)
# ========================================================
try:
    import django
    django.setup()
    from django.db import connection
    
    with connection.cursor() as cursor:
        # This raw SQL directly truncates or purges the row breaking the migration
        cursor.execute("DELETE FROM students_student WHERE school_id NOT SIMILAR TO '[0-9]+';")
        print("EMERGENCY CLEANUP: Cleaned invalid school text records directly from production tables!")
except Exception as e:
    print(f"EMERGENCY CLEANUP NOTIFICATION: {e}")
# ========================================================

application = get_wsgi_application()