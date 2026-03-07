import json
import os
import logging

from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.db import models as db_models
from django.db.models import Count
from django.views import View

from .models import Membro, Tarefa, Setor, Conversa, Mensagem, SolicitacaoCadastro, AnexoTarefa

logger = logging.getLogger(__name__)


# ============================================================================
#  Forms (movidos de forms.py)
# ============================================================================

class FormMembro(forms.Form):
    username = forms.CharField(
        max_length=150,
        label='Nome de usuário',
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'ex: joao.silva'}),
    )
    first_name = forms.CharField(
        max_length=150,
        label='Nome',
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'ex: João'}),
    )
    last_name = forms.CharField(
        max_length=150,
        label='Sobrenome',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'ex: Silva'}),
    )
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Senha inicial'}),
    )
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'ex: joao@email.com'}),
    )
    cargo = forms.ChoiceField(
        choices=Membro.CARGO_CHOICES,
        label='Cargo',
        widget=forms.Select(attrs={'class': 'form-input'}),
    )
    setor = forms.ModelChoiceField(
        queryset=Setor.objects.all(),
        label='Setor',
        required=False,
        widget=forms.Select(attrs={'class': 'form-input'}),
    )

    def __init__(self, *args, cargo_quem_cria=None, **kwargs):
        super().__init__(*args, **kwargs)
        if cargo_quem_cria == 'diretor':
            self.fields['cargo'].choices = [('membro', 'Membro')]
            self.fields['cargo'].initial = 'membro'
        elif cargo_quem_cria in ('presidente', 'vice_presidente'):
            self.fields['cargo'].choices = [
                c for c in Membro.CARGO_CHOICES if c[0] != 'administrador'
            ]

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Esse nome de usuário já existe.')
        return username


class FormEditarMembro(forms.Form):
    username = forms.CharField(
        max_length=150,
        label='Nome de usuário',
        widget=forms.TextInput(attrs={'class': 'form-input'}),
    )
    first_name = forms.CharField(
        max_length=150,
        label='Nome',
        widget=forms.TextInput(attrs={'class': 'form-input'}),
    )
    last_name = forms.CharField(
        max_length=150,
        label='Sobrenome',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input'}),
    )
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={'class': 'form-input'}),
    )
    nova_senha = forms.CharField(
        label='Nova Senha',
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Deixe em branco para manter a atual',
        }),
    )
    cargo = forms.ChoiceField(
        choices=Membro.CARGO_CHOICES,
        label='Cargo',
        widget=forms.Select(attrs={'class': 'form-input'}),
    )
    setor = forms.ModelChoiceField(
        queryset=Setor.objects.all(),
        label='Setor',
        required=False,
        widget=forms.Select(attrs={'class': 'form-input'}),
    )

    def __init__(self, *args, membro_atual=None, cargo_quem_edita=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.membro_atual = membro_atual
        if cargo_quem_edita in ('presidente', 'vice_presidente'):
            self.fields['cargo'].choices = [
                c for c in Membro.CARGO_CHOICES if c[0] != 'administrador'
            ]

    def clean_username(self):
        username = self.cleaned_data['username']
        qs = User.objects.filter(username=username)
        if self.membro_atual:
            qs = qs.exclude(pk=self.membro_atual.usuario.pk)
        if qs.exists():
            raise forms.ValidationError('Esse nome de usuário já existe.')
        return username

    def clean_nova_senha(self):
        senha = self.cleaned_data.get('nova_senha')
        if senha and len(senha) < 8:
            raise forms.ValidationError('A senha deve ter pelo menos 8 caracteres.')
        return senha


class FormTarefa(forms.ModelForm):
    class Meta:
        model = Tarefa
        fields = ['titulo', 'descricao', 'responsavel', 'prioridade', 'funcao', 'projeto', 'prazo']
        labels = {
            'titulo': 'Título',
            'descricao': 'Descrição',
            'responsavel': 'Responsável',
            'prioridade': 'Prioridade',
            'funcao': 'Função',
            'projeto': 'Projeto',
            'prazo': 'Prazo',
        }
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex: Criar página de contato'}),
            'descricao': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Descreva a tarefa...'}),
            'responsavel': forms.Select(attrs={'class': 'form-input'}),
            'prioridade': forms.Select(attrs={'class': 'form-input'}),
            'funcao': forms.Select(attrs={'class': 'form-input'}),
            'projeto': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex: Site institucional'}),
            'prazo': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-input', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['prazo'].localize = False


class FormSetor(forms.ModelForm):
    class Meta:
        model = Setor
        fields = ['nome', 'descricao']
        labels = {
            'nome': 'Nome do Setor',
            'descricao': 'Descrição',
        }
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex: Desenvolvimento'}),
            'descricao': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Descreva o setor...'}),
        }


class FormEditarSolicitacao(forms.ModelForm):
    class Meta:
        model = SolicitacaoCadastro
        fields = ['first_name', 'last_name', 'username', 'email', 'setor', 'cargo']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'username': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'setor': forms.Select(attrs={'class': 'form-input'}),
            'cargo': forms.Select(attrs={'class': 'form-input'}),
        }
        labels = {
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
            'username': 'Nome de usuário',
            'email': 'E-mail',
            'setor': 'Setor',
            'cargo': 'Cargo desejado',
        }

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Esse nome de usuário já está em uso.')
        qs = SolicitacaoCadastro.objects.filter(username=username, status='pendente')
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Já existe outra solicitação pendente com esse nome de usuário.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Esse e-mail já está em uso.')
        qs = SolicitacaoCadastro.objects.filter(email=email, status='pendente')
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Já existe outra solicitação pendente com esse e-mail.')
        return email


