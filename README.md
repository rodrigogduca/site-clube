# Sistema Administrativo - Clube de Programacao

![Django](https://img.shields.io/badge/django_6.0-%23092e20.svg?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![License](https://img.shields.io/badge/license-MIT-orange?style=for-the-badge)

Sistema web para gestao interna do Clube de Programacao. Permite que administradores gerenciem membros e atribuam tarefas, enquanto membros acompanham suas tarefas em um quadro Kanban.

## Funcionalidades

### Administrador
- Adicionar, editar e excluir membros do clube
- Criar, editar e excluir tarefas e atribui-las a membros
- Visualizar todos os membros e todas as tarefas no painel
- Alterar status de qualquer tarefa (Pendente, Em andamento, Concluida)

### Membro
- Visualizar apenas as tarefas atribuidas a si em um quadro Kanban (estilo Trello)
- Colunas: **Pendente**, **Em Andamento** e **Concluida**
- Alterar o status das suas proprias tarefas

### Geral
- Autenticacao com login/logout (Django auth)
- Notificacao por e-mail ao responsavel quando uma nova tarefa e atribuida
- Pagina inicial publica com informacoes sobre o clube
- Interface com tema escuro (dark theme)

## Tecnologias

| Camada | Tecnologia |
| :--- | :--- |
| **Backend** | Python 3 + Django 6.0.2 |
| **Frontend** | HTML5, CSS3, JavaScript |
| **Banco de dados** | SQLite (desenvolvimento) |
| **Servidor de arquivos estaticos** | WhiteNoise |
| **Variaveis de ambiente** | python-dotenv |

## Estrutura do Projeto

```
clube-programacao/
├── manage.py
├── requirements.txt
├── .env                        # Variaveis de ambiente (nao versionado)
├── .env.example
│
├── clube_de_programacao/       # Configuracoes do Django
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── core/                       # App principal
│   ├── models.py               # Modelos Membro e Tarefa
│   ├── views.py                # Views do painel, CRUD de membros e tarefas
│   ├── forms.py                # Formularios (FormMembro, FormTarefa, FormEditarMembro)
│   ├── urls.py                 # Rotas da aplicacao
│   ├── admin.py                # Registro dos modelos no Django Admin
│   ├── migrations/
│   ├── static/
│   │   ├── core/css/           # Estilos (home, login, painel)
│   │   ├── core/images/        # Logo e imagens
│   │   └── core/js/            # Scripts (modal da home)
│   └── templates/
│       ├── core/               # Templates do app (home, paineis, formularios)
│       └── registration/       # Template de login
│
└── tarefas/                    # App legado (nao utilizado ativamente)
```

## Modelos de Dados

### Membro
- `usuario` — OneToOneField para o User do Django
- `cargo` — `admin` ou `membro`
- `bio` — texto opcional
- `data_entrada` — preenchido automaticamente

### Tarefa
- `titulo`, `descricao`
- `responsavel` — ForeignKey para Membro
- `criado_por` — ForeignKey para Membro (quem criou)
- `status` — `pendente`, `em_andamento` ou `concluida`
- `prazo` — data opcional
- `data_criacao` — preenchido automaticamente

## Rotas Principais

| URL | Descricao |
| :--- | :--- |
| `/` | Pagina inicial publica |
| `/accounts/login/` | Login |
| `/painel/` | Painel (admin ou membro, conforme cargo) |
| `/painel/adicionar-membro/` | Adicionar membro (admin) |
| `/painel/criar-tarefa/` | Criar tarefa (admin) |
| `/painel/membro/<id>/editar/` | Editar membro (admin) |
| `/painel/membro/<id>/excluir/` | Excluir membro (admin) |
| `/painel/tarefa/<id>/editar/` | Editar tarefa (admin) |
| `/painel/tarefa/<id>/excluir/` | Excluir tarefa (admin) |
| `/painel/tarefa/<id>/atualizar/` | Atualizar status da tarefa |

## Como Executar

### Pre-requisitos
- Python 3.10 ou superior
- Git

### Passo a Passo

1. Clone o repositorio:
```bash
git clone https://github.com/rodrigogduca/clube-de-programacao.git
cd clube-de-programacao
```

2. Crie e ative um ambiente virtual:

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux/macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Instale as dependencias:
```bash
pip install -r requirements.txt
```

4. Configure as variaveis de ambiente:
   - Copie `.env.example` para `.env`
   - Ajuste `SECRET_KEY` e `DEBUG` conforme necessario

5. Aplique as migracoes:
```bash
python manage.py migrate
```

6. Crie um superusuario (sera automaticamente admin):
```bash
python manage.py createsuperuser
```

7. Inicie o servidor:
```bash
python manage.py runserver
```

8. Acesse no navegador: `http://127.0.0.1:8000/`

## Configuracao de E-mail

Por padrao, os e-mails sao exibidos no console do servidor (backend `console`). Para enviar e-mails reais, configure no `.env`:

```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-de-app
DEFAULT_FROM_EMAIL=Clube de Programacao <seu-email@gmail.com>
```

## Licenca

Este projeto esta sob a licenca MIT.
