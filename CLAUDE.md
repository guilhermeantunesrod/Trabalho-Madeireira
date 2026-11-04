# CLAUDE.md — Vila em Tempo Real (Trabalho 01 · LPP · Programação Orientada a Eventos)

Instruções para o Claude desenvolver este trabalho. Leia tudo antes de qualquer tarefa.

**Regra principal: faça só o que o enunciado exige. Nada além.** Sem extras, sem refatorações, sem bibliotecas novas, sem testes automatizados, sem banco, sem login, sem deploy. Se algo não estiver aqui, pergunte antes.

---

## 0. Dados do trabalho (o usuário preenche — se estiver vazio, PERGUNTE antes de começar)

- **Tipo de vila sorteado:** **Madeireira (nº 1)** — toras → tábuas; construções: serraria, depósito, cabana; trabalhadores: lenhadores (detalhes na seção 6)
- **Modalidade:** dupla (por isso os contadores por evento são obrigatórios; os dois integrantes devem fazer commits)
- **Integrantes:** Guilherme Antunes Rodrigues e Samuel Frare (o @GitHub de cada um ainda falta: perguntar antes do README)
- **Nome do repositório:** `lpp-trabalho01-guilherme-samuel` (ou outro no formato `lpp-trabalho01-nome1-nome2`), minúsculas, sem acento
- **Entrega:** 04/11/2026 — commits depois do prazo não contam.

---

## 1. O que é o trabalho

App web em tempo real, estilo vila cooperativa. Vários jogadores na mesma vila; o **servidor decide** e **todos veem o resultado na hora**, sem recarregar a página. O que é avaliado é o **paradigma orientado a eventos** (emit / on / reagir), não o visual.

- **Mestre**: abre e encerra a temporada.
- **Jogador**: constrói.
- O servidor produz recurso sozinho a cada intervalo (temporizador) e a obra termina sozinha após alguns segundos (temporizador).
- Falta de recurso/trabalhador ou temporada fechada → **recusa só para quem pediu**.
- Dois jogadores pedindo o último recurso/trabalhador ao mesmo tempo → **só um consegue**.

---

## 2. Stack (não mudar)

- **Servidor: Python 3** com `python-socketio` (AsyncServer, `async_mode="asgi"`) + `uvicorn`. Só isso no `requirements.txt`.
- **Cliente:** o `client/index.html` do kit (Vue 3 + Socket.IO + Phaser 3 por CDN). Não criar build, não instalar nada de JS.
- Estado **só na memória** do servidor.

Executar:
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn server:app --reload
```
Abrir `http://localhost:8000` (nunca `file://`). Testar com duas ou três abas.

---

## 3. Estrutura (é a do kit — não criar outras pastas/arquivos)

```
client/index.html       # tela: preencher ESCUTAS e PEDIDOS
client/assets/          # mapa e sprites (não mexer)
server.py               # todo o servidor, em um arquivo só
docs/especificacao.md   # preencher ANTES do código
requirements.txt
README.md
.gitignore
CLAUDE.md
```

---

## 4. Eventos (catálogo mínimo)

Padrão de nomes: `objeto.acao_no_passado` = **fato** do servidor; `objeto.acao_solicitada` = **pedido** do cliente.

| Evento | Emite | Recebe | O que faz |
|---|---|---|---|
| `estado.sincronizado` | Servidor | Só quem conectou (`to=sid`) | Entrega o estado atual (causa: `conexao`) |
| `vila.abertura_solicitada` | Mestre | Servidor | Pedido para abrir |
| `vila.iniciada` | Servidor | Todos | Fase vira `aberta`, inicia o temporizador de produção |
| `construcao.solicitada` | Jogador | Servidor | Pedido para construir (nada muda) |
| `construcao.iniciada` | Servidor | Todos | Debita custo, ocupa 1 trabalhador, `em_obra += 1`, inicia temporizador da obra |
| `operacao.recusada` | Servidor | **Só quem pediu** (`to=sid`) | Envia `motivo` e `causa`; estado não muda |
| `recurso.produzido` | Servidor | Todos | A cada `INTERVALO`, estoque `+= producao` (causa: `temporizador`) |
| `construcao.concluida` | Servidor | Todos | Libera trabalhador, `em_obra -= 1`, `concluidas += 1`, aumenta produção (causa: `construcao.iniciada (temporizador)`) |
| `vila.encerramento_solicitado` | Mestre | Servidor | Pedido para encerrar |
| `vila.encerrada` | Servidor | Todos | Fase vira `encerrada`; produção para; novas ações são recusadas |