class FormSolicitacao(forms.Form):
    first_name = forms.CharField(
        max_length=150,
        label='Nome',
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Seu nome'}),
    )
    last_name = forms.CharField(
        max_length=150,
        label='Sobrenome',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Seu sobrenome'}),
    )
    username = forms.CharField(
        max_length=150,
        label='Nome de usuário',
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'ex: joao.silva'}),
    )
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'seu@email.com'}),
    )
    setor = forms.ModelChoiceField(
        queryset=Setor.objects.all(),
        label='Setor',
        required=False,
        widget=forms.Select(attrs={'class': 'form-input'}),
    )
    cargo = forms.ChoiceField(
        choices=Membro.CARGO_CHOICES,
        label='Cargo desejado',
        initial='membro',
        widget=forms.Select(attrs={'class': 'form-input'}),
    )
    senha = forms.CharField(
        label='Senha',
        min_length=8,
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Mínimo 8 caracteres'}),
    )
    confirmar_senha = forms.CharField(
        label='Confirmar senha',
        min_length=8,
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Repita a senha'}),
    )

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Esse nome de usuário já está em uso.')
        if SolicitacaoCadastro.objects.filter(username=username, status='pendente').exists():
            raise forms.ValidationError('Já existe uma solicitação pendente com esse nome de usuário.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Esse e-mail já está em uso.')
        if SolicitacaoCadastro.objects.filter(email=email, status='pendente').exists():
            raise forms.ValidationError('Já existe uma solicitação pendente com esse e-mail.')
        return email

    def clean(self):
        cleaned = super().clean()
        senha = cleaned.get('senha')
        confirmar = cleaned.get('confirmar_senha')
        if senha and confirmar and senha != confirmar:
            raise forms.ValidationError('As senhas não coincidem.')
        return cleaned


class FormAnexoArquivo(forms.ModelForm):
    class Meta:
        model = AnexoTarefa
        fields = ['nome', 'arquivo']
        labels = {
            'nome': 'Nome do Anexo',
            'arquivo': 'Arquivo',
        }
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: Documento de requisitos',
            }),
            'arquivo': forms.ClearableFileInput(attrs={
                'class': 'form-input',
            }),
        }

    def clean_arquivo(self):
        arquivo = self.cleaned_data.get('arquivo')
        if arquivo and hasattr(arquivo, 'size') and arquivo.size > 10 * 1024 * 1024:
            raise forms.ValidationError('O arquivo não pode exceder 10MB.')
        return arquivo


class FormAnexoLink(forms.ModelForm):
    class Meta:
        model = AnexoTarefa
        fields = ['nome', 'url']
        labels = {
            'nome': 'Nome do Link',
            'url': 'URL',
        }
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: Referência do design',
            }),
            'url': forms.URLInput(attrs={
                'class': 'form-input',
                'placeholder': 'https://...',
            }),
        }


# ============================================================================
#  Mixins
# ============================================================================

class MembroMixin:
    """Resolve self.membro via dispatch() antes de get/post."""
    membro_auto_create = False

    def dispatch(self, request, *args, **kwargs):
        if self.membro_auto_create:
            self.membro, _ = Membro.objects.get_or_create(
                usuario=request.user,
                defaults={'cargo': 'presidente' if request.user.is_superuser else 'membro'},
            )
        else:
            try:
                self.membro = request.user.membro
            except Membro.DoesNotExist:
                return redirect('home')
        perm = self.check_membro_permission()
        if perm is not None:
            return perm
        return super().dispatch(request, *args, **kwargs)

    def check_membro_permission(self):
        return None


class AdminRequiredMixin(MembroMixin):
    """Verifica is_admin(), redireciona com erro se não."""
    admin_error_message = 'Você não tem permissão para esta ação.'

    def check_membro_permission(self):
        if not self.membro.is_admin():
            messages.error(self.request, self.admin_error_message)
            return redirect('painel')
        return None


class TarefaPermissionMixin(MembroMixin):
    """Carrega tarefa por tarefa_id da URL, verifica permissão."""
    tarefa_allow_assignee = False

    def dispatch(self, request, *args, **kwargs):
        result = super().dispatch(request, *args, **kwargs)
        if isinstance(result, type(redirect('home'))):
            return result
        self.tarefa = get_object_or_404(Tarefa, id=kwargs['tarefa_id'])
        if not _check_tarefa_permission(self.membro, self.tarefa, allow_assignee=self.tarefa_allow_assignee):
            messages.error(request, 'Você não tem permissão para esta ação.')
            return redirect('painel')
        return super(MembroMixin, self).dispatch(request, *args, **kwargs)


# ============================================================================
#  Helper
# ============================================================================

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


# ============================================================================
#  Views: Home / Menu / Painel
# ============================================================================

class HomeView(View):
    def get(self, request):
        context = {}
        if request.user.is_authenticated:
            membro, _ = Membro.objects.get_or_create(
                usuario=request.user,
                defaults={'cargo': 'presidente' if request.user.is_superuser else 'membro'},
            )
            context['membro'] = membro
        return render(request, 'core/home.html', context)


