import json
import os
import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import models as db_models

from .models import Membro, Tarefa, Setor, Conversa, Mensagem, SolicitacaoCadastro
from .forms import FormMembro, FormTarefa, FormEditarMembro, FormSetor, FormSolicitacao, FormEditarSolicitacao

logger = logging.getLogger(__name__)


def home(request):
    return render(request, 'core/home.html')


# ---------------------------------------------------------------------------
#  Painel: 3 vias (admin / diretor / membro)
# ---------------------------------------------------------------------------

@login_required
def painel(request):
    membro, _ = Membro.objects.get_or_create(
        usuario=request.user,
        defaults={'cargo': 'presidente' if request.user.is_superuser else 'membro'},
    )

    # Admin, Diretor, Antiga Gestao -> painel_admin.html (with permission flags)
    if membro.is_admin() or membro.is_diretor() or membro.is_antiga_gestao():
        setores = Setor.objects.prefetch_related('membros__usuario', 'tarefas').all()
        membros_sem_setor = Membro.objects.filter(setor__isnull=True).select_related('usuario')
        tarefas_sem_setor = Tarefa.objects.filter(setor__isnull=True).select_related(
            'responsavel__usuario', 'criado_por'
        )
        todos_membros = Membro.objects.select_related('usuario').all()
        todas_tarefas = Tarefa.objects.select_related('responsavel__usuario', 'criado_por').all()

        # Hide admin members from non-admin users
        if membro.cargo != 'administrador':
            todos_membros = todos_membros.exclude(cargo='administrador')
            membros_sem_setor = membros_sem_setor.exclude(cargo='administrador')

        setor_ativo_id = request.GET.get('setor')
        setor_ativo = None
        if setor_ativo_id:
            setor_ativo = Setor.objects.filter(id=setor_ativo_id).first()

        # Permission flags for template
        can_create_member = membro.is_superadmin() or membro.is_diretor()
        can_edit_member = membro.is_superadmin()
        can_delete_member = membro.is_superadmin()
        can_manage_tasks = not membro.is_read_only()
        can_manage_setores = membro.is_admin()

        # Setores that this user can manage (for conditional actions in template)
        if membro.is_admin():
            setores_gerenciaveis = set(s.id for s in setores)
        elif membro.is_diretor() and membro.setor:
            setores_gerenciaveis = {membro.setor.id}
        else:
            setores_gerenciaveis = set()

        # Kanban data: pre-filter tasks by status
        todas_tarefas_pendente = todas_tarefas.filter(status='pendente')
        todas_tarefas_em_andamento = todas_tarefas.filter(status='em_andamento')
        todas_tarefas_concluida = todas_tarefas.filter(status='concluida')

        tarefas_sem_setor_pendente = tarefas_sem_setor.filter(status='pendente')
        tarefas_sem_setor_em_andamento = tarefas_sem_setor.filter(status='em_andamento')
        tarefas_sem_setor_concluida = tarefas_sem_setor.filter(status='concluida')

        # Pending registration requests count (for superadmin badge)
        solicitacoes_pendentes = 0
        if membro.is_superadmin():
            solicitacoes_pendentes = SolicitacaoCadastro.objects.filter(status='pendente').count()

        return render(request, 'core/painel_admin.html', {
            'membro': membro,
            'setores': setores,
            'setor_ativo': setor_ativo,
            'membros_sem_setor': membros_sem_setor,
            'tarefas_sem_setor': tarefas_sem_setor,
            'todos_membros': todos_membros,
            'todas_tarefas': todas_tarefas,
            'can_create_member': can_create_member,
            'can_edit_member': can_edit_member,
            'can_delete_member': can_delete_member,
            'can_manage_tasks': can_manage_tasks,
            'can_manage_setores': can_manage_setores,
            'setores_gerenciaveis': setores_gerenciaveis,
            'solicitacoes_pendentes': solicitacoes_pendentes,
            # Kanban data
            'todas_tarefas_pendente': todas_tarefas_pendente,
            'todas_tarefas_em_andamento': todas_tarefas_em_andamento,
            'todas_tarefas_concluida': todas_tarefas_concluida,
            'tarefas_sem_setor_pendente': tarefas_sem_setor_pendente,
            'tarefas_sem_setor_em_andamento': tarefas_sem_setor_em_andamento,
            'tarefas_sem_setor_concluida': tarefas_sem_setor_concluida,
        })

    # Membro -> painel_membro.html (kanban of own tasks + sector colleagues)
    else:
        tarefas = Tarefa.objects.filter(responsavel=membro).select_related('criado_por')
        tarefas_pendente = tarefas.filter(status='pendente')
        tarefas_em_andamento = tarefas.filter(status='em_andamento')
        tarefas_concluida = tarefas.filter(status='concluida')

        # Sector colleagues: directors + members in the same sector
        colegas_setor = []
        if membro.setor:
            colegas_setor = Membro.objects.filter(
                setor=membro.setor
            ).exclude(pk=membro.pk).exclude(
                cargo='administrador'
            ).select_related('usuario').order_by('cargo', 'usuario__first_name')

        return render(request, 'core/painel_membro.html', {
            'membro': membro,
            'tarefas': tarefas,
            'tarefas_pendente': tarefas_pendente,
            'tarefas_em_andamento': tarefas_em_andamento,
            'tarefas_concluida': tarefas_concluida,
            'colegas_setor': colegas_setor,
        })


