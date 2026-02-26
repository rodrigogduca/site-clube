# Sistema Administrativo - Clube de Programação

![Django](https://img.shields.io/badge/django_6.0-%23092e20.svg?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![License](https://img.shields.io/badge/license-MIT-orange?style=for-the-badge)

Sistema web para gestão interna do Clube de Programação. Permite que administradores, presidentes e diretores gerenciem membros, setores e tarefas, com chat em tempo real via Pusher.

## Funcionalidades

### Presidente / Vice-Presidente / Administrador
- Adicionar, editar e excluir membros do clube
- Criar, editar e excluir tarefas e atribuí-las a membros
- Criar, editar e excluir setores
- Gerenciar solicitações de cadastro (aprovar/rejeitar)
- Visualizar a senha informada pelo solicitante antes de aprovar
- Visualizar todos os membros e tarefas no painel

### Diretor
- Adicionar membros ao seu setor
- Gerenciar tarefas do seu setor

### Membro
- Visualizar tarefas atribuídas em quadro Kanban
- Alterar status das suas tarefas (Pendente, Em Andamento, Concluída)

### Geral
- Autenticação com login por username ou email
- Solicitação de cadastro por novos membros (com aprovação)
- Recuperação de senha via email (requer configuração SMTP)
- Chat em tempo real (Pusher)
- Página inicial pública com efeito visual fullscreen
- Interface com tema escuro

### Segurança
- Presidente e vice não podem editar ou excluir o administrador
- Senha do solicitante é apagada após aprovação ou rejeição
- Sessões via cookies assinados (sem dependência de banco para sessões)
- CSRF e HSTS configuráveis para produção
- Login por username ou email via backend customizado

## Tecnologias

| Camada | Tecnologia |
| :--- | :--- |
| **Backend** | Python 3 + Django 6.0.2 |
| **Frontend** | HTML5, CSS3, JavaScript |
| **Banco de dados** | SQLite (dev) / PostgreSQL via Neon (prod) |
| **Deploy** | Vercel (WSGI) |
| **Arquivos estáticos** | WhiteNoise |
| **Chat em tempo real** | Pusher |

## Cargos e Permissões

| Cargo | Membros | Tarefas | Setores | Solicitações |
| :--- | :---: | :---: | :---: | :---: |
| **Administrador** | Tudo | Tudo | Tudo | Tudo |
| **Presidente** | Tudo* | Tudo | Tudo | Tudo |
| **Vice-Presidente** | Tudo* | Tudo | Tudo | Tudo |
| **Diretor** | Adicionar | Seu setor | - | - |
| **Membro** | - | Suas tarefas | - | - |

\* Não pode editar ou excluir o administrador.

## Estrutura do Projeto

```
clube-programacao/
├── manage.py
├── requirements.txt
├── vercel.json
├── .env.example
├── clube_de_programacao/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── core/
    ├── models.py
    ├── views.py
    ├── forms.py
    ├── urls.py
    ├── admin.py
    ├── backends.py
    ├── apps.py
    ├── migrations/
    ├── templatetags/
    ├── static/
    │   ├── css/
    │   ├── images/
    │   └── js/
    └── templates/
        ├── core/
        └── registration/
```

## Como Executar

1. Clone o repositório e entre na pasta
2. Crie e ative um ambiente virtual:
```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
source .venv/bin/activate # Linux/macOS
```
3. Instale as dependências:
```bash
pip install -r requirements.txt
```
4. Copie `.env.example` para `.env` e ajuste as variáveis
5. Aplique as migrações:
```bash
python manage.py migrate
```
6. Inicie o servidor:
```bash
python manage.py runserver
```
7. Acesse: `http://127.0.0.1:8000/`

## Variáveis de Ambiente

Consulte `.env.example` para a lista completa. As principais são:

| Variável | Descrição |
| :--- | :--- |
| `SECRET_KEY` | Chave secreta do Django (obrigatória em produção) |
| `DEBUG` | Modo debug (True/False) |
| `DATABASE_URL` | URL do banco de dados |
| `ALLOWED_HOSTS` | Hosts permitidos, separados por vírgula |
| `EMAIL_BACKEND` | Backend de email do Django |
| `EMAIL_HOST_USER` | Email para envio (Gmail SMTP) |
| `EMAIL_HOST_PASSWORD` | Senha de app do Google |
| `PUSHER_APP_ID` / `PUSHER_KEY` / `PUSHER_SECRET` | Credenciais do Pusher |

## Licença

Este projeto está sob a licença MIT.