class MenuView(LoginRequiredMixin, MembroMixin, View):
    membro_auto_create = True

    def get(self, request):
        solicitacoes_pendentes = 0
        if self.membro.is_admin():
            solicitacoes_pendentes = SolicitacaoCadastro.objects.filter(status='pendente').count()
        return render(request, 'core/menu.html', {
            'membro': self.membro,
            'solicitacoes_pendentes': solicitacoes_pendentes,
        })


class PainelView(LoginRequiredMixin, MembroMixin, View):
    membro_auto_create = True

    def get(self, request):
        membro = self.membro

        if membro.is_admin() or membro.is_diretor() or membro.is_antiga_gestao():
            return self._render_admin(request, membro)
        return self._render_membro(request, membro)

    def _render_admin(self, request, membro):
        setores = Setor.objects.prefetch_related('membros__usuario', 'tarefas').all()
        membros_sem_setor = Membro.objects.filter(setor__isnull=True).select_related('usuario')
        tarefas_sem_setor = Tarefa.objects.filter(setor__isnull=True).select_related(
            'responsavel__usuario', 'criado_por'
        ).annotate(anexos_count=Count('anexos'))
        todos_membros = Membro.objects.select_related('usuario', 'setor').all()
        todas_tarefas = Tarefa.objects.select_related(
            'responsavel__usuario', 'criado_por'
        ).annotate(anexos_count=Count('anexos')).all()

        if membro.cargo != 'administrador':
            todos_membros = todos_membros.exclude(cargo='administrador')
            membros_sem_setor = membros_sem_setor.exclude(cargo='administrador')

        setor_ativo_id = request.GET.get('setor')
        setor_ativo = None
        if setor_ativo_id:
            setor_ativo = Setor.objects.filter(id=setor_ativo_id).first()

        can_create_member = membro.is_admin() or membro.is_diretor()
        can_edit_member = membro.is_admin()
        can_delete_member = membro.is_admin()
        can_manage_tasks = not membro.is_read_only()
        can_manage_setores = membro.is_admin()

        if membro.is_admin():
            setores_gerenciaveis = set(s.id for s in setores)
        elif membro.is_diretor() and membro.setor:
            setores_gerenciaveis = {membro.setor.id}
        else:
            setores_gerenciaveis = set()

        todas_tarefas_pendente = todas_tarefas.filter(status='pendente')
        todas_tarefas_em_andamento = todas_tarefas.filter(status='em_andamento')
        todas_tarefas_concluida = todas_tarefas.filter(status='concluida')

        tarefas_sem_setor_pendente = tarefas_sem_setor.filter(status='pendente')
        tarefas_sem_setor_em_andamento = tarefas_sem_setor.filter(status='em_andamento')
        tarefas_sem_setor_concluida = tarefas_sem_setor.filter(status='concluida')

        solicitacoes_pendentes = 0
        if membro.is_admin():
            solicitacoes_pendentes = SolicitacaoCadastro.objects.filter(status='pendente').count()

        membros_por_cargo = []
        for cargo_key, cargo_label in Membro.CARGO_CHOICES:
            membros_cargo = todos_membros.filter(cargo=cargo_key)
            if membros_cargo.exists():
                membros_por_cargo.append((cargo_label, list(membros_cargo)))

        return render(request, 'core/painel_admin.html', {
            'membro': membro,
            'setores': setores,
            'setor_ativo': setor_ativo,
            'membros_sem_setor': membros_sem_setor,
            'tarefas_sem_setor': tarefas_sem_setor,
            'todos_membros': todos_membros,
            'membros_por_cargo': membros_por_cargo,
            'todas_tarefas': todas_tarefas,
            'can_create_member': can_create_member,
            'can_edit_member': can_edit_member,
            'can_delete_member': can_delete_member,
            'can_manage_tasks': can_manage_tasks,
            'can_manage_setores': can_manage_setores,
            'setores_gerenciaveis': setores_gerenciaveis,
            'solicitacoes_pendentes': solicitacoes_pendentes,
            'todas_tarefas_pendente': todas_tarefas_pendente,
            'todas_tarefas_em_andamento': todas_tarefas_em_andamento,
            'todas_tarefas_concluida': todas_tarefas_concluida,
            'tarefas_sem_setor_pendente': tarefas_sem_setor_pendente,
            'tarefas_sem_setor_em_andamento': tarefas_sem_setor_em_andamento,
            'tarefas_sem_setor_concluida': tarefas_sem_setor_concluida,
        })

    def _render_membro(self, request, membro):
        tarefas = Tarefa.objects.filter(responsavel=membro).select_related(
            'criado_por'
        ).annotate(anexos_count=Count('anexos'))
        tarefas_pendente = tarefas.filter(status='pendente')
        tarefas_em_andamento = tarefas.filter(status='em_andamento')
        tarefas_concluida = tarefas.filter(status='concluida')

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


# ============================================================================
#  Views: Membros CRUD
# ============================================================================

class AdicionarMembroView(LoginRequiredMixin, MembroMixin, View):
    def check_membro_permission(self):
        if not (self.membro.is_admin() or self.membro.is_diretor()):
            messages.error(self.request, 'Você não tem permissão para adicionar membros.')
            return redirect('painel')
        return None

    def get(self, request):
        form = FormMembro(cargo_quem_cria=self.membro.cargo)
        if self.membro.is_diretor() and self.membro.setor:
            form.fields['setor'].initial = self.membro.setor
            form.fields['setor'].widget = form.fields['setor'].hidden_widget()
        return render(request, 'core/adicionar_membro.html', {'form': form, 'membro': self.membro})

    def post(self, request):
        form = FormMembro(request.POST, cargo_quem_cria=self.membro.cargo)
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
            if self.membro.is_diretor():
                cargo = 'membro'
                setor = self.membro.setor
            if cargo in ('presidente', 'vice_presidente'):
                setor = None
            novo_membro = Membro.objects.create(usuario=user, cargo=cargo, setor=setor)
            if setor and hasattr(setor, 'conversa'):
                setor.conversa.participantes.add(novo_membro)
            messages.success(request, f'Membro {user.get_full_name() or user.username} adicionado com sucesso!')
            return redirect('painel')
        return render(request, 'core/adicionar_membro.html', {'form': form, 'membro': self.membro})


