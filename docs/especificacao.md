# Especificação — Vila em Tempo Real

**Integrantes:** Guilherme Antunes Rodrigues (@guilhermeantunesrod) e Samuel Frare (@samuelpavanello-cyber)
**Tipo de vila (sorteio):** Madeireira

## 1. Regras da vila

- **Papéis:** o Mestre abre e encerra a temporada; o Jogador constrói serrarias.
- **Recurso primário e recurso refinado:** toras 🪵 (primário) e tábuas 🪚 (refinado).
- **Estoque inicial:** 120 toras e 0 tábuas.
- **Construção:** serraria.
- **Custo de uma serraria:** 60 toras.
- **Tempo da obra:** 10 segundos. A obra termina sozinha.
- **Limite de lenhadores:** 3. Cada obra ocupa 1 lenhador do início ao fim.
- **Produção automática:** a cada 4 segundos, enquanto a temporada estiver aberta, a vila ganha 12 toras (valor inicial).
- **Quando uma serraria fica pronta:** o lenhador fica livre, a produção de toras aumenta em 4 por intervalo e, a partir daí, cada serraria pronta gera 2 tábuas a cada produção.
- **Recusas:** um pedido é recusado, e só quem pediu é avisado, quando:
  - a temporada não está aberta;
  - faltam toras para pagar a serraria;
  - todos os lenhadores estão ocupados;
  - um Jogador tenta abrir ou encerrar a temporada (só o Mestre pode);
  - o Mestre tenta abrir uma temporada que já foi aberta, ou encerrar uma que não está aberta.
- **Um pedido por vez:** os pedidos são decididos um de cada vez, na ordem em que chegam. Se dois pedidos disputam o último lenhador ou as últimas toras, só o primeiro é aceito.
- **Encerramento:** depois que a temporada é encerrada, a produção para, as obras em andamento não terminam mais e todo novo pedido é recusado.

## 2. Eventos

| Evento | Emite | Recebe | O que muda no estado |
|---|---|---|---|
| `estado.sincronizado` | Servidor | Só quem acabou de entrar | Nada muda; quem entrou recebe o estado atual da vila |
| `vila.abertura_solicitada` | Mestre | Servidor | É um pedido; nada muda |
| `vila.iniciada` | Servidor | Todos | A temporada passa de "aguardando" para "aberta" e a produção automática começa |
| `construcao.solicitada` | Jogador | Servidor | É um pedido; nada muda |
| `construcao.iniciada` | Servidor | Todos | Toras −60, lenhadores ocupados +1, serrarias em obra +1 |
| `operacao.recusada` | Servidor | Só quem pediu | Nada muda; quem pediu recebe o motivo da recusa |
| `recurso.produzido` | Servidor | Todos | Toras + produção atual; tábuas + 2 × serrarias prontas |
| `construcao.concluida` | Servidor | Todos | Lenhadores ocupados −1, serrarias em obra −1, serrarias prontas +1, produção de toras +4 |
| `vila.encerramento_solicitado` | Mestre | Servidor | É um pedido; nada muda |
| `vila.encerrada` | Servidor | Todos | A temporada passa para "encerrada"; a produção para e novos pedidos são recusados |

## 3. Cenários de teste (Dado / Quando / Então, escritos com eventos)

### Recusa
Dado que a temporada está aberta, há 3 de 3 lenhadores ocupados e o estoque tem 150 toras,
quando o Jogador A emite `construcao.solicitada`,
então o servidor emite `operacao.recusada` com o motivo "Sem lenhador livre" apenas para o Jogador A, e o estoque continua com 150 toras e 3 de 3 lenhadores ocupados.

### Passagem do tempo
Dado que a temporada está aberta, há 120 toras, 0 tábuas, produção de 12 toras e nenhuma serraria pronta,
quando o Jogador A emite `construcao.solicitada`,
então o servidor emite `construcao.iniciada` para todos (toras: 60, lenhadores: 1 de 3);
a cada 4 segundos, sem ninguém pedir, o servidor emite `recurso.produzido` para todos, com +12 toras;
10 segundos depois do início da obra, o servidor emite `construcao.concluida` para todos (lenhadores: 0 de 3, serrarias prontas: 1, produção: 16 toras);
e o próximo `recurso.produzido` traz +16 toras e +2 tábuas.

### Disputa entre dois jogadores
Dado que a temporada está aberta, há 2 de 3 lenhadores ocupados e o estoque tem 200 toras,
quando os jogadores A e B emitem `construcao.solicitada` ao mesmo tempo,
então o servidor emite `construcao.iniciada` para todos apenas uma vez, para o pedido que chegou primeiro (lenhadores: 3 de 3, toras: 140), e emite `operacao.recusada` com o motivo "Sem lenhador livre" apenas para o outro jogador. Os lenhadores ocupados nunca passam de 3.