# ---------------------------------------------------------------------------
#  Membros: CRUD
# ---------------------------------------------------------------------------

@login_required
def adicionar_membro(request):
    try:
        membro = request.user.membro
    except Membro.DoesNotExist:
        return redirect('home')

    if not (membro.is_superadmin() or membro.is_diretor()):
        messages.error(request, 'Você não tem permissão para adicionar membros.')
        return redirect('painel')

    if request.method == 'POST':
        form = FormMembro(request.POST, cargo_quem_cria=membro.cargo)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                email=form.cleaned_data['email'],
            )
            setor = form.cleaned_data.get('setor')
            cargo = form.cleaned_data['cargo']
            # Diretor: force cargo=membro and setor to their own
            if membro.is_diretor():
                cargo = 'membro'
                setor = membro.setor
            # Presidente/vice don't belong to a sector
            if cargo in ('presidente', 'vice_presidente'):
                setor = None
            novo_membro = Membro.objects.create(
                usuario=user,
                cargo=cargo,
                setor=setor,
            )
            # Auto-add to sector group chat
            if setor and hasattr(setor, 'conversa'):
                setor.conversa.participantes.add(novo_membro)
            messages.success(request, f'Membro {user.get_full_name() or user.username} adicionado com sucesso!')
            return redirect('painel')
    else:
        form = FormMembro(cargo_quem_cria=membro.cargo)
        # Diretor: limit setor to their own
        if membro.is_diretor() and membro.setor:
            form.fields['setor'].initial = membro.setor
            form.fields['setor'].widget = form.fields['setor'].hidden_widget()

    return render(request, 'core/adicionar_membro.html', {'form': form})


@login_required
def editar_membro(request, membro_id):
    try:
        admin = request.user.membro
    except Membro.DoesNotExist:
        return redirect('home')

    if not admin.is_superadmin():
        messages.error(request, 'Apenas o administrador pode editar membros.')
        return redirect('painel')

    membro = get_object_or_404(Membro, id=membro_id)

    setor_anterior = membro.setor

    if request.method == 'POST':
        form = FormEditarMembro(request.POST, membro_atual=membro, cargo_quem_edita=admin.cargo)
        if form.is_valid():
            membro.usuario.username = form.cleaned_data['username']
            membro.usuario.first_name = form.cleaned_data['first_name']
            membro.usuario.last_name = form.cleaned_data['last_name']
            membro.usuario.email = form.cleaned_data['email']
            nova_senha = form.cleaned_data.get('nova_senha')
            if nova_senha:
                membro.usuario.set_password(nova_senha)
            membro.usuario.save()
            membro.cargo = form.cleaned_data['cargo']
            membro.setor = form.cleaned_data.get('setor')
            # Presidente/vice don't belong to a sector
            if membro.cargo in ('presidente', 'vice_presidente'):
                membro.setor = None
            membro.save()

            # Update group chat membership
            novo_setor = membro.setor
            if setor_anterior != novo_setor:
                if setor_anterior and hasattr(setor_anterior, 'conversa'):
                    setor_anterior.conversa.participantes.remove(membro)
                if novo_setor and hasattr(novo_setor, 'conversa'):
                    novo_setor.conversa.participantes.add(membro)

            messages.success(request, f'Membro {membro.usuario.get_full_name() or membro.usuario.username} atualizado!')
            return redirect('painel')
    else:
        form = FormEditarMembro(membro_atual=membro, cargo_quem_edita=admin.cargo, initial={
            'username': membro.usuario.username,
            'first_name': membro.usuario.first_name,
            'last_name': membro.usuario.last_name,
            'email': membro.usuario.email,
            'cargo': membro.cargo,
            'setor': membro.setor,
        })

    return render(request, 'core/editar_membro.html', {'form': form, 'membro': membro})