class EditarMembroView(LoginRequiredMixin, AdminRequiredMixin, View):
    admin_error_message = 'Você não tem permissão para editar membros.'

    def get(self, request, membro_id):
        membro_alvo = get_object_or_404(Membro, id=membro_id)
        if membro_alvo.cargo == 'administrador' and not self.membro.is_superadmin():
            messages.error(request, 'Apenas o administrador pode editar outros administradores.')
            return redirect('painel')
        form = FormEditarMembro(membro_atual=membro_alvo, cargo_quem_edita=self.membro.cargo, initial={
            'username': membro_alvo.usuario.username,
            'first_name': membro_alvo.usuario.first_name,
            'last_name': membro_alvo.usuario.last_name,
            'email': membro_alvo.usuario.email,
            'cargo': membro_alvo.cargo,
            'setor': membro_alvo.setor,
        })
        return render(request, 'core/editar_membro.html', {
            'form': form, 'membro_alvo': membro_alvo, 'membro': self.membro,
        })

    def post(self, request, membro_id):
        membro_alvo = get_object_or_404(Membro, id=membro_id)
        if membro_alvo.cargo == 'administrador' and not self.membro.is_superadmin():
            messages.error(request, 'Apenas o administrador pode editar outros administradores.')
            return redirect('painel')
        setor_anterior = membro_alvo.setor
        form = FormEditarMembro(request.POST, membro_atual=membro_alvo, cargo_quem_edita=self.membro.cargo)
        if form.is_valid():
            membro_alvo.usuario.username = form.cleaned_data['username']
            membro_alvo.usuario.first_name = form.cleaned_data['first_name']
            membro_alvo.usuario.last_name = form.cleaned_data['last_name']
            membro_alvo.usuario.email = form.cleaned_data['email']
            nova_senha = form.cleaned_data.get('nova_senha')
            if nova_senha:
                membro_alvo.usuario.set_password(nova_senha)
            membro_alvo.usuario.save()
            membro_alvo.cargo = form.cleaned_data['cargo']
            membro_alvo.setor = form.cleaned_data.get('setor')
            if membro_alvo.cargo in ('presidente', 'vice_presidente'):
                membro_alvo.setor = None
            membro_alvo.save()
            novo_setor = membro_alvo.setor
            if setor_anterior != novo_setor:
                if setor_anterior and hasattr(setor_anterior, 'conversa'):
                    setor_anterior.conversa.participantes.remove(membro_alvo)
                if novo_setor and hasattr(novo_setor, 'conversa'):
                    novo_setor.conversa.participantes.add(membro_alvo)
            messages.success(request, f'Membro {membro_alvo.usuario.get_full_name() or membro_alvo.usuario.username} atualizado!')
            return redirect('painel')
        return render(request, 'core/editar_membro.html', {
            'form': form, 'membro_alvo': membro_alvo, 'membro': self.membro,
        })


class ExcluirMembroView(LoginRequiredMixin, AdminRequiredMixin, View):
    admin_error_message = 'Você não tem permissão para excluir membros.'

    def get(self, request, membro_id):
        membro_alvo = get_object_or_404(Membro, id=membro_id)
        if membro_alvo.usuario == request.user:
            messages.error(request, 'Você não pode excluir a si mesmo.')
            return redirect('painel')
        if membro_alvo.cargo == 'administrador':
            messages.error(request, 'Não é possível excluir um administrador.')
            return redirect('painel')
        return render(request, 'core/excluir_membro.html', {
            'membro_alvo': membro_alvo, 'membro': self.membro,
        })

    def post(self, request, membro_id):
        membro_alvo = get_object_or_404(Membro, id=membro_id)
        if membro_alvo.usuario == request.user:
            messages.error(request, 'Você não pode excluir a si mesmo.')
            return redirect('painel')
        if membro_alvo.cargo == 'administrador':
            messages.error(request, 'Não é possível excluir um administrador.')
            return redirect('painel')
        nome = membro_alvo.usuario.get_full_name() or membro_alvo.usuario.username
        membro_alvo.usuario.delete()
        messages.success(request, f'Membro {nome} excluído com sucesso!')
        return redirect('painel')


# ============================================================================
#  Views: Tarefas CRUD
# ============================================================================

