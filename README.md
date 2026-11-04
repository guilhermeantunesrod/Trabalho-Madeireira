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

No Linux ou macOS, ative com `source .venv/bin/activate`.

## Como testar com duas abas
Abra `http://localhost:8000` em duas abas: entre como **Mestre** na primeira e como **Jogador** na segunda. O estado fica na memória do servidor, então, para testar de novo do início, reinicie o `uvicorn` e recarregue as abas.

1. **Conexão:** as duas abas mostram 120 toras, 0 tábuas e lenhadores 0/3 (`estado.sincronizado`).
2. **Recusa:** no Jogador, clique em "Construir serraria" antes de abrir a temporada. O aviso vermelho aparece só nessa aba (`operacao.recusada`).
3. **Abertura:** no Mestre, clique em "Abrir temporada". As duas abas mostram a temporada aberta (`vila.iniciada`).
4. **Produção:** sem clicar em nada, as toras sobem 12 a cada 4 segundos nas duas abas (`recurso.produzido`, causa `temporizador`).
5. **Construção:** no Jogador, clique em "Construir serraria". As duas abas mostram −60 toras, lenhadores 1/3 e o canteiro no mapa (`construcao.iniciada`).
6. **Fim da obra:** 10 segundos depois, sem clicar em nada, a serraria fica pronta, o lenhador é liberado e a produção sobe para 16 toras (`construcao.concluida`). A partir daí, cada produção também traz 2 tábuas.
7. **Encerramento:** no Mestre, clique em "Encerrar temporada". As duas abas escurecem e a produção para (`vila.encerrada`).
8. **Recusa final:** no Jogador, clique em "Construir serraria". A recusa aparece só nessa aba.

### Disputa com três abas
Reinicie o servidor e entre com um Mestre e dois Jogadores (A e B).

1. O Mestre abre a temporada. Espere o estoque chegar a 240 toras (cerca de 40 segundos).
2. A clica duas vezes em "Construir serraria", deixando lenhadores 2/3.
3. Antes de a primeira obra terminar, A e B clicam juntos em "Construir serraria".
4. Só um pedido é aceito (`construcao.iniciada`, lenhadores 3/3). O outro jogador recebe `operacao.recusada` com o motivo "Sem lenhador livre", e os lenhadores nunca passam de 3.

## Perguntas
### 1. Quais eventos o seu sistema emite e escuta?

| Quem | Emite | Escuta |
|---|---|---|
| **Servidor** (`server.py`) | `estado.sincronizado`, `vila.iniciada`, `construcao.iniciada`, `operacao.recusada`, `recurso.produzido`, `construcao.concluida`, `vila.encerrada` | `connect`, `disconnect`, `vila.abertura_solicitada`, `construcao.solicitada`, `vila.encerramento_solicitado` |
| **Cliente** (`client/index.html`) | `vila.abertura_solicitada`, `construcao.solicitada`, `vila.encerramento_solicitado` | `estado.sincronizado`, `vila.iniciada`, `construcao.iniciada`, `operacao.recusada`, `recurso.produzido`, `construcao.concluida`, `vila.encerrada` |

Os eventos terminados em `_solicitada` ou `_solicitado` são pedidos do cliente. Os outros são fatos decididos pelo servidor.

### 2. Como o sistema sabe quando deve atualizar os outros jogadores?

O servidor é o único que altera o estado. Sempre que isso acontece, seja por um pedido aceito ou por um temporizador, ele emite um fato com o estado novo. Sem `to`, o fato vai para todos os jogadores:

```python
await sio.emit("construcao.iniciada", fato("construcao.solicitada", jogador=jogadores[sid]["nome"]))
```

Quando o assunto interessa a uma pessoa só, o servidor usa `to=sid`. É o caso da recusa, que não muda o estado:

```python
await sio.emit("operacao.recusada", {"motivo": motivo, "causa": causa}, to=sid)
```

Cada cliente escuta esses fatos e copia o estado recebido, sem calcular nada por conta própria e sem perguntar ao servidor se algo mudou:

```js
ouvir("construcao.iniciada", "desconta as toras, ocupa um lenhador e desenha o canteiro da serraria", (d) => {
  atualizar(d);
  jogo.obraIniciada(d.estado);
```

### 3. Que parte do código mostra claramente o uso do paradigma orientado a eventos?

O handler de `construcao.solicitada`, em `server.py`. Ele só roda quando o evento chega, decide, e responde com outro evento. Como não há `await` entre validar e alterar o estado, dois pedidos simultâneos são decididos um de cada vez, e isso resolve a disputa:

```python
@sio.on("construcao.solicitada")
async def construcao_solicitada(sid, dados=None):
    if estado["fase"] != "aberta":
        return await recusar(sid, "A temporada não está aberta", "construcao.solicitada")
    if estado["toras"] < CUSTO:
        return await recusar(sid, "Toras insuficientes", "construcao.solicitada")
    if estado["trabalhadores"] >= estado["limite"]:
        return await recusar(sid, "Sem lenhador livre", "construcao.solicitada")
    estado["toras"] -= CUSTO
    estado["trabalhadores"] += 1
    estado["em_obra"] += 1
    await sio.emit("construcao.iniciada", fato("construcao.solicitada", jogador=jogadores[sid]["nome"]))
    sio.start_background_task(concluir_obra)
```

Esse trecho também mostra o encadeamento: o pedido gera `construcao.iniciada`, que inicia um temporizador, e ele gera `construcao.concluida` sem nenhum novo pedido. O tempo também é uma fonte de eventos:

```python
async def concluir_obra():
    await sio.sleep(TEMPO_OBRA)
    if estado["fase"] != "aberta":
        return
    estado["trabalhadores"] -= 1
    estado["em_obra"] -= 1
    estado["concluidas"] += 1
    estado["producao"] += GANHO_POR_SERRARIA
    await sio.emit("construcao.concluida", fato("construcao.iniciada (temporizador)"))
```

## Uso de IA
Usamos o Claude (Claude Code) durante o desenvolvimento, para ajudar a implementar os eventos no servidor e no cliente, adicionar os contadores por evento, conferir o projeto com o enunciado, realizar testes e como auxílio para escrever o README.

**O que mudamos e revisamos:** definimos as regras e os números próprios da Madeireira, para o resultado não ficar igual ao exemplo do kit. Testamos o resultado no navegador com duas abas (abertura, construção, produção, fim da obra e encerramento), conferindo os números e os contadores no Painel de eventos. Também comparamos o projeto com o enunciado para ver o que ainda faltava e escolhemos o que entraria em cada commit.
