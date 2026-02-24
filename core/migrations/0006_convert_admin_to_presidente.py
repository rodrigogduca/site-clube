from django.db import migrations


def convert_cargo_forward(apps, schema_editor):
    Membro = apps.get_model('core', 'Membro')
    Membro.objects.filter(cargo='admin').update(cargo='presidente')


def convert_cargo_reverse(apps, schema_editor):
    Membro = apps.get_model('core', 'Membro')
    Membro.objects.filter(cargo='presidente').update(cargo='admin')


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_add_setor_chat_update_cargo'),
    ]

    operations = [
        migrations.RunPython(convert_cargo_forward, convert_cargo_reverse),
    ]
