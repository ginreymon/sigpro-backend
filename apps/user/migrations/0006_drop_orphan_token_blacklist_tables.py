# Drops the leftover tables of rest_framework_simplejwt.token_blacklist.
# The app was removed from INSTALLED_APPS (commit fe1e0ff) and no code uses these tables,
# so Django cannot autogenerate the drop: raw SQL it is. Child table first (it has an FK
# to outstandingtoken). The migration rows of the removed app are cleaned up as well.
# Not reversible: the dropped data (revoked/issued token logs) is not recoverable.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0005_delete_useremployeelink"),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                "DROP TABLE IF EXISTS dbo.token_blacklist_blacklistedtoken;",
                "DROP TABLE IF EXISTS dbo.token_blacklist_outstandingtoken;",
                "DELETE FROM dbo.django_migrations WHERE app = 'token_blacklist';",
            ],
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
