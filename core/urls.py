from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('painel/', views.painel, name='painel'),

    # Membros
    path('painel/adicionar-membro/', views.adicionar_membro, name='adicionar_membro'),
    path('painel/membro/<int:membro_id>/editar/', views.editar_membro, name='editar_membro'),
    path('painel/membro/<int:membro_id>/excluir/', views.excluir_membro, name='excluir_membro'),

    # Tarefas
    path('painel/criar-tarefa/', views.criar_tarefa, name='criar_tarefa'),
    path('painel/tarefa/<int:tarefa_id>/atualizar/', views.atualizar_tarefa, name='atualizar_tarefa'),
    path('painel/tarefa/<int:tarefa_id>/editar/', views.editar_tarefa, name='editar_tarefa'),
    path('painel/tarefa/<int:tarefa_id>/excluir/', views.excluir_tarefa, name='excluir_tarefa'),

    # Setores
    path('painel/criar-setor/', views.criar_setor, name='criar_setor'),
    path('painel/setor/<int:setor_id>/editar/', views.editar_setor, name='editar_setor'),
    path('painel/setor/<int:setor_id>/excluir/', views.excluir_setor, name='excluir_setor'),

    # Solicitacoes de Cadastro
    path('solicitar-cadastro/', views.solicitar_cadastro, name='solicitar_cadastro'),
    path('painel/solicitacoes/', views.listar_solicitacoes, name='listar_solicitacoes'),
    path('painel/solicitacoes/<int:solicitacao_id>/aprovar/', views.aprovar_solicitacao, name='aprovar_solicitacao'),
    path('painel/solicitacoes/<int:solicitacao_id>/rejeitar/', views.rejeitar_solicitacao, name='rejeitar_solicitacao'),
    path('painel/solicitacoes/<int:solicitacao_id>/excluir/', views.excluir_solicitacao, name='excluir_solicitacao'),
    path('painel/solicitacoes/<int:solicitacao_id>/editar/', views.editar_solicitacao, name='editar_solicitacao'),

    # Chat
    path('painel/chat/', views.chat_lista, name='chat_lista'),
    path('painel/chat/<int:conversa_id>/', views.chat_conversa, name='chat_conversa'),
    path('painel/chat/nova/<int:membro_id>/', views.chat_nova_individual, name='chat_nova_individual'),
    path('painel/chat/<int:conversa_id>/renomear/', views.renomear_conversa, name='renomear_conversa'),
    path('painel/chat/<int:conversa_id>/excluir/', views.excluir_conversa, name='excluir_conversa'),

    # Chat API
    path('api/chat/<int:conversa_id>/enviar/', views.api_enviar_mensagem, name='api_enviar_mensagem'),
    path('api/chat/<int:conversa_id>/mensagens/', views.api_listar_mensagens, name='api_listar_mensagens'),
    path('api/pusher/auth/', views.pusher_auth, name='pusher_auth'),

    # Auth
    path('accounts/login/', auth_views.LoginView.as_view(redirect_authenticated_user=True), name='login'),
    path('accounts/', include('django.contrib.auth.urls')),
]
