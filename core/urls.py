from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('menu/', views.MenuView.as_view(), name='menu'),
    path('painel/', views.PainelView.as_view(), name='painel'),

    # Membros
    path('painel/adicionar-membro/', views.AdicionarMembroView.as_view(), name='adicionar_membro'),
    path('painel/membro/<int:membro_id>/editar/', views.EditarMembroView.as_view(), name='editar_membro'),
    path('painel/membro/<int:membro_id>/excluir/', views.ExcluirMembroView.as_view(), name='excluir_membro'),

    # Tarefas
    path('painel/criar-tarefa/', views.CriarTarefaView.as_view(), name='criar_tarefa'),
    path('painel/tarefa/<int:tarefa_id>/atualizar/', views.AtualizarTarefaView.as_view(), name='atualizar_tarefa'),
    path('painel/tarefa/<int:tarefa_id>/editar/', views.EditarTarefaView.as_view(), name='editar_tarefa'),
    path('painel/tarefa/<int:tarefa_id>/excluir/', views.ExcluirTarefaView.as_view(), name='excluir_tarefa'),

    # Anexos de Tarefas
    path('painel/tarefa/<int:tarefa_id>/anexos/', views.GerenciarAnexosView.as_view(), name='gerenciar_anexos'),
    path('painel/anexo/<int:anexo_id>/editar/', views.EditarAnexoView.as_view(), name='editar_anexo'),
    path('painel/anexo/<int:anexo_id>/excluir/', views.ExcluirAnexoView.as_view(), name='excluir_anexo'),

    # Setores
    path('painel/criar-setor/', views.CriarSetorView.as_view(), name='criar_setor'),
    path('painel/setor/<int:setor_id>/editar/', views.EditarSetorView.as_view(), name='editar_setor'),
    path('painel/setor/<int:setor_id>/excluir/', views.ExcluirSetorView.as_view(), name='excluir_setor'),

    # Solicitacoes de Cadastro
    path('solicitar-cadastro/', views.SolicitarCadastroView.as_view(), name='solicitar_cadastro'),
    path('painel/solicitacoes/', views.ListarSolicitacoesView.as_view(), name='listar_solicitacoes'),
    path('painel/solicitacoes/<int:solicitacao_id>/aprovar/', views.AprovarSolicitacaoView.as_view(), name='aprovar_solicitacao'),
    path('painel/solicitacoes/<int:solicitacao_id>/rejeitar/', views.RejeitarSolicitacaoView.as_view(), name='rejeitar_solicitacao'),
    path('painel/solicitacoes/<int:solicitacao_id>/excluir/', views.ExcluirSolicitacaoView.as_view(), name='excluir_solicitacao'),
    path('painel/solicitacoes/<int:solicitacao_id>/editar/', views.EditarSolicitacaoView.as_view(), name='editar_solicitacao'),

    # Chat
    path('painel/chat/', views.ChatListaView.as_view(), name='chat_lista'),
    path('painel/chat/<int:conversa_id>/', views.ChatConversaView.as_view(), name='chat_conversa'),
    path('painel/chat/nova/<int:membro_id>/', views.ChatNovaIndividualView.as_view(), name='chat_nova_individual'),
    path('painel/chat/<int:conversa_id>/renomear/', views.RenomearConversaView.as_view(), name='renomear_conversa'),
    path('painel/chat/<int:conversa_id>/excluir/', views.ExcluirConversaView.as_view(), name='excluir_conversa'),

    # Chat API
    path('api/chat/<int:conversa_id>/enviar/', views.ApiEnviarMensagemView.as_view(), name='api_enviar_mensagem'),
    path('api/chat/<int:conversa_id>/mensagens/', views.ApiListarMensagensView.as_view(), name='api_listar_mensagens'),
    path('api/pusher/auth/', views.PusherAuthView.as_view(), name='pusher_auth'),

    # Auth
    path('accounts/login/', auth_views.LoginView.as_view(redirect_authenticated_user=True), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
]
