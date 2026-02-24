from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_remove_categoria'),
    ]

    operations = [
        migrations.RunSQL(
            sql='DROP TABLE IF EXISTS tarefas_task;',
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