@login_required
def excluir_membro(request, membro_id):
    try:
        admin = request.user.membro
    except Membro.DoesNotExist:
        return redirect('home')

    if not admin.is_superadmin():
        messages.error(request, 'Apenas o administrador pode excluir membros.')
        return redirect('painel')

    membro = get_object_or_404(Membro, id=membro_id)

    if membro.usuario == request.user:
        messages.error(request, 'Você não pode excluir a si mesmo.')
        return redirect('painel')

    # Protect admin members: nobody can delete an admin
    if membro.cargo == 'administrador':
        messages.error(request, 'Não é possível excluir um administrador.')
        return redirect('painel')

    if request.method == 'POST':
        nome = membro.usuario.get_full_name() or membro.usuario.username
        membro.usuario.delete()
        messages.success(request, f'Membro {nome} excluído com sucesso!')
        return redirect('painel')

    return render(request, 'core/excluir_membro.html', {'membro': membro})


# ---------------------------------------------------------------------------
#  Tarefas: CRUD
# ---------------------------------------------------------------------------

def _check_tarefa_permission(membro, tarefa, allow_assignee=False):
    """Check if membro can manage a tarefa."""
    if membro.is_read_only():
        return False
    if membro.is_admin():
        return True
    if membro.is_diretor() and membro.setor and tarefa.setor == membro.setor:
        return True
    if allow_assignee and tarefa.responsavel == membro:
        return True
    return False


@login_required
def criar_tarefa(request):
    try:
        membro = request.user.membro
    except Membro.DoesNotExist:
        return redirect('home')

    can_create = membro.is_admin() or membro.is_diretor()
    if not can_create:
        messages.error(request, 'Apenas administradores e diretores podem criar tarefas.')
        return redirect('painel')

    if request.method == 'POST':
        form = FormTarefa(request.POST)
        if form.is_valid():
            tarefa = form.save(commit=False)
            tarefa.criado_por = membro
            # Diretor: force setor to their own
            if membro.is_diretor() and membro.setor:
                tarefa.setor = membro.setor
            tarefa.save()

            # Envia notificacao por email ao responsavel
            email_responsavel = tarefa.responsavel.usuario.email
            if email_responsavel:
                try:
                    send_mail(
                        subject=f'Nova tarefa atribuída: {tarefa.titulo}',
                        message=(
                            f'Olá {tarefa.responsavel.usuario.get_full_name() or tarefa.responsavel.usuario.username},\n\n'
                            f'Uma nova tarefa foi atribuída a você no Clube de Programação.\n\n'
                            f'Tarefa: {tarefa.titulo}\n'
                            f'{f"Descrição: {tarefa.descricao}" if tarefa.descricao else ""}\n'
                            f'{f"Prazo: {tarefa.prazo.strftime("%d/%m/%Y")}" if tarefa.prazo else ""}\n\n'
                            f'Acesse o painel para mais detalhes.'
                        ),
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[email_responsavel],
                        fail_silently=True,
                    )
                except Exception:
                    logger.warning('Falha ao enviar email de notificacao para %s', email_responsavel)

            messages.success(request, f'Tarefa "{tarefa.titulo}" criada com sucesso!')
            return redirect('painel')
    else:
        form = FormTarefa()
        # Diretor: limit responsavel to their sector members
        if membro.is_diretor() and membro.setor:
            form.fields['responsavel'].queryset = Membro.objects.filter(setor=membro.setor)
            form.fields['setor'].initial = membro.setor
            form.fields['setor'].widget = form.fields['setor'].hidden_widget()

    return render(request, 'core/criar_tarefa.html', {'form': form})


