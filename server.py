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


def fato(causa, **extras):
    return {"estado": dict(estado), "causa": causa, **extras}


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
        return
    if estado["fase"] != "aguardando":
        return
    estado["fase"] = "aberta"
    # todos recebem: a temporada aberta vale para a vila inteira
    await sio.emit("vila.iniciada", fato("vila.abertura_solicitada"))
