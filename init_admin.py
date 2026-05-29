import os
import django

# Initialize Django environment settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings') # Change 'core' to your project name if different
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

if username and password:
    if not User.objects.filter(username=username).exists():
        print(f"Creating superuser for {username}...")
        User.objects.create_superuser(username=username, email=email, password=password)
        print("Superuser created successfully!")
    else:
        print("Superuser already exists. Skipping.")
else:
    print("Superuser environment variables missing. Skipping.")