@login_required
def atualizar_tarefa(request, tarefa_id):
    tarefa = get_object_or_404(Tarefa, id=tarefa_id)
    membro = request.user.membro

    if not _check_tarefa_permission(membro, tarefa, allow_assignee=True):
        messages.error(request, 'Você não tem permissão para alterar esta tarefa.')
        return redirect('painel')

    if request.method == 'POST':
        novo_status = request.POST.get('status')
        if novo_status in dict(Tarefa.STATUS_CHOICES):
            tarefa.status = novo_status
            tarefa.save()
            messages.success(request, f'Tarefa "{tarefa.titulo}" atualizada!')

    return redirect('painel')


@login_required
def editar_tarefa(request, tarefa_id):
    try:
        membro = request.user.membro
    except Membro.DoesNotExist:
        return redirect('home')

    tarefa = get_object_or_404(Tarefa, id=tarefa_id)

    if not _check_tarefa_permission(membro, tarefa):
        messages.error(request, 'Você não tem permissão para editar esta tarefa.')
        return redirect('painel')

    if request.method == 'POST':
        form = FormTarefa(request.POST, instance=tarefa)
        if form.is_valid():
            form.save()
            messages.success(request, f'Tarefa "{tarefa.titulo}" atualizada!')
            return redirect('painel')
    else:
        form = FormTarefa(instance=tarefa)

    return render(request, 'core/editar_tarefa.html', {'form': form, 'tarefa': tarefa})


@login_required
def excluir_tarefa(request, tarefa_id):
    try:
        membro = request.user.membro
    except Membro.DoesNotExist:
        return redirect('home')

    tarefa = get_object_or_404(Tarefa, id=tarefa_id)

    if not _check_tarefa_permission(membro, tarefa):
        messages.error(request, 'Você não tem permissão para excluir esta tarefa.')
        return redirect('painel')

    if request.method == 'POST':
        titulo = tarefa.titulo
        tarefa.delete()
        messages.success(request, f'Tarefa "{titulo}" excluída com sucesso!')
        return redirect('painel')

    return render(request, 'core/excluir_tarefa.html', {'tarefa': tarefa})


# ---------------------------------------------------------------------------
#  Setores: CRUD
# ---------------------------------------------------------------------------

@login_required
def criar_setor(request):
    try:
        membro = request.user.membro
    except Membro.DoesNotExist:
        return redirect('home')

    if not membro.is_admin():
        messages.error(request, 'Apenas administradores podem criar setores.')
        return redirect('painel')

    if request.method == 'POST':
        form = FormSetor(request.POST)
        if form.is_valid():
            setor = form.save()
            # Auto-create group chat for the sector
            Conversa.objects.create(
                tipo='grupo',
                nome=f'Chat - {setor.nome}',
                setor=setor,
            )
            messages.success(request, f'Setor "{setor.nome}" criado com sucesso!')
            return redirect('painel')
    else:
        form = FormSetor()

    return render(request, 'core/criar_setor.html', {'form': form})


@login_required
def editar_setor(request, setor_id):
    try:
        membro = request.user.membro
    except Membro.DoesNotExist:
        return redirect('home')

    if not membro.is_admin():
        messages.error(request, 'Apenas administradores podem editar setores.')
        return redirect('painel')

    setor = get_object_or_404(Setor, id=setor_id)

    if request.method == 'POST':
        form = FormSetor(request.POST, instance=setor)
        if form.is_valid():
            form.save()
            if hasattr(setor, 'conversa'):
                setor.conversa.nome = f'Chat - {setor.nome}'
                setor.conversa.save()
            messages.success(request, f'Setor "{setor.nome}" atualizado!')
            return redirect('painel')
    else:
        form = FormSetor(instance=setor)

    return render(request, 'core/editar_setor.html', {'form': form, 'setor': setor})


@login_required
def excluir_setor(request, setor_id):
    try:
        membro = request.user.membro
    except Membro.DoesNotExist:
        return redirect('home')

    if not membro.is_admin():
        messages.error(request, 'Apenas administradores podem excluir setores.')
        return redirect('painel')

    setor = get_object_or_404(Setor, id=setor_id)

    if request.method == 'POST':
        nome = setor.nome
        setor.delete()
        messages.success(request, f'Setor "{nome}" excluído com sucesso!')
        return redirect('painel')

    return render(request, 'core/excluir_setor.html', {'setor': setor})


# ---------------------------------------------------------------------------
#  Chat: Pages
# ---------------------------------------------------------------------------

