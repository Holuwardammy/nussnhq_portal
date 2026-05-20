import os
import django

# Set up the Django configuration environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nuss_webapp.settings')
django.setup()

from django.contrib.auth.models import User

def create_portal_admin():
    # Using your email for BOTH fields exactly as you want it
    target_email = "adeagbosheriffdeenadebayo@gmail.com"
    account_password = "Hardey@2025"
    
    # 1. Clear out any old instances to prevent "Username already exists" crashes
    User.objects.filter(username=target_email).delete()
    User.objects.filter(email=target_email).delete()
    User.objects.filter(username="admin").delete() # Clears the previous suggestion
    
    # 2. Create the clean superuser account where username == email
    user = User.objects.create_superuser(
        username=target_email,
        email=target_email,
        password=account_password
    )
    
    # 3. Double-check all admin flags are explicitly active
    user.is_staff = True
    user.is_superuser = True
    user.is_active = True
    user.save()
    
    print("--- PORTAL ADMIN SETUP ENGINE RUN COMPLETE ---")
    print(f"--> Superuser active with Username: {target_email}")

if __name__ == "__main__":
    create_portal_admin()