Os nomes dos eventos podem continuar esses (recomendado — menos chance de erro). Os nomes de **recursos, construções, trabalhadores, textos e emojis** devem ser do tipo de vila sorteado. Os nomes têm que ser **idênticos** na especificação, no `server.py` e no `index.html`.

---

## 5. Regras de implementação (obrigatórias)

### Servidor (`server.py`)
- Seguir o Guia de Implementação, etapas 1 a 6, usando o esqueleto do kit.
- Todo fato é montado por `fato(causa, **extras)` → `{"estado": dict(estado), "causa": causa, ...}`.
- Recusa sempre por `recusar(sid, motivo, causa)` → `sio.emit("operacao.recusada", ..., to=sid)`.
- Em `construcao.solicitada`: **validar tudo e alterar o estado SEM nenhum `await` no meio** (é isso que resolve a disputa). Ordem das validações: temporada aberta → recurso suficiente → trabalhador livre.
- Abertura/encerramento: só `papel == "mestre"`; validar a fase atual.
- Temporizadores com `sio.start_background_task(...)` e `await sio.sleep(...)`. **Nunca `time.sleep`.** Nunca laço que fica verificando estado para o cliente.
- Todo handler: `async def f(sid, dados=None)`.
- Estado do kit: `fase, <recurso>, trabalhadores, limite, producao, intervalo, tempo_obra, custo, concluidas, em_obra` (+ o recurso refinado, ver seção 6).

### Cliente (`client/index.html`)
- Usar **só** `ouvir(evento, "reação", fn)` e `pedir(evento)` — nunca `socket.on`/`socket.emit` direto (senão não aparece no Painel de eventos).
- O cliente **nunca altera o estado por conta própria**; só via `atualizar(d)` ao receber um fato.
- Ligar cada evento ao método do Phaser: `mostrarEstado`, `vilaIniciada`, `obraIniciada`, `recusado`, `recursoProduzido`, `obraConcluida`, `vilaEncerrada`.
- Avisos (`avisar`) de sucesso, recusa (`"erro"`) e fim de obra (`"ok"`).
- Cada frase de reação do `ouvir(...)` descreve o que o cliente faz e bate com a especificação.
- Rodapé: `Desenvolvido por: <nomes dos integrantes>`.
- **Não remover** o Painel de eventos.
- No bloco do Phaser, mexer **apenas** em textos/emojis se for preciso (ex.: "🏠 Obra concluída!" → "🪚 Serraria pronta!"). Não alterar a lógica.
- Acrescentar `tabuas` ao `estado` reativo, ao painel de recursos e à função `resumir()`, e trocar "Trabalhadores"/"Construções" por "Lenhadores"/"Serrarias" na tela.
- **Contadores por evento (obrigatório, é dupla):** trocar o comentário `ETAPA 7 (dupla)` pelo bloco de contadores do Guia (`v-for="(n, nome) in contadores"`). Sem isso perde 0,5 ponto.

### Comentários (vale nota)
- Em **todo** ponto onde um evento é emitido ou escutado (servidor e cliente), um comentário curto em português explicando **o porquê** (ex.: `# só quem pediu recebe: os outros não precisam saber da recusa`).
- Fora disso, sem comentários desnecessários.

---

## 6. Adaptação ao tipo de vila (obrigatória, mínimo necessário)

**Tipo sorteado: Madeireira.** Atenção: o exemplo do Guia/kit já usa toras, então o recurso primário é o mesmo. Por isso a diferença em relação ao exemplo precisa ficar evidente nos outros pontos. Um trabalho igual ao exemplo não cumpre o escopo.

