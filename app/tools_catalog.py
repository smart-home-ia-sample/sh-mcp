# One entry per generic verb tool (not per device type). Documented with tags and
# Portuguese example phrasings spanning every device type the verb applies to, so
# the BFA can rank it in /resolve. This list is the source of `GET /tools`, which
# the BFA pulls into its catalog (spec/13) — no self-registration.
TOOLS: list[dict] = [
    {
        "id": "turn_on",
        "name": "Turn on",
        "description": "Turns a device on (light, TV, coffee maker, AC, any on/off appliance)",
        "tags": ["on", "light", "tv", "appliance", "ac", "coffee"],
        "examples": [
            "acende a luz da sala", "liga a TV", "liga a cafeteira",
            "liga o ar-condicionado do quarto", "pode ligar a luz da cozinha?",
        ],
    },
    {
        "id": "turn_off",
        "name": "Turn off",
        "description": "Turns a device off (light, TV, coffee maker, AC, any on/off appliance)",
        "tags": ["off", "light", "tv", "appliance", "ac", "coffee"],
        "examples": [
            "apaga a luz da sala", "desliga a TV", "desliga a cafeteira",
            "desliga o ar-condicionado", "escurece o quarto",
        ],
    },
    {
        "id": "set_brightness",
        "name": "Set brightness",
        "description": "Sets a dimmable light's brightness level from 0 to 100",
        "tags": ["light", "brightness", "dim"],
        "examples": ["diminui o brilho da luz do quarto", "coloca a luz da sala em 30%", "abaixa a luz"],
    },
    {
        "id": "set_temperature",
        "name": "Set temperature",
        "description": "Sets the target temperature of an air conditioner (16-30 C)",
        "tags": ["ac", "air conditioner", "temperature", "climate"],
        "examples": ["ajusta a temperatura para 22 graus", "está muito quente no quarto", "coloca o ar em 24"],
    },
    {
        "id": "open",
        "name": "Open",
        "description": "Opens a curtain or a window",
        "tags": ["curtain", "blinds", "window", "open"],
        "examples": ["abre a cortina da sala", "abre a janela do quarto", "levanta a cortina"],
    },
    {
        "id": "close",
        "name": "Close",
        "description": "Closes a curtain or a window",
        "tags": ["curtain", "blinds", "window", "close"],
        "examples": ["fecha a cortina da sala", "fecha a janela do quarto", "abaixa a cortina"],
    },
    {
        "id": "lock",
        "name": "Lock",
        "description": "Locks a door",
        "tags": ["door", "lock", "security"],
        "examples": ["tranca a porta da frente", "pode trancar a porta?", "fecha tudo à chave"],
    },
    {
        "id": "unlock",
        "name": "Unlock",
        "description": "Unlocks a door",
        "tags": ["door", "unlock", "security"],
        "examples": ["destranca a porta da frente", "abre a porta da frente à chave"],
    },
    {
        "id": "arm",
        "name": "Arm alarm",
        "description": "Arms the home alarm system",
        "tags": ["alarm", "security", "arm"],
        "examples": ["arma o alarme", "ativa a segurança da casa"],
    },
    {
        "id": "disarm",
        "name": "Disarm alarm",
        "description": "Disarms the home alarm system",
        "tags": ["alarm", "security", "disarm"],
        "examples": ["desarma o alarme", "desativa a segurança"],
    },
]