@login_required
def chat_lista(request):
    membro = request.user.membro
    conversas = membro.conversas.prefetch_related('participantes__usuario').annotate(
        ultima_mensagem_data=db_models.Max('mensagens__data_envio')
    ).order_by(db_models.F('ultima_mensagem_data').desc(nulls_last=True))

    outros_membros = Membro.objects.exclude(pk=membro.pk).select_related('usuario')

    return render(request, 'core/chat_lista.html', {
        'membro': membro,
        'conversas': conversas,
        'outros_membros': outros_membros,
    })


@login_required
def chat_conversa(request, conversa_id):
    membro = request.user.membro
    conversa = get_object_or_404(Conversa, id=conversa_id, participantes=membro)

    mensagens = conversa.mensagens.select_related('autor__usuario').order_by('-data_envio')[:50]
    mensagens = list(reversed(mensagens))

    return render(request, 'core/chat_conversa.html', {
        'membro': membro,
        'conversa': conversa,
        'mensagens': mensagens,
        'pusher_key': os.environ.get('PUSHER_KEY', ''),
        'pusher_cluster': os.environ.get('PUSHER_CLUSTER', 'sa1'),
    })


@login_required
def chat_nova_individual(request, membro_id):
    membro = request.user.membro
    outro = get_object_or_404(Membro, id=membro_id)

    if membro == outro:
        return redirect('chat_lista')

    # Check if individual conversation already exists
    conversa = Conversa.objects.filter(
        tipo='individual',
        participantes=membro,
    ).filter(
        participantes=outro,
    ).first()

    if not conversa:
        conversa = Conversa.objects.create(tipo='individual')
        conversa.participantes.add(membro, outro)

    return redirect('chat_conversa', conversa_id=conversa.id)


# ---------------------------------------------------------------------------
#  Chat: API (JSON)
# ---------------------------------------------------------------------------

@require_POST
@login_required
def api_enviar_mensagem(request, conversa_id):
    membro = request.user.membro
    conversa = get_object_or_404(Conversa, id=conversa_id, participantes=membro)

    try:
        data = json.loads(request.body)
        conteudo = data.get('conteudo', '').strip()
    except (json.JSONDecodeError, AttributeError):
        conteudo = request.POST.get('conteudo', '').strip()

    if not conteudo:
        return JsonResponse({'error': 'Mensagem vazia'}, status=400)

    mensagem = Mensagem.objects.create(
        conversa=conversa,
        autor=membro,
        conteudo=conteudo,
    )

    event_data = {
        'id': mensagem.id,
        'autor_id': membro.id,
        'autor_nome': membro.usuario.get_full_name() or membro.usuario.username,
        'autor_iniciais': (
            (membro.usuario.first_name[:1] if membro.usuario.first_name else '?')
            + (membro.usuario.last_name[:1] if membro.usuario.last_name else '')
        ),
        'conteudo': mensagem.conteudo,
        'data_envio': mensagem.data_envio.isoformat(),
    }

    # Push via Pusher (if configured)
    pusher_app_id = os.environ.get('PUSHER_APP_ID')
    if pusher_app_id:
        try:
            import pusher as pusher_lib
            client = pusher_lib.Pusher(
                app_id=pusher_app_id,
                key=os.environ['PUSHER_KEY'],
                secret=os.environ['PUSHER_SECRET'],
                cluster=os.environ.get('PUSHER_CLUSTER', 'sa1'),
                ssl=True,
            )
            client.trigger(f'private-conversa-{conversa.id}', 'nova-mensagem', event_data)
        except Exception:
            logger.warning('Falha ao enviar evento Pusher para conversa %s', conversa.id)

    return JsonResponse({'status': 'ok', 'mensagem': event_data})


@login_required
def api_listar_mensagens(request, conversa_id):
    membro = request.user.membro
    conversa = get_object_or_404(Conversa, id=conversa_id, participantes=membro)

    before_id = request.GET.get('before')
    qs = conversa.mensagens.select_related('autor__usuario').order_by('-data_envio')

    if before_id:
        try:
            qs = qs.filter(id__lt=int(before_id))
        except (ValueError, TypeError):
            pass

    mensagens = list(qs[:30])
    mensagens.reverse()

    data = [{
        'id': m.id,
        'autor_id': m.autor.id,
        'autor_nome': m.autor.usuario.get_full_name() or m.autor.usuario.username,
        'conteudo': m.conteudo,
        'data_envio': m.data_envio.isoformat(),
    } for m in mensagens]

    return JsonResponse({'mensagens': data})