class CriarTarefaView(LoginRequiredMixin, MembroMixin, View):
    def check_membro_permission(self):
        if not (self.membro.is_admin() or self.membro.is_diretor()):
            messages.error(self.request, 'Apenas administradores e diretores podem criar tarefas.')
            return redirect('painel')
        return None

    def get(self, request):
        form = FormTarefa()
        if self.membro.is_diretor() and self.membro.setor:
            form.fields['responsavel'].queryset = Membro.objects.filter(setor=self.membro.setor)
        return render(request, 'core/criar_tarefa.html', {'form': form, 'membro': self.membro})

    def post(self, request):
        form = FormTarefa(request.POST)
        if form.is_valid():
            tarefa = form.save(commit=False)
            tarefa.criado_por = self.membro
            if self.membro.is_diretor() and self.membro.setor:
                tarefa.setor = self.membro.setor
            else:
                tarefa.setor = tarefa.responsavel.setor
            tarefa.save()

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
                            f'{f"Prazo: {tarefa.prazo.strftime("%d/%m/%Y")}" if tarefa.prazo else ""}\n'
                            f'{f"Prioridade: {tarefa.get_prioridade_display()}" if tarefa.prioridade else ""}\n'
                            f'{f"Função: {tarefa.get_funcao_display()}" if tarefa.funcao else ""}\n'
                            f'{f"Projeto: {tarefa.projeto}" if tarefa.projeto else ""}\n\n'
                            f'Acesse o painel para mais detalhes.'
                        ),
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[email_responsavel],
                        fail_silently=True,
                    )
                except Exception:
                    logger.warning('Falha ao enviar email de notificação para %s', email_responsavel)

            messages.success(request, f'Tarefa "{tarefa.titulo}" criada com sucesso!')
            return redirect('painel')
        return render(request, 'core/criar_tarefa.html', {'form': form, 'membro': self.membro})


class AtualizarTarefaView(LoginRequiredMixin, MembroMixin, View):
    def post(self, request, tarefa_id):
        tarefa = get_object_or_404(Tarefa, id=tarefa_id)
        if not _check_tarefa_permission(self.membro, tarefa, allow_assignee=True):
            messages.error(request, 'Você não tem permissão para alterar esta tarefa.')
            return redirect('painel')
        novo_status = request.POST.get('status')
        if novo_status in dict(Tarefa.STATUS_CHOICES):
            tarefa.status = novo_status
            tarefa.save()
            messages.success(request, f'Tarefa "{tarefa.titulo}" atualizada!')
        return redirect('painel')


class EditarTarefaView(LoginRequiredMixin, MembroMixin, View):
    def _get_tarefa(self, request, tarefa_id):
        tarefa = get_object_or_404(Tarefa, id=tarefa_id)
        if not _check_tarefa_permission(self.membro, tarefa):
            messages.error(request, 'Você não tem permissão para editar esta tarefa.')
            return None
        return tarefa

    def get(self, request, tarefa_id):
        tarefa = self._get_tarefa(request, tarefa_id)
        if tarefa is None:
            return redirect('painel')
        form = FormTarefa(instance=tarefa)
        return render(request, 'core/editar_tarefa.html', {
            'form': form, 'tarefa': tarefa, 'membro': self.membro,
        })

    def post(self, request, tarefa_id):
        tarefa = self._get_tarefa(request, tarefa_id)
        if tarefa is None:
            return redirect('painel')
        form = FormTarefa(request.POST, instance=tarefa)
        if form.is_valid():
            tarefa = form.save(commit=False)
            if self.membro.is_diretor() and self.membro.setor:
                tarefa.setor = self.membro.setor
            else:
                tarefa.setor = tarefa.responsavel.setor
            tarefa.save()
            messages.success(request, f'Tarefa "{tarefa.titulo}" atualizada!')
            return redirect('painel')
        return render(request, 'core/editar_tarefa.html', {
            'form': form, 'tarefa': tarefa, 'membro': self.membro,
        })


class ExcluirTarefaView(LoginRequiredMixin, MembroMixin, View):
    def _get_tarefa(self, request, tarefa_id):
        tarefa = get_object_or_404(Tarefa, id=tarefa_id)
        if not _check_tarefa_permission(self.membro, tarefa):
            messages.error(request, 'Você não tem permissão para excluir esta tarefa.')
            return None
        return tarefa

    def get(self, request, tarefa_id):
        tarefa = self._get_tarefa(request, tarefa_id)
        if tarefa is None:
            return redirect('painel')
        return render(request, 'core/excluir_tarefa.html', {
            'tarefa': tarefa, 'membro': self.membro,
        })

    def post(self, request, tarefa_id):
        tarefa = self._get_tarefa(request, tarefa_id)
        if tarefa is None:
            return redirect('painel')
        titulo = tarefa.titulo
        tarefa.delete()
        messages.success(request, f'Tarefa "{titulo}" excluída com sucesso!')
        return redirect('painel')


# ============================================================================
#  Views: Anexos de Tarefas CRUD
# ============================================================================

