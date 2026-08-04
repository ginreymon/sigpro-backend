# Rename tables to snake_case and django_user -> auth_user (data-preserving, sp_rename under the hood)

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0003_alter_useremployeelink_employee_local'),
    ]

    operations = [
        migrations.RenameField(
            model_name='useremployeelink',
            old_name='django_user',
            new_name='auth_user',
        ),
        migrations.AlterModelTable(
            name='useremployeelink',
            table='user_employee_link',
        ),
        migrations.AlterModelTable(
            name='passwordresettoken',
            table='password_reset_token',
        ),
    ]
