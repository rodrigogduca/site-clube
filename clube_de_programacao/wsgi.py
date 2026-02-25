import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clube_de_programacao.settings')

application = get_wsgi_application()
app = application
