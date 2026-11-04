import socketio

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
app = socketio.ASGIApp(sio, static_files={
    "/": "client/index.html",
    "/assets": "client/assets",      # mapa, tileset e sprites da vila
})

# A partir da Etapa 1, adicione o seu código ABAIXO desta linha.

CUSTO = 60          # toras por serraria
TEMPO_OBRA = 10     # segundos até a serraria ficar pronta
INTERVALO = 4       # segundos entre cada produção de toras

estado = {
    "fase": "aguardando",
    "toras": 120,
    "tabuas": 0,
    "trabalhadores": 0,     # lenhadores ocupados
    "limite": 3,            # total de lenhadores
    "producao": 12,         # toras por intervalo
    "intervalo": INTERVALO,
    "tempo_obra": TEMPO_OBRA,
    "custo": CUSTO,
    "concluidas": 0,        # serrarias prontas
    "em_obra": 0,           # serrarias em construção
}

jogadores = {}      # sid -> {"nome": ..., "papel": ...}

GANHO_POR_SERRARIA = 4      # toras a mais por intervalo a cada serraria pronta
TABUAS_POR_SERRARIA = 2     # tábuas por serraria pronta a cada produção


def fato(causa, **extras):
    return {"estado": dict(estado), "causa": causa, **extras}


async def recusar(sid, motivo, causa):
    # só quem pediu recebe: os outros não precisam saber da recusa e o estado não mudou
    await sio.emit("operacao.recusada", {"motivo": motivo, "causa": causa}, to=sid)


@sio.event
async def connect(sid, environ, auth=None):
    auth = auth or {}
    jogadores[sid] = {"nome": auth.get("nome", "Anônimo"), "papel": auth.get("papel", "jogador")}
    # só quem acabou de entrar recebe: os outros já têm o estado atual
    await sio.emit("estado.sincronizado", fato("conexao"), to=sid)


@sio.event
async def disconnect(sid, dados=None):
    jogadores.pop(sid, None)


# o Mestre pede para abrir; o servidor é quem decide se a temporada pode começar
@sio.on("vila.abertura_solicitada")
async def abertura_solicitada(sid, dados=None):
    if jogadores[sid]["papel"] != "mestre":
        return await recusar(sid, "Só o Mestre pode abrir a temporada", "vila.abertura_solicitada")
    if estado["fase"] != "aguardando":
        return await recusar(sid, "A temporada já foi aberta", "vila.abertura_solicitada")
    estado["fase"] = "aberta"
    # todos recebem: a temporada aberta vale para a vila inteira
    await sio.emit("vila.iniciada", fato("vila.abertura_solicitada"))
    sio.start_background_task(produzir)


# o Jogador só pede; o servidor decide e altera o estado
@sio.on("construcao.solicitada")
async def construcao_solicitada(sid, dados=None):
    # validar e alterar sem nenhum await no meio: assim dois pedidos simultâneos
    # não conseguem os mesmos lenhadores/toras (só um passa)
    if estado["fase"] != "aberta":
        return await recusar(sid, "A temporada não está aberta", "construcao.solicitada")
    if estado["toras"] < CUSTO:
        return await recusar(sid, "Toras insuficientes", "construcao.solicitada")
    if estado["trabalhadores"] >= estado["limite"]:
        return await recusar(sid, "Sem lenhador livre", "construcao.solicitada")
    estado["toras"] -= CUSTO
    estado["trabalhadores"] += 1
    estado["em_obra"] += 1
    # todos recebem: as toras gastas e o lenhador ocupado mudam a vila de todo mundo
    await sio.emit("construcao.iniciada", fato("construcao.solicitada", jogador=jogadores[sid]["nome"]))
    sio.start_background_task(concluir_obra)


# o Mestre pede para encerrar; o servidor valida e decide
@sio.on("vila.encerramento_solicitado")
async def encerramento_solicitado(sid, dados=None):
    if jogadores[sid]["papel"] != "mestre":
        return await recusar(sid, "Só o Mestre pode encerrar a temporada", "vila.encerramento_solicitado")
    if estado["fase"] != "aberta":
        return await recusar(sid, "A temporada não está aberta", "vila.encerramento_solicitado")
    estado["fase"] = "encerrada"
    # todos recebem: com a temporada encerrada a produção para e ninguém mais constrói
    await sio.emit("vila.encerrada", fato("vila.encerramento_solicitado"))


# temporizador: a vila produz sozinha a cada INTERVALO, sem ninguém pedir
async def produzir():
    while estado["fase"] == "aberta":
        await sio.sleep(INTERVALO)
        if estado["fase"] != "aberta":
            break
        estado["toras"] += estado["producao"]
        estado["tabuas"] += TABUAS_POR_SERRARIA * estado["concluidas"]
        # todos recebem: o estoque é da vila inteira; a causa é o tempo, não um pedido
        await sio.emit("recurso.produzido", fato("temporizador"))


# temporizador: a serraria fica pronta sozinha TEMPO_OBRA segundos depois de iniciada
async def concluir_obra():
    await sio.sleep(TEMPO_OBRA)
    if estado["fase"] != "aberta":
        return
    estado["trabalhadores"] -= 1
    estado["em_obra"] -= 1
    estado["concluidas"] += 1
    estado["producao"] += GANHO_POR_SERRARIA
    # todos recebem: o lenhador livre e a produção maior valem para todo mundo
    await sio.emit("construcao.concluida", fato("construcao.iniciada (temporizador)"))