@require_POST
@login_required
def pusher_auth(request):
    membro = request.user.membro
    channel_name = request.POST.get('channel_name', '')
    socket_id = request.POST.get('socket_id', '')

    if channel_name.startswith('private-conversa-'):
        try:
            conversa_id = int(channel_name.rsplit('-', 1)[-1])
            if not Conversa.objects.filter(id=conversa_id, participantes=membro).exists():
                return JsonResponse({'error': 'Forbidden'}, status=403)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Invalid channel'}, status=403)
    else:
        return JsonResponse({'error': 'Unknown channel'}, status=403)

    pusher_app_id = os.environ.get('PUSHER_APP_ID')
    if not pusher_app_id:
        return JsonResponse({'error': 'Pusher not configured'}, status=500)

    try:
        import pusher as pusher_lib
        client = pusher_lib.Pusher(
            app_id=pusher_app_id,
            key=os.environ['PUSHER_KEY'],
            secret=os.environ['PUSHER_SECRET'],
            cluster=os.environ.get('PUSHER_CLUSTER', 'sa1'),
            ssl=True,
        )
        auth = client.authenticate(channel=channel_name, socket_id=socket_id)
        return JsonResponse(auth)
    except Exception:
        return JsonResponse({'error': 'Auth failed'}, status=500)


# ---------------------------------------------------------------------------
#  Chat: Rename / Delete
# ---------------------------------------------------------------------------

@require_POST
@login_required
def renomear_conversa(request, conversa_id):
    membro = request.user.membro
    conversa = get_object_or_404(Conversa, id=conversa_id, participantes=membro)

    # Group/sector chats: only admins can rename
    if conversa.tipo == 'grupo' and not membro.is_admin():
        messages.error(request, 'Apenas administradores podem renomear chats de grupo.')
        return redirect('chat_lista')

    novo_nome = request.POST.get('novo_nome', '').strip()
    if novo_nome:
        conversa.nome = novo_nome
        conversa.save()
        messages.success(request, 'Conversa renomeada com sucesso!')
    else:
        messages.error(request, 'O nome não pode estar vazio.')

    return redirect('chat_lista')


@require_POST
@login_required
def excluir_conversa(request, conversa_id):
    membro = request.user.membro
    conversa = get_object_or_404(Conversa, id=conversa_id, participantes=membro)

    # Group/sector chats: only admins can delete
    if conversa.tipo == 'grupo' and not membro.is_admin():
        messages.error(request, 'Apenas administradores podem excluir chats de grupo.')
        return redirect('chat_lista')

    conversa.delete()
    messages.success(request, 'Conversa excluída com sucesso!')
    return redirect('chat_lista')


# ---------------------------------------------------------------------------
#  Solicitacoes de Cadastro
# ---------------------------------------------------------------------------

