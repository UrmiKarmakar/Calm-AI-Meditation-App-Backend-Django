from django.db import migrations
from django.contrib.auth.hashers import make_password

def seed_superadmin(apps, schema_editor):
    CustomUser = apps.get_model("accounts", "CustomUser")
    if not CustomUser.objects.filter(role="superadmin").exists():
        CustomUser.objects.create(
            username="master",
            email="superadmin@example.com",
            password=make_password("supersecure"),  # change in production
            role="superadmin",
            is_verified=True,
            is_staff=True,
            is_superuser=True,
        )

class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_superadmin),
    ]
