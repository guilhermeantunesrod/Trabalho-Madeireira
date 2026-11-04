# Vila em Tempo Real — Madeireira

## Integrantes
- Guilherme Antunes Rodrigues — @guilhermeantunesrod
- Samuel Frare — @samuelpavanello-cyber

## Linguagem e bibliotecas
- **Servidor:** Python 3, com `python-socketio` e `uvicorn`.
- **Cliente:** Vue 3, Socket.IO e Phaser 3, carregados por CDN (vêm do Kit Inicial, nada a instalar).

## Como instalar e executar
É preciso ter o Python 3 instalado. Na pasta do projeto:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn server:app --reload
```

Depois, abra `http://localhost:8000` no navegador (não abra o arquivo `index.html` direto).

Se o Windows não encontrar o comando `python`, use `py -m venv .venv`. Se o PowerShell bloquear o `activate`, rode antes `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.

Para os comandos de ativação em Linux ou macOS, use `source .venv/bin/activate`.

## Como testar com duas abas
(Passo a passo: quem entra como Mestre, quem entra como Jogador, o que clicar e o que deve aparecer.)

## Perguntas
1. Quais eventos o seu sistema emite e escuta?
2. Como o sistema sabe quando deve atualizar os outros jogadores?
3. Que parte do código mostra claramente o uso do paradigma orientado a eventos?

## Uso de IA
(O que usou e o que mudou. Se não usou: "Não utilizei IA".)