class GerenciarAnexosView(LoginRequiredMixin, MembroMixin, View):
    def _get_tarefa(self, request, tarefa_id):
        tarefa = get_object_or_404(Tarefa, id=tarefa_id)
        if not _check_tarefa_permission(self.membro, tarefa, allow_assignee=True):
            messages.error(request, 'Você não tem permissão para gerenciar anexos desta tarefa.')
            return None
        return tarefa

    def get(self, request, tarefa_id):
        tarefa = self._get_tarefa(request, tarefa_id)
        if tarefa is None:
            return redirect('painel')
        anexos = tarefa.anexos.select_related('enviado_por__usuario').all()
        return render(request, 'core/gerenciar_anexos.html', {
            'membro': self.membro,
            'tarefa': tarefa,
            'anexos': anexos,
            'form_arquivo': FormAnexoArquivo(),
            'form_link': FormAnexoLink(),
        })

    def post(self, request, tarefa_id):
        tarefa = self._get_tarefa(request, tarefa_id)
        if tarefa is None:
            return redirect('painel')
        action = request.POST.get('action', '')
        form_arquivo = FormAnexoArquivo()
        form_link = FormAnexoLink()

        if action == 'upload_arquivo':
            form_arquivo = FormAnexoArquivo(request.POST, request.FILES)
            if form_arquivo.is_valid():
                anexo = form_arquivo.save(commit=False)
                anexo.tarefa = tarefa
                anexo.tipo = 'arquivo'
                anexo.enviado_por = self.membro
                anexo.save()
                messages.success(request, f'Arquivo "{anexo.nome}" enviado com sucesso!')
                return redirect('gerenciar_anexos', tarefa_id=tarefa.id)
        elif action == 'add_link':
            form_link = FormAnexoLink(request.POST)
            if form_link.is_valid():
                anexo = form_link.save(commit=False)
                anexo.tarefa = tarefa
                anexo.tipo = 'link'
                anexo.enviado_por = self.membro
                anexo.save()
                messages.success(request, f'Link "{anexo.nome}" adicionado com sucesso!')
                return redirect('gerenciar_anexos', tarefa_id=tarefa.id)

        anexos = tarefa.anexos.select_related('enviado_por__usuario').all()
        return render(request, 'core/gerenciar_anexos.html', {
            'membro': self.membro,
            'tarefa': tarefa,
            'anexos': anexos,
            'form_arquivo': form_arquivo,
            'form_link': form_link,
        })


class EditarAnexoView(LoginRequiredMixin, MembroMixin, View):
    def _get_anexo(self, request, anexo_id):
        anexo = get_object_or_404(AnexoTarefa, id=anexo_id)
        if not _check_tarefa_permission(self.membro, anexo.tarefa, allow_assignee=True):
            messages.error(request, 'Você não tem permissão para editar este anexo.')
            return None
        return anexo

    def get(self, request, anexo_id):
        anexo = self._get_anexo(request, anexo_id)
        if anexo is None:
            return redirect('painel')
        FormClass = FormAnexoArquivo if anexo.tipo == 'arquivo' else FormAnexoLink
        form = FormClass(instance=anexo)
        return render(request, 'core/editar_anexo.html', {
            'membro': self.membro, 'tarefa': anexo.tarefa, 'anexo': anexo, 'form': form,
        })

    def post(self, request, anexo_id):
        anexo = self._get_anexo(request, anexo_id)
        if anexo is None:
            return redirect('painel')
        FormClass = FormAnexoArquivo if anexo.tipo == 'arquivo' else FormAnexoLink
        form = FormClass(request.POST, request.FILES, instance=anexo)
        if form.is_valid():
            form.save()
            messages.success(request, f'Anexo "{anexo.nome}" atualizado!')
            return redirect('gerenciar_anexos', tarefa_id=anexo.tarefa.id)
        return render(request, 'core/editar_anexo.html', {
            'membro': self.membro, 'tarefa': anexo.tarefa, 'anexo': anexo, 'form': form,
        })


class ExcluirAnexoView(LoginRequiredMixin, MembroMixin, View):
    def _get_anexo(self, request, anexo_id):
        anexo = get_object_or_404(AnexoTarefa, id=anexo_id)
        if not _check_tarefa_permission(self.membro, anexo.tarefa, allow_assignee=True):
            messages.error(request, 'Você não tem permissão para excluir este anexo.')
            return None
        return anexo

    def get(self, request, anexo_id):
        anexo = self._get_anexo(request, anexo_id)
        if anexo is None:
            return redirect('painel')
        return render(request, 'core/excluir_anexo.html', {
            'membro': self.membro, 'tarefa': anexo.tarefa, 'anexo': anexo,
        })

    def post(self, request, anexo_id):
        anexo = self._get_anexo(request, anexo_id)
        if anexo is None:
            return redirect('painel')
        nome = anexo.nome
        tarefa_id = anexo.tarefa.id
        if anexo.tipo == 'arquivo' and anexo.arquivo:
            import cloudinary.uploader
            try:
                cloudinary.uploader.destroy(str(anexo.arquivo))
            except Exception:
                logger.warning('Falha ao remover arquivo do Cloudinary: %s', anexo.arquivo)
        anexo.delete()
        messages.success(request, f'Anexo "{nome}" excluído com sucesso!')
        return redirect('gerenciar_anexos', tarefa_id=tarefa_id)


# ============================================================================
#  Views: Setores CRUD
# ============================================================================

class CriarSetorView(LoginRequiredMixin, AdminRequiredMixin, View):
    admin_error_message = 'Apenas administradores podem criar setores.'

    def get(self, request):
        form = FormSetor()
        return render(request, 'core/criar_setor.html', {'form': form, 'membro': self.membro})

    def post(self, request):
        form = FormSetor(request.POST)
        if form.is_valid():
            setor = form.save()
            Conversa.objects.create(tipo='grupo', nome=f'Chat - {setor.nome}', setor=setor)
            messages.success(request, f'Setor "{setor.nome}" criado com sucesso!')
            return redirect('painel')
        return render(request, 'core/criar_setor.html', {'form': form, 'membro': self.membro})


class EditarSetorView(LoginRequiredMixin, AdminRequiredMixin, View):
    admin_error_message = 'Apenas administradores podem editar setores.'

    def get(self, request, setor_id):
        setor = get_object_or_404(Setor, id=setor_id)
        form = FormSetor(instance=setor)
        return render(request, 'core/editar_setor.html', {
            'form': form, 'setor': setor, 'membro': self.membro,
        })

    def post(self, request, setor_id):
        setor = get_object_or_404(Setor, id=setor_id)
        form = FormSetor(request.POST, instance=setor)
        if form.is_valid():
            form.save()
            if hasattr(setor, 'conversa'):
                setor.conversa.nome = f'Chat - {setor.nome}'
                setor.conversa.save()
            messages.success(request, f'Setor "{setor.nome}" atualizado!')
            return redirect('painel')
        return render(request, 'core/editar_setor.html', {
            'form': form, 'setor': setor, 'membro': self.membro,
        })


