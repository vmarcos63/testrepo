# Detector sísmico experimental — fase 0

Detector **en silencio** que usa solo datos abiertos y gratuitos:

- **Señales en tiempo real** de estaciones sísmicas abiertas, vía el servidor SeedLink público de EarthScope (`rtserve.earthscope.org`). Con ellas detectamos nosotros mismos el inicio del sacudón (STA/LTA por estación más asociación entre estaciones).
- **EMSC** por websocket, para comparar cuánto tardan en publicar.

Nada de esto es una alerta pública: los avisos van a un chat privado de Telegram y todo queda registrado en CSV para **medir la velocidad real** durante las réplicas.

## Qué hace cada parte

| Comando | Qué hace |
|---|---|
| `python -m sismo.find_stations` | Busca estaciones abiertas y activas en la región (Panamá con margen) y las guarda en `data/stations.json` |
| `python -m sismo.detector` | Se conecta a SeedLink, detecta disparos por estación y declara un sismo cuando **3 o más estaciones** a menos de 250 km se disparan en menos de 20 s. Avisa por Telegram con la cuenta regresiva estimada para cada ciudad |
| `python -m sismo.emsc_listener` | Registra cada sismo que publica EMSC en la región y cuántos minutos tardó en publicarlo |

Archivos que se generan en `data/`:

- `triggers.csv`: cada disparo individual de estación.
- `detections.csv`: cada sismo detectado, con la demora desde el primer disparo.
- `emsc.csv`: cada evento de EMSC, con su demora de publicación.
- `status.csv`: cuántas estaciones están enviando datos (una vez por hora).

## Instalación en Oracle Cloud (Always Free)

### 1. Crear el servidor

1. En la consola de Oracle: **Compute → Instances → Create instance**.
2. **Image:** Canonical Ubuntu 24.04.
3. **Shape:** *Ampere* → `VM.Standard.A1.Flex`, con **1 OCPU y 6 GB** de memoria (entra en Always Free).
4. **SSH keys:** subí tu clave pública o descargá la que genera Oracle.
5. Crear. No hace falta abrir puertos: el servidor solo hace conexiones salientes.

Si aparece "Out of capacity" para Ampere, probá otro *Availability Domain* o reintentá más tarde.

### 2. Instalar

Conectate por SSH (`ssh ubuntu@<IP pública>`) y corré:

```bash
sudo apt update && sudo apt install -y git python3-venv python3-dev build-essential
git clone -b claude/festive-franklin-vdtary https://github.com/vmarcos63/testrepo.git
cd testrepo
python3 -m venv .venv
.venv/bin/pip install -r sismo/requirements.txt
.venv/bin/python -m unittest discover -s sismo/tests -t .
```

Si el repositorio es privado, `git clone` va a pedir usuario y un *personal access token* de GitHub en lugar de la contraseña.

### 3. Bot de Telegram (gratis)

1. En Telegram, hablá con **@BotFather** → `/newbot` → copiá el **token**.
2. Mandale cualquier mensaje a tu bot.
3. Abrí `https://api.telegram.org/bot<TOKEN>/getUpdates` y copiá el número de `"chat":{"id":...}`.
4. En el servidor: `cp sismo/.env.example sismo/.env` y completá `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID`.

### 4. Buscar estaciones

```bash
set -a; . sismo/.env; set +a
.venv/bin/python -m sismo.find_stations
```

**Pasame la lista que imprime**: de cuántas estaciones abiertas haya cerca de la costa del Pacífico depende la velocidad que podemos lograr.

### 5. Dejarlo corriendo siempre

```bash
sudo cp sismo/deploy/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now sismo-detector sismo-emsc
journalctl -u sismo-detector -f      # ver el log en vivo
```

Una vez por hora el log muestra cuántas estaciones están enviando datos y con qué demora.

## Ajustes

Todo se configura con variables en `sismo/.env` (ver `sismo/config.py`). Las más importantes:

| Variable | Por defecto | Qué controla |
|---|---|---|
| `SISMO_MIN_STATIONS` | 3 | Estaciones que tienen que coincidir para declarar un sismo |
| `SISMO_TRIGGER_ON` | 4.0 | Sensibilidad del disparo por estación (más alto = menos falsas alarmas) |
| `SISMO_ASSOC_WINDOW_S` | 20 | Ventana de tiempo para asociar disparos |
| `SISMO_EMSC_MIN_MAG` | 3.0 | Magnitud mínima que se registra de EMSC |
| `SISMO_MIN_LAT` … `SISMO_MAX_LON` | Panamá con margen | Región de interés |

## Limitaciones conocidas

- La **zona aproximada** es el promedio de las primeras estaciones en dispararse, no una ubicación sismológica. La cuenta regresiva es optimista: el sismo empezó unos segundos antes del primer disparo.
- No estima magnitud todavía.
- El servidor de EarthScope es compartido y no garantiza la demora; el detector la registra por estación.
- Con pocas estaciones cerca, la detección es más lenta o puede no ocurrir.