Fazer exatamente isto:
1. **Nomes:** recurso primário `toras` 🪵 (mantém o campo `toras`); recurso refinado `tabuas` (tábuas); trabalhadores = **lenhadores** 🪓; a construção é a **serraria** (o texto da tela diz "Construir serraria", e os avisos falam em serraria e lenhadores, não em "obra genérica"/"trabalhadores"). Os eventos mantêm os nomes da seção 4.
2. **Números próprios, diferentes do exemplo** (o exemplo usa custo 50, obra 8 s, intervalo 5 s, limite 2, estoque 150, produção 10, ganho +5). Usar:
   - `CUSTO = 60` toras por serraria
   - `TEMPO_OBRA = 10` segundos
   - `INTERVALO = 4` segundos
   - `limite = 3` lenhadores
   - estoque inicial: 120 toras, 0 tábuas
   - produção inicial: 12 toras por intervalo
   - cada serraria concluída: produção de toras `+= 4`
3. **Recurso refinado `tabuas`:** novo campo no estado. A cada `recurso.produzido`, cada serraria concluída gera 2 tábuas (`tabuas += 2 * concluidas`). Uma nova linha no painel de recursos da tela (ex.: "🪚 Tábuas: N") e as tábuas aparecem no `resumir()` do painel de eventos.

Se o usuário quiser outros números, trocar aqui e na especificação antes do código.

Não implementar "o que expira" (encomenda de tábuas com prazo), missões, níveis nem mapa novo — são extras.

---

## 7. Ordem de trabalho e commits

O histórico de commits é avaliado. **A especificação precisa ser commitada antes do código** (senão perde 2,0 pontos).

**O Claude não faz commit nem push sem o usuário pedir.** Ao fim de cada etapa: parar, dizer como testar com duas abas e sugerir a mensagem de commit.

| # | Etapa | Commit sugerido |
|---|---|---|
| E | Preencher `docs/especificacao.md` (seção 8) já com os nomes e números do tipo de vila | `docs: especificação da vila` |
| 0 | Kit no ar (já vem pronto) | `feat: kit inicial e esqueleto do servidor` |
| 1 | `estado.sincronizado` | `feat: conexão e estado.sincronizado` |
| 2 | Abertura pelo Mestre | `feat: Mestre abre a temporada (vila.iniciada)` |
| 3 | `construcao.solicitada` / `construcao.iniciada` | `feat: construção` |
| 4 | Validações e `operacao.recusada` | `feat: validações e operacao.recusada` |
| 5 | Temporizadores: produção e obra | `feat: produção automática e obra com tempo` |
| 6 | Encerramento + teste de disputa | `feat: encerramento da temporada` |
| 7 | Contadores por evento (obrigatório) | `feat: contadores por evento` |
| 8 | README final | `docs: README` |

Como a especificação já é escrita com o tipo de vila, as etapas 1–6 já usam os nomes e números do tipo sorteado (não precisa fazer a vila de toras e depois trocar). O recurso refinado entra na etapa 5.

---

## 8. `docs/especificacao.md` (usar o modelo do kit)

- **Não citar tecnologia** (nada de Python, Socket.IO, Vue, servidor HTTP etc.). Escrever na linguagem da vila.
- (a) Tabela de eventos da seção 4, adaptada ao tipo de vila, com a coluna "O que muda no estado".
- (b) Regras: recurso primário e refinado, custo, tempo da obra, limite de trabalhadores, intervalo e quantidade da produção, o que muda quando uma obra termina.
- (c) Três cenários Dado / Quando / Então, escritos com eventos:
  - **Recusa** (ex.: construir com a temporada fechada ou sem recurso);
  - **Passagem do tempo** (produção a cada intervalo e obra terminando sozinha);
  - **Disputa** (ex.: "dado que há N-1 de N trabalhadores ocupados, quando A e B emitem `construcao.solicitada` ao mesmo tempo, então o servidor emite `construcao.iniciada` para um e `operacao.recusada` só para o outro").
- Os números da especificação devem ser exatamente os do `server.py`.

---

## 9. README.md (usar o modelo do kit)

Precisa ter:
- Título com o tipo de vila; integrantes com **nome e @GitHub**.
- Linguagem e bibliotecas: Python + python-socketio + uvicorn; cliente Vue 3, Socket.IO e Phaser 3 por CDN (do kit).
- Como instalar e executar (comandos da seção 2).
- Como testar com duas abas (Mestre abre, Jogador constrói, recusa, produção, obra, encerramento) e três abas para a disputa.
- Respostas às três perguntas, citando eventos e trechos reais do código:
  1. Quais eventos o sistema emite e escuta?
  2. Como o sistema sabe quando deve atualizar os outros jogadores?
  3. Que parte do código mostra claramente o paradigma orientado a eventos?
