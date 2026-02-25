# Sistema Administrativo - Clube de Programacao

![Django](https://img.shields.io/badge/django_6.0-%23092e20.svg?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![License](https://img.shields.io/badge/license-MIT-orange?style=for-the-badge)

Sistema web para gestao interna do Clube de Programacao. Permite que administradores, presidentes e diretores gerenciem membros, setores e tarefas, com chat em tempo real via Pusher.

## Funcionalidades

### Presidente / Vice-Presidente / Administrador
- Adicionar, editar e excluir membros do clube
- Criar, editar e excluir tarefas e atribui-las a membros
- Criar, editar e excluir setores
- Gerenciar solicitacoes de cadastro (aprovar/rejeitar)
- Visualizar todos os membros e tarefas no painel

### Diretor
- Adicionar membros ao seu setor
- Gerenciar tarefas do seu setor

### Membro
- Visualizar tarefas atribuidas em quadro Kanban
- Alterar status das suas tarefas (Pendente, Em Andamento, Concluida)

### Geral
- Autenticacao com login por username ou email
- Chat em tempo real (Pusher)
- Solicitacao de cadastro por novos membros
- Pagina inicial publica
- Interface com tema escuro

## Tecnologias

| Camada | Tecnologia |
| :--- | :--- |
| **Backend** | Python 3 + Django 6.0.2 |
| **Frontend** | HTML5, CSS3, JavaScript |
| **Banco de dados** | SQLite (dev) / PostgreSQL via Neon (prod) |
| **Deploy** | Vercel (WSGI) |
| **Arquivos estaticos** | WhiteNoise |
| **Chat em tempo real** | Pusher |

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

1. Clone o repositorio e entre na pasta
2. Crie e ative um ambiente virtual:
```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
source .venv/bin/activate # Linux/macOS
```
3. Instale as dependencias:
```bash
pip install -r requirements.txt
```
4. Copie `.env.example` para `.env` e ajuste as variaveis
5. Aplique as migracoes:
```bash
python manage.py migrate
```
6. Inicie o servidor:
```bash
python manage.py runserver
```
7. Acesse: `http://127.0.0.1:8000/`

## Licenca

Este projeto esta sob a licenca MIT.