def solicitar_cadastro(request):
    if request.user.is_authenticated:
        return redirect('painel')

    if request.method == 'POST':
        form = FormSolicitacao(request.POST)
        if form.is_valid():
            from django.contrib.auth.hashers import make_password
            SolicitacaoCadastro.objects.create(
                username=form.cleaned_data['username'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data.get('last_name', ''),
                email=form.cleaned_data['email'],
                senha_hash=make_password(form.cleaned_data['senha']),
            )
            messages.success(
                request,
                'Solicitação enviada com sucesso! Aguarde a aprovação de um administrador.',
            )
            return redirect('login')
    else:
        form = FormSolicitacao()

    return render(request, 'core/solicitar_cadastro.html', {'form': form})


@login_required
def listar_solicitacoes(request):
    try:
        membro = request.user.membro
    except Membro.DoesNotExist:
        return redirect('home')

    if not membro.is_superadmin():
        messages.error(request, 'Apenas o administrador pode gerenciar solicitações.')
        return redirect('painel')

    filtro = request.GET.get('status', 'pendente')
    if filtro not in ('pendente', 'aprovada', 'rejeitada'):
        filtro = 'pendente'

    solicitacoes = SolicitacaoCadastro.objects.filter(status=filtro)

    return render(request, 'core/solicitacoes.html', {
        'membro': membro,
        'solicitacoes': solicitacoes,
        'filtro_atual': filtro,
    })


@require_POST
@login_required
def aprovar_solicitacao(request, solicitacao_id):
    try:
        membro = request.user.membro
    except Membro.DoesNotExist:
        return redirect('home')

    if not membro.is_superadmin():
        messages.error(request, 'Apenas o administrador pode aprovar solicitações.')
        return redirect('painel')

    from django.utils import timezone

    solicitacao = get_object_or_404(SolicitacaoCadastro, id=solicitacao_id, status='pendente')

    # Check if username or email was taken in the meantime
    if User.objects.filter(username=solicitacao.username).exists():
        messages.error(request, f'O nome de usuário "{solicitacao.username}" já está em uso.')
        return redirect('listar_solicitacoes')
    if User.objects.filter(email=solicitacao.email).exists():
        messages.error(request, f'O e-mail "{solicitacao.email}" já está em uso.')
        return redirect('listar_solicitacoes')

    # Create User with the pre-hashed password
    user = User(
        username=solicitacao.username,
        first_name=solicitacao.first_name,
        last_name=solicitacao.last_name,
        email=solicitacao.email,
        password=solicitacao.senha_hash,
    )
    user.save()

    novo_membro = Membro.objects.create(usuario=user, cargo='membro')

    solicitacao.status = 'aprovada'
    solicitacao.data_resposta = timezone.now()
    solicitacao.respondido_por = request.user
    solicitacao.save()

    messages.success(
        request,
        f'Solicitação de {solicitacao.first_name} {solicitacao.last_name} aprovada! Membro criado.',
    )
    return redirect('listar_solicitacoes')


@require_POST
@login_required
def rejeitar_solicitacao(request, solicitacao_id):
    try:
        membro = request.user.membro
    except Membro.DoesNotExist:
        return redirect('home')

    if not membro.is_superadmin():
        messages.error(request, 'Apenas o administrador pode rejeitar solicitações.')
        return redirect('painel')

    from django.utils import timezone

    solicitacao = get_object_or_404(SolicitacaoCadastro, id=solicitacao_id, status='pendente')

    solicitacao.status = 'rejeitada'
    solicitacao.data_resposta = timezone.now()
    solicitacao.respondido_por = request.user
    solicitacao.save()

    messages.success(
        request,
        f'Solicitação de {solicitacao.first_name} {solicitacao.last_name} rejeitada.',
    )
    return redirect('listar_solicitacoes')


@require_POST
@login_required
def excluir_solicitacao(request, solicitacao_id):
    try:
        membro = request.user.membro
    except Membro.DoesNotExist:
        return redirect('home')

    if not membro.is_superadmin():
        messages.error(request, 'Apenas o administrador pode excluir solicitações.')
        return redirect('painel')

    solicitacao = get_object_or_404(SolicitacaoCadastro, id=solicitacao_id)

    if solicitacao.status == 'pendente':
        messages.error(request, 'Não é possível excluir solicitações pendentes. Aprove ou rejeite primeiro.')
        return redirect('listar_solicitacoes')

    status_anterior = solicitacao.status
    nome = f'{solicitacao.first_name} {solicitacao.last_name}'
    solicitacao.delete()

    messages.success(request, f'Solicitação de {nome} excluída do histórico.')

    from django.urls import reverse
    return redirect(f"{reverse('listar_solicitacoes')}?status={status_anterior}")


@login_required
def editar_solicitacao(request, solicitacao_id):
    try:
        membro = request.user.membro
    except Membro.DoesNotExist:
        return redirect('home')

    if not membro.is_superadmin():
        messages.error(request, 'Apenas o administrador pode editar solicitações.')
        return redirect('painel')

    solicitacao = get_object_or_404(SolicitacaoCadastro, id=solicitacao_id, status='pendente')

    if request.method == 'POST':
        form = FormEditarSolicitacao(request.POST, instance=solicitacao)
        if form.is_valid():
            form.save()
            messages.success(request, 'Solicitação atualizada com sucesso.')
            return redirect('listar_solicitacoes')
    else:
        form = FormEditarSolicitacao(instance=solicitacao)

    return render(request, 'core/editar_solicitacao.html', {
        'form': form,
        'solicitacao': solicitacao,
        'membro': membro,
    })
