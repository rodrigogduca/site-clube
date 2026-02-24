from django.db import models
from django.contrib.auth.models import User


class Setor(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nome']
        verbose_name_plural = 'Setores'

    def __str__(self):
        return self.nome


class Membro(models.Model):
    CARGO_CHOICES = [
        ('presidente', 'Presidente'),
        ('vice_presidente', 'Vice-Presidente'),
        ('administrador', 'Administrador'),
        ('diretor', 'Diretor'),
        ('antiga_gestao', 'Antiga Gestão'),
        ('membro', 'Membro'),
    ]

    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='membro')
    cargo = models.CharField(max_length=20, choices=CARGO_CHOICES, default='membro')
    setor = models.ForeignKey(
        Setor, on_delete=models.SET_NULL, null=True, blank=True, related_name='membros'
    )
    bio = models.TextField(blank=True)
    data_entrada = models.DateField(auto_now_add=True)

    def __str__(self):
        return f'{self.usuario.get_full_name() or self.usuario.username} ({self.get_cargo_display()})'

    def is_admin(self):
        return self.cargo in ('presidente', 'vice_presidente', 'administrador')

    def is_superadmin(self):
        return self.cargo == 'administrador'

    def is_diretor(self):
        return self.cargo == 'diretor'

    def is_antiga_gestao(self):
        return self.cargo == 'antiga_gestao'

    def is_read_only(self):
        return self.cargo == 'antiga_gestao'

    def can_manage_setor(self, setor):
        if self.is_read_only():
            return False
        if self.is_admin():
            return True
        return self.is_diretor() and self.setor == setor


class Tarefa(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('em_andamento', 'Em andamento'),
        ('concluida', 'Concluída'),
    ]

    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    responsavel = models.ForeignKey(
        Membro, on_delete=models.CASCADE, related_name='tarefas'
    )
    criado_por = models.ForeignKey(
        Membro, on_delete=models.SET_NULL, null=True, related_name='tarefas_criadas'
    )
    setor = models.ForeignKey(
        Setor, on_delete=models.SET_NULL, null=True, blank=True, related_name='tarefas'
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pendente')
    data_criacao = models.DateTimeField(auto_now_add=True)
    prazo = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.titulo

    class Meta:
        ordering = ['-data_criacao']


class Conversa(models.Model):
    TIPO_CHOICES = [
        ('individual', 'Individual'),
        ('grupo', 'Grupo'),
    ]

    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES)
    nome = models.CharField(max_length=200, blank=True)
    setor = models.OneToOneField(
        Setor, on_delete=models.CASCADE, null=True, blank=True, related_name='conversa'
    )
    participantes = models.ManyToManyField(Membro, related_name='conversas', blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']

    def __str__(self):
        if self.tipo == 'grupo' and self.nome:
            return self.nome
        return f'Conversa {self.id}'

    def get_display_name(self, for_membro=None):
        if self.tipo == 'grupo':
            if self.setor:
                return f'Chat - {self.setor.nome}'
            return self.nome or f'Grupo {self.id}'
        if for_membro:
            other = self.participantes.exclude(pk=for_membro.pk).first()
            if other:
                return other.usuario.get_full_name() or other.usuario.username
        return f'Conversa {self.id}'


class Mensagem(models.Model):
    conversa = models.ForeignKey(
        Conversa, on_delete=models.CASCADE, related_name='mensagens'
    )
    autor = models.ForeignKey(
        Membro, on_delete=models.CASCADE, related_name='mensagens_enviadas'
    )
    conteudo = models.TextField()
    data_envio = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['data_envio']

    def __str__(self):
        return f'{self.autor} - {self.conteudo[:50]}'


class SolicitacaoCadastro(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('aprovada', 'Aprovada'),
        ('rejeitada', 'Rejeitada'),
    ]

    username = models.CharField(max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField()
    senha_hash = models.CharField(max_length=128)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pendente')
    data_solicitacao = models.DateTimeField(auto_now_add=True)
    data_resposta = models.DateTimeField(null=True, blank=True)
    respondido_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ['-data_solicitacao']

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.username}) - {self.get_status_display()}'
