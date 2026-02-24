from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_convert_admin_to_presidente'),
    ]

    operations = [
        migrations.AlterField(
            model_name='membro',
            name='cargo',
            field=models.CharField(
                choices=[
                    ('presidente', 'Presidente'),
                    ('vice_presidente', 'Vice-Presidente'),
                    ('administrador', 'Administrador'),
                    ('diretor', 'Diretor'),
                    ('antiga_gestao', 'Antiga Gestão'),
                    ('membro', 'Membro'),
                ],
                default='membro',
                max_length=20,
            ),
        ),
    ]