class ExcluirSetorView(LoginRequiredMixin, AdminRequiredMixin, View):
    admin_error_message = 'Apenas administradores podem excluir setores.'

    def get(self, request, setor_id):
        setor = get_object_or_404(Setor, id=setor_id)
        return render(request, 'core/excluir_setor.html', {
            'setor': setor, 'membro': self.membro,
        })

    def post(self, request, setor_id):
        setor = get_object_or_404(Setor, id=setor_id)
        nome = setor.nome
        setor.delete()
        messages.success(request, f'Setor "{nome}" excluído com sucesso!')
        return redirect('painel')


# ============================================================================
#  Views: Chat Pages
# ============================================================================

class ChatListaView(LoginRequiredMixin, MembroMixin, View):
    def get(self, request):
        conversas = self.membro.conversas.prefetch_related('participantes__usuario').annotate(
            ultima_mensagem_data=db_models.Max('mensagens__data_envio')
        ).order_by(db_models.F('ultima_mensagem_data').desc(nulls_last=True))
        outros_membros = Membro.objects.exclude(pk=self.membro.pk).select_related('usuario')
        return render(request, 'core/chat_lista.html', {
            'membro': self.membro,
            'conversas': conversas,
            'outros_membros': outros_membros,
        })


class ChatConversaView(LoginRequiredMixin, MembroMixin, View):
    def get(self, request, conversa_id):
        conversa = get_object_or_404(Conversa, id=conversa_id, participantes=self.membro)
        mensagens = conversa.mensagens.select_related('autor__usuario').order_by('-data_envio')[:50]
        mensagens = list(reversed(mensagens))
        return render(request, 'core/chat_conversa.html', {
            'membro': self.membro,
            'conversa': conversa,
            'mensagens': mensagens,
            'pusher_key': os.environ.get('PUSHER_KEY', ''),
            'pusher_cluster': os.environ.get('PUSHER_CLUSTER', 'sa1'),
        })


class ChatNovaIndividualView(LoginRequiredMixin, MembroMixin, View):
    def get(self, request, membro_id):
        outro = get_object_or_404(Membro, id=membro_id)
        if self.membro == outro:
            return redirect('chat_lista')
        conversa = Conversa.objects.filter(
            tipo='individual', participantes=self.membro,
        ).filter(participantes=outro).first()
        if not conversa:
            conversa = Conversa.objects.create(tipo='individual')
            conversa.participantes.add(self.membro, outro)
        return redirect('chat_conversa', conversa_id=conversa.id)


# ============================================================================
#  Views: Chat API (JSON)
# ============================================================================

class ApiEnviarMensagemView(LoginRequiredMixin, MembroMixin, View):
    def post(self, request, conversa_id):
        conversa = get_object_or_404(Conversa, id=conversa_id, participantes=self.membro)
        try:
            data = json.loads(request.body)
            conteudo = data.get('conteudo', '').strip()
        except (json.JSONDecodeError, AttributeError):
            conteudo = request.POST.get('conteudo', '').strip()
        if not conteudo:
            return JsonResponse({'error': 'Mensagem vazia'}, status=400)
        mensagem = Mensagem.objects.create(
            conversa=conversa, autor=self.membro, conteudo=conteudo,
        )
        event_data = {
            'id': mensagem.id,
            'autor_id': self.membro.id,
            'autor_nome': self.membro.usuario.get_full_name() or self.membro.usuario.username,
            'autor_iniciais': (
                (self.membro.usuario.first_name[:1] if self.membro.usuario.first_name else '?')
                + (self.membro.usuario.last_name[:1] if self.membro.usuario.last_name else '')
            ),
            'conteudo': mensagem.conteudo,
            'data_envio': mensagem.data_envio.isoformat(),
        }
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


class ApiListarMensagensView(LoginRequiredMixin, MembroMixin, View):
    def get(self, request, conversa_id):
        conversa = get_object_or_404(Conversa, id=conversa_id, participantes=self.membro)
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


class PusherAuthView(LoginRequiredMixin, MembroMixin, View):
    def post(self, request):
        channel_name = request.POST.get('channel_name', '')
        socket_id = request.POST.get('socket_id', '')
        if channel_name.startswith('private-conversa-'):
            try:
                conversa_id = int(channel_name.rsplit('-', 1)[-1])
                if not Conversa.objects.filter(id=conversa_id, participantes=self.membro).exists():
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


# ============================================================================
#  Views: Chat Management
# ============================================================================

class RenomearConversaView(LoginRequiredMixin, MembroMixin, View):
    def post(self, request, conversa_id):
        conversa = get_object_or_404(Conversa, id=conversa_id, participantes=self.membro)
        if conversa.tipo == 'grupo' and not self.membro.is_admin():
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


class ExcluirConversaView(LoginRequiredMixin, MembroMixin, View):
    def post(self, request, conversa_id):
        conversa = get_object_or_404(Conversa, id=conversa_id, participantes=self.membro)
        if conversa.tipo == 'grupo' and not self.membro.is_admin():
            messages.error(request, 'Apenas administradores podem excluir chats de grupo.')
            return redirect('chat_lista')
        conversa.delete()
        messages.success(request, 'Conversa excluída com sucesso!')
        return redirect('chat_lista')


