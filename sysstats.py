import os

try:
    import psutil
    _PSUTIL_AVAILABLE = True
except ImportError:
    _PSUTIL_AVAILABLE = False

# El % de CPU por ventana se normaliza contra el total de nucleos, para
# que sea comparable con el % de RAM/swap del sistema (0-100 = "cuanto de
# la capacidad total de la maquina esta usando esto"), en vez de dejarlo
# en la escala nativa de psutil (0-100 POR NUCLEO, que puede superar 100
# en procesos con varios hilos).
_CPU_COUNT = (psutil.cpu_count(logical=True) or 1) if _PSUTIL_AVAILABLE else 1


def stats_available():
    return _PSUTIL_AVAILABLE


def system_ram_percent():
    return psutil.virtual_memory().percent


def system_swap_percent():
    return psutil.swap_memory().percent


class ProcessTreeCpu:
    """Trackea el % de CPU (normalizado a 0-100 sobre el total de la
    maquina) de un proceso y todos sus hijos, sumados.

    Un proceso "hijo" cubre, por ejemplo, un compilador lanzado desde una
    terminal, o un proceso de decodificacion de video lanzado por un
    navegador: sin sumar el arbol completo, esa carga no se reflejaria en
    el PID de la ventana en si.

    Hay que mantener la MISMA instancia de esta clase entre polls:
    psutil.Process.cpu_percent() mide el uso transcurrido desde la ULTIMA
    vez que se llamo sobre ese mismo objeto Process; crear un Process
    nuevo en cada poll siempre devolveria 0.0 (nunca hay "ultima vez").
    """

    def __init__(self, root_pid):
        self._root_pid = root_pid
        self._procs = {}  # pid -> psutil.Process, ya "primeados"
        self._discover_and_prime()

    def _discover(self):
        if not self._root_pid:
            return []
        try:
            root = psutil.Process(self._root_pid)
        except psutil.NoSuchProcess:
            return []
        procs = [root]
        try:
            procs.extend(root.children(recursive=True))
        except psutil.NoSuchProcess:
            pass
        return procs

    def _discover_and_prime(self):
        # cpu_percent(None) sin bloquear arranca el contador interno de
        # ese Process; la primera lectura siempre da 0.0 (no hay intervalo
        # previo), pero deja el objeto listo para que el proximo poll() de
        # un numero real.
        for p in self._discover():
            if p.pid not in self._procs:
                try:
                    p.cpu_percent(None)
                    self._procs[p.pid] = p
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

    def poll(self):
        # se vuelve a descubrir el arbol en cada poll: un proceso de
        # compilacion o de decodificacion que arranco despues de crear
        # este tracker tiene que sumarse tambien, no solo los que existian
        # al momento de abrir el picker.
        self._discover_and_prime()

        total = 0.0
        dead_pids = []
        for pid, proc in self._procs.items():
            try:
                total += proc.cpu_percent(None)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                dead_pids.append(pid)
        for pid in dead_pids:
            del self._procs[pid]

        return total / _CPU_COUNT
