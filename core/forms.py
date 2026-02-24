from django import forms
from django.contrib.auth.models import User
from .models import Membro, Tarefa, Setor, SolicitacaoCadastro


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
        fields = ['titulo', 'descricao', 'responsavel', 'setor', 'prazo']
        labels = {
            'titulo': 'Título',
            'descricao': 'Descrição',
            'responsavel': 'Responsável',
            'setor': 'Setor',
            'prazo': 'Prazo',
        }
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex: Criar página de contato'}),
            'descricao': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Descreva a tarefa...'}),
            'responsavel': forms.Select(attrs={'class': 'form-input'}),
            'setor': forms.Select(attrs={'class': 'form-input'}),
            'prazo': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-input', 'type': 'date'}),
        }


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
        fields = ['first_name', 'last_name', 'username', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'username': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
        }
        labels = {
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
            'username': 'Nome de usuário',
            'email': 'E-mail',
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
