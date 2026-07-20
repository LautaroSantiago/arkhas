#!/bin/bash
# Reinicia Arkhas de cero: mata cualquier instancia (nueva o vieja), limpia
# el lockfile, y lo vuelve a levantar en segundo plano desde ESTE
# directorio. Pensado para cortar de raiz cualquier estado raro (proceso
# viejo con codigo desactualizado, lock huerfano, picker que haya quedado
# colgado) sin tener que acordarse de la secuencia de comandos a mano.
set -e

echo "Matando cualquier instancia de Arkhas..."
pkill -9 -f "arkhas.py" 2>/dev/null || true
sleep 1

echo "Limpiando el lockfile..."
rm -f "$HOME/.config/arkhas/arkhas.lock"

# cd al directorio donde esta este script (no a donde se lo invoco desde),
# asi funciona sin importar la carpeta actual de la terminal
cd "$(dirname "$(readlink -f "$0")")"

echo "Levantando Arkhas oculto..."
setsid nohup python3 arkhas.py --hidden >> /tmp/arkhas.log 2>&1 < /dev/null &
disown 2>/dev/null || true
sleep 1

# El volcado completo del log solo tiene sentido si alguien lo esta
# mirando en una terminal de verdad. Si este script se invoca desde el
# autostart (stdout redirigido a un archivo, no a una terminal), volcar
# el log completo ahi mismo lo haria crecer mucho mas rapido de lo
# necesario en cada boot (se estaria copiando el log adentro de si mismo).
if [ -t 1 ]; then
    echo "--- log ---"
    cat /tmp/arkhas.log
fi

echo "--- proceso ---"
if pgrep -af "arkhas.py" > /dev/null; then
    pgrep -af "arkhas.py"
else
    echo "NO HAY NINGUN PROCESO CORRIENDO - algo fallo, revisar el log"
fi
