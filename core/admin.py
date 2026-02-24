from django.contrib import admin
from .models import Membro, Tarefa, Setor, Conversa, Mensagem

admin.site.register(Membro)
admin.site.register(Tarefa)
admin.site.register(Setor)
admin.site.register(Conversa)
admin.site.register(Mensagem)