- **Uso de IA:** declarar que usou o Claude (Claude Code), para quê, e o que o aluno mudou/revisou. (O usuário completa o que ele mudou.)
- Sem seção de extras (não há extras).

---

## 10. Checklist final (conferir antes de dizer que terminou)

- [ ] Especificação commitada antes do código; um commit por etapa.
- [ ] Todos os eventos da seção 4 funcionando, testados com 2–3 abas, sem recarregar a página.
- [ ] Recusa aparece só na aba de quem pediu, em vermelho no painel.
- [ ] Disputa: trabalhadores e recurso nunca passam do limite / ficam negativos.
- [ ] Produção e obra acontecem sozinhas (causa `temporizador` no painel).
- [ ] Painel mostra emit/on, nome, hora, causa, dados e reação de cada evento.
- [ ] Nomes, números, textos e emojis do tipo de vila; recurso refinado no estado e na tela.
- [ ] Comentários do "porquê" em cada emit/on.
- [ ] Nome dos desenvolvedores no rodapé.
- [ ] Contadores por evento.
- [ ] README completo; `.venv` fora do repositório.
- [ ] Nada em inglês na interface.

---

## 11. Referência: tipos de vila (PDF do professor)

| # | Vila | Primário → refinado | Construções | Trabalhadores |
|---|---|---|---|---|
| 1 | Madeireira | toras → tábuas | serraria, depósito, cabana | lenhadores |
| 2 | Fazenda | trigo → farinha | moinho, celeiro, horta | agricultores |
| 3 | Mina | pedra e minério → barras | fornalha, depósito, poço | mineiros |
| 4 | Porto de pesca | peixe → peixe salgado | cais, salga, barco | pescadores |
| 5 | Taverna | ingredientes → pratos | cozinha, despensa, salão | cozinheiros |
| 6 | Ferraria | barras → ferramentas | forja, bancada, armazém | ferreiros |
| 7 | Apiário e mercado | mel → hidromel | colmeia, barraca, adega | apicultores |
| 8 | Alquimia | ervas → poções | estufa, laboratório, estante | alquimistas |
| 9 | Cervejaria artesanal | cevada → cerveja | maltaria, tanques, adega | cervejeiros |
| 10 | Tecelagem | algodão → tecido | tear, tinturaria, depósito | tecelões |
| 11 | Olaria | argila → telhas | olaria, forno, secador | oleiros |
| 12 | Cebolal | cebola → cebola curada | canteiros, galpão de cura, conserveira | colhedores |
| 13 | Pomar e geleias | frutas → geleia | pomar, tacho, despensa | colhedores |
| 14 | Laticínios | leite → queijo | curral, queijaria, câmara de cura | ordenhadores |
| 15 | Padaria | farinha → pães | moinho, forno, vitrine | padeiros |
| 16 | Escribas | papel e tinta → livros | scriptorium, encadernação, estante | escribas |
| 17 | Estaleiro | madeira → barcos | carpintaria, doca, depósito | carpinteiros |
| 18 | Cristais | cristal bruto → cristal lapidado | mina de cristal, lapidaria, cofre | lapidadores |
| 19 | Floricultura | flores → buquês | estufa, ateliê, loja | floristas |
| 20 | Engenho de cana | cana → rapadura | plantio, engenho, tacho | cortadores |
| 21 | Salina | água do mar → sal | tanques, secagem, armazém | salineiros |
| 22 | Vinícola | uvas → vinho | parreiral, lagar, adega | vindimadores |
| 23 | Cafezal | café → café torrado | plantação, terreiro, torrefação | colhedores |
| 24 | Vidraçaria | areia → vidro | forno, bancada de sopro, depósito | vidreiros |
| 25 | Chocolataria | cacau → chocolate | torrefação, moagem, vitrine | chocolateiros |

(A coluna "o que expira" do PDF é extra — não implementar.)

---

## 12. Avaliação (para priorizar)

Especificação 2,0 · Eventos emit/on 2,5 · Fluxo em tempo real 2,0 · Painel e interface 1,5 · Código 1,0 · README e GitHub 1,0. Penalidade de −0,10 por funcionalidade incompleta **ou fora do escopo** — mais um motivo para não fazer nada além do pedido. Cada integrante precisa saber explicar qualquer evento: quem emite, quem escuta e o que muda.