# ============================================================================
#  Views: Solicitações de Cadastro
# ============================================================================

class SolicitarCadastroView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('painel')
        form = FormSolicitacao()
        return render(request, 'core/solicitar_cadastro.html', {'form': form})

    def post(self, request):
        if request.user.is_authenticated:
            return redirect('painel')
        form = FormSolicitacao(request.POST)
        if form.is_valid():
            from django.contrib.auth.hashers import make_password
            SolicitacaoCadastro.objects.create(
                username=form.cleaned_data['username'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data.get('last_name', ''),
                email=form.cleaned_data['email'],
                setor=form.cleaned_data.get('setor'),
                cargo=form.cleaned_data.get('cargo', 'membro'),
                senha_hash=make_password(form.cleaned_data['senha']),
                senha_plain=form.cleaned_data['senha'],
            )
            messages.success(
                request,
                'Solicitação enviada com sucesso! Aguarde a aprovação de um administrador.',
            )
            return redirect('login')
        return render(request, 'core/solicitar_cadastro.html', {'form': form})


class ListarSolicitacoesView(LoginRequiredMixin, AdminRequiredMixin, View):
    admin_error_message = 'Você não tem permissão para gerenciar solicitações.'

    def get(self, request):
        filtro = request.GET.get('status', 'pendente')
        if filtro not in ('pendente', 'aprovada', 'rejeitada'):
            filtro = 'pendente'
        solicitacoes = SolicitacaoCadastro.objects.filter(status=filtro)
        return render(request, 'core/solicitacoes.html', {
            'membro': self.membro,
            'solicitacoes': solicitacoes,
            'filtro_atual': filtro,
        })


class AprovarSolicitacaoView(LoginRequiredMixin, AdminRequiredMixin, View):
    admin_error_message = 'Você não tem permissão para aprovar solicitações.'

    def post(self, request, solicitacao_id):
        from django.utils import timezone
        solicitacao = get_object_or_404(SolicitacaoCadastro, id=solicitacao_id, status='pendente')
        if User.objects.filter(username=solicitacao.username).exists():
            messages.error(request, f'O nome de usuário "{solicitacao.username}" já está em uso.')
            return redirect('listar_solicitacoes')
        if User.objects.filter(email=solicitacao.email).exists():
            messages.error(request, f'O e-mail "{solicitacao.email}" já está em uso.')
            return redirect('listar_solicitacoes')
        user = User(
            username=solicitacao.username,
            first_name=solicitacao.first_name,
            last_name=solicitacao.last_name,
            email=solicitacao.email,
            password=solicitacao.senha_hash,
        )
        user.save()
        novo_membro = Membro.objects.create(usuario=user, cargo=solicitacao.cargo or 'membro', setor=solicitacao.setor)
        if solicitacao.setor and hasattr(solicitacao.setor, 'conversa'):
            solicitacao.setor.conversa.participantes.add(novo_membro)
        solicitacao.status = 'aprovada'
        solicitacao.data_resposta = timezone.now()
        solicitacao.respondido_por = request.user
        solicitacao.senha_plain = ''
        solicitacao.save()
        messages.success(
            request,
            f'Solicitação de {solicitacao.first_name} {solicitacao.last_name} aprovada! Membro criado.',
        )
        return redirect('listar_solicitacoes')


class RejeitarSolicitacaoView(LoginRequiredMixin, AdminRequiredMixin, View):
    admin_error_message = 'Você não tem permissão para rejeitar solicitações.'

    def post(self, request, solicitacao_id):
        from django.utils import timezone
        solicitacao = get_object_or_404(SolicitacaoCadastro, id=solicitacao_id, status='pendente')
        solicitacao.status = 'rejeitada'
        solicitacao.data_resposta = timezone.now()
        solicitacao.respondido_por = request.user
        solicitacao.senha_plain = ''
        solicitacao.save()
        messages.success(
            request,
            f'Solicitação de {solicitacao.first_name} {solicitacao.last_name} rejeitada.',
        )
        return redirect('listar_solicitacoes')


class ExcluirSolicitacaoView(LoginRequiredMixin, AdminRequiredMixin, View):
    admin_error_message = 'Você não tem permissão para excluir solicitações.'

    def post(self, request, solicitacao_id):
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


class EditarSolicitacaoView(LoginRequiredMixin, AdminRequiredMixin, View):
    admin_error_message = 'Você não tem permissão para editar solicitações.'

    def get(self, request, solicitacao_id):
        solicitacao = get_object_or_404(SolicitacaoCadastro, id=solicitacao_id, status='pendente')
        form = FormEditarSolicitacao(instance=solicitacao)
        return render(request, 'core/editar_solicitacao.html', {
            'form': form, 'solicitacao': solicitacao, 'membro': self.membro,
        })

    def post(self, request, solicitacao_id):
        solicitacao = get_object_or_404(SolicitacaoCadastro, id=solicitacao_id, status='pendente')
        form = FormEditarSolicitacao(request.POST, instance=solicitacao)
        if form.is_valid():
            form.save()
            messages.success(request, 'Solicitação atualizada com sucesso.')
            return redirect('listar_solicitacoes')
        return render(request, 'core/editar_solicitacao.html', {
            'form': form, 'solicitacao': solicitacao, 'membro': self.membro,
        })
