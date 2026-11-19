# ==============================================================================
# RESOLUCIÓN DE RUTA E IMPORTACIÓN DE MÓDULOS (D10):
# Este módulo reside en 'skills/arma3-sqf-skill/scripts/'. Cuando es ejecutado
# como script o importado desde la raíz del plugin, subdirectorios o arnés de
# pruebas, asegura la inclusión de su directorio contenedor en 'sys.path' para
# permitir la resolución directa de su módulo hermano 'sqf_wiki_reader.py'.
# ==============================================================================
import re
import sys
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Literal

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from sqf_wiki_reader import lookup_syntax_symbol


class ScopeStatus(Enum):
    NOT_LOCAL = "NOT_LOCAL"
    LOCAL = "LOCAL"
    MIXED = "MIXED"
    INDETERMINATE = "INDETERMINATE"


@dataclass
class SQFFinding:
    severity: Literal["BLOQUEANTE", "SUGERENCIA", "NO_VERIFICADO"]
    file: str
    line: int
    description: str
    evidence: str
    discipline: str

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


# Advertencias de scope de sqflint: "Local variable \"_x\" is not from this scope (not private)"
# El linter las reporta como warning, no como error, asi que con rc==0 el codigo previously
# las descartaba. SKILL.md declara esa misma categoria como BLOQUEANTE (P0), de modo que
# el mapeo se hace por patron estable y no por texto libre.
SCOPE_WARNING_RE = re.compile(
    r"not from this scope|not private|is not defined but was used",
    re.IGNORECASE,
)


def strip_comments_and_strings(code: str) -> str:
    """Elimina comentarios de línea y bloque, y sustituye contenido de cadenas por espacios."""
    def replacer(match):
        s = match.group(0)
        if s.startswith(('/', '/*')):
            return " " * len(s)
        # Cadena entre comillas: preservar las comillas delimitadoras pero vaciar el contenido interior
        return s[0] + (" " * (len(s) - 2)) + s[-1] if len(s) >= 2 else s

    pattern = r'/\*[\s\S]*?\*/|//.*|"(?:[^"]|"")*"|\'(?:[^\']|\'\')*\''
    return re.sub(pattern, replacer, code)


def evaluate_token_scope(token: str, source_code: str) -> ScopeStatus:
    """Determina si un token aparece asignado/declarado como variable local, distinguiendo posición de comando."""
    if not source_code.strip():
        return ScopeStatus.INDETERMINATE

    clean_code = strip_comments_and_strings(source_code)
    assign_pattern = rf"\b(?:private\s+)?{re.escape(token)}\s*=(?!=)"
    private_pattern = rf"\bprivate\s+([\"']{re.escape(token)}[\"']|{re.escape(token)}\b)"
    params_pattern = rf"\bparams\s*\[[^\]]*[\"']{re.escape(token)}[\"']"

    has_assign = bool(re.search(assign_pattern, clean_code))
    has_private = bool(re.search(private_pattern, clean_code))
    has_params = bool(re.search(params_pattern, clean_code))
    is_local_declared = has_assign or has_private or has_params

    if not is_local_declared:
        return ScopeStatus.NOT_LOCAL

    # Posición de comando: precedida de inicio de línea, ;, { o }, y no seguida de =
    command_pos_pattern = rf"(?:^|[;{{}}])\s*\b{re.escape(token)}\b\s*(?!=)"
    has_command_pos = bool(re.search(command_pos_pattern, clean_code, re.MULTILINE))

    if has_command_pos:
        return ScopeStatus.MIXED
    return ScopeStatus.LOCAL


def parse_sqflint_output(rc: int, stdout: str, source_code: str = "") -> list[SQFFinding]:
    if rc == 2:
        raise ValueError(f"Error de uso de sqflint (rc=2): {stdout.strip()}")

    if rc == 3 or "SQFLINT_NO_DISPONIBLE" in stdout:
        return [SQFFinding(
            severity="NO_VERIFICADO",
            file="desconocido",
            line=0,
            description="Analizador estático no disponible en el host (SQFLINT_NO_DISPONIBLE)",
            evidence=stdout.strip(),
            discipline="Sintaxis"
        )]

    if "Excepción al ejecutar sqflint" in stdout or "TIMEOUT EXPIRED" in stdout:
        return [SQFFinding(
            severity="NO_VERIFICADO",
            file="desconocido",
            line=0,
            description="El linter fue bloqueado, no se pudo ejecutar o supero el tiempo limite",
            evidence=stdout.strip(),
            discipline="Sistema"
        )]

    findings: list[SQFFinding] = []
    seen: set[tuple[str, int, str]] = set()
    pattern = re.compile(r'^(.*?):(\d+):\s*(error|warning):\s*(.*)$', re.IGNORECASE)
    for line_text in stdout.splitlines():
        match = pattern.match(line_text.strip())
        if match:
            file_path, line_num, level, msg = match.groups()
            key = (file_path, int(line_num), msg)
            if key in seen:
                continue
            seen.add(key)
            is_scope = bool(SCOPE_WARNING_RE.search(msg))
            cmd_match = re.search(r"<Variable\(([a-zA-Z0-9_]+)\)>", msg, re.IGNORECASE)
            cmd_name = cmd_match.group(1) if cmd_match is not None else ""

            # PRECEDENCIA DE ÁMBITO SOBRE TRATAMIENTO DE COMANDO (D2):
            # Si el mensaje es un aviso de ámbito, la severidad es BLOQUEANTE y la
            # disciplina es Scope, independientemente de si incluye marcas <Variable(...)>.
            if is_scope:
                severity: Literal["BLOQUEANTE", "SUGERENCIA", "NO_VERIFICADO"] = "BLOQUEANTE"
                discipline = "Scope"
            elif cmd_name:
                scope_status = evaluate_token_scope(cmd_name, source_code)
                if scope_status == ScopeStatus.LOCAL or scope_status == ScopeStatus.MIXED or scope_status == ScopeStatus.INDETERMINATE:
                    severity = "BLOQUEANTE"
                    discipline = "Scope"
                else:  # ScopeStatus.NOT_LOCAL
                    wiki_info = lookup_syntax_symbol(cmd_name)
                    if wiki_info is None:
                        severity = "BLOQUEANTE"
                        discipline = "Sintaxis"
                    else:
                        canonical = wiki_info["canonical_name"]
                        if cmd_name != canonical:
                            severity = "BLOQUEANTE"
                            discipline = "Sintaxis"
                            msg = f"Comando oficial '{canonical}' escrito con casing divergente '{cmd_name}'"
                        else:
                            status = wiki_info.get("status", "ok")
                            if status == "broken":
                                severity = "BLOQUEANTE"
                                discipline = "Biki"
                                msg = f"Comando oficial reportado como ROTO (broken) en el snapshot: {canonical}"
                            elif status == "deprecated":
                                severity = "SUGERENCIA"
                                discipline = "Biki"
                                rep = ", ".join(wiki_info["replaced_by"]) if wiki_info.get("replaced_by") else "sin sustituto"
                                msg = f"Comando oficial deprecado: {canonical} (reemplazado por: {rep}; ver {wiki_info['url']})"
                            else:
                                severity = "SUGERENCIA"
                                discipline = "Biki"
                                ver = wiki_info.get("version", "versión no disponible en el snapshot")
                                msg = f"Comando oficial válido según Biki: {canonical} (desde v{ver}; ver {wiki_info['url']})"
            elif level.lower() == "error":
                severity = "BLOQUEANTE"
                discipline = "Sintaxis"
            else:
                severity = "SUGERENCIA"
                discipline = "Sintaxis"

            findings.append(SQFFinding(
                severity=severity,
                file=file_path,
                line=int(line_num),
                description=msg,
                evidence=line_text,
                discipline=discipline
            ))

    if not findings and rc not in (0, 1):
        findings.append(SQFFinding(
            severity="NO_VERIFICADO",
            file="desconocido",
            line=0,
            description=f"Fallo del linter o rc desconocido (rc={rc})",
            evidence=stdout,
            discipline="Sintaxis"
        ))
    elif not findings and rc == 1:
        findings.append(SQFFinding(
            severity="BLOQUEANTE",
            file="desconocido",
            line=0,
            description="Error de sintaxis o formato no reconocido del linter (rc=1)",
            evidence=stdout,
            discipline="Sintaxis"
        ))
    return findings


# Estos dos patrones deben ser IDENTICOS a los de SKILL.md lineas 70 y 72.
# Si divergen, el codigo deja de detectar lo que la skill prohibe en modo Micro.
NETWORK_SIGNALS_RE = re.compile(
    r"\b(remoteExec|remoteExecCall|publicVariable|publicVariableServer|publicVariableClient"
    r"|addPublicVariableEventHandler|remoteExecutedOwner|setOwner|BIS_fnc_MP|isDedicated"
    r"|isServer|hasInterface|HeadlessClient)\b"
    r"|setVariable\s*\[.*true",
    re.IGNORECASE,
)

PERFORMANCE_SIGNALS_RE = re.compile(
    r"\b(while|waitUntil|EachFrame|onEachFrame|Draw3D|allUnits|allGroups|allMissionObjects"
    r"|nearestObjects|nearEntities|createVehicle|createUnit|createGroup|addEventHandler"
    r"|addMissionEventHandler|spawn|execVM)\b",
    re.IGNORECASE,
)

LIFECYCLE_SIGNALS_RE = re.compile(
    r"init\.sqf|initServer\.sqf|initPlayerLocal\.sqf|initPlayerServer\.sqf"
    r"|description\.ext|config\.cpp|CfgRemoteExec|CfgFunctions",
    re.IGNORECASE,
)


def check_escalation_needed(raw_code: str, current_mode: str) -> str:
    """Escala fuera de Micro si el codigo cumple CUALQUIER criterio de exclusion de SKILL.md."""
    if current_mode != "Micro":
        return current_mode
    clean_code = strip_comments_and_strings(raw_code)
    if (NETWORK_SIGNALS_RE.search(clean_code)
            or PERFORMANCE_SIGNALS_RE.search(clean_code)
            or LIFECYCLE_SIGNALS_RE.search(clean_code)):
        return "Estándar"
    return current_mode


def check_escalation_needed_for_files(files: dict[str, str] | list[Any], current_mode: str) -> str:
    """Escala fuera de Micro si el codigo cumple CUALQUIER criterio de exclusion de SKILL.md.

    Un inventario VACIO no es un archivo limpio: no es 'Micro', es 'no se puede decidir'.
    Se lanza ValueError para que la capa de arriba lo trate como NO VERIFICADO y no
    como un veredicto. Un modo concedido por defecto sobre nada es un verde por omision.
    """
    if current_mode != "Micro":
        return current_mode
    if not files:
        raise ValueError(
            "Inventario vacio: no se encontraron archivos .sqf. No se puede decidir el modo "
            "sobre cero archivos; un inventario vacio NO es 'Micro'. Revisa la ruta de --root "
            "o indica los archivos concretos."
        )
    if len(files) > 1:
        return "Estándar"
    if isinstance(files, dict):
        for raw in files.values():
            if check_escalation_needed(raw, current_mode) != "Micro":
                return "Estándar"
    else:
        for f in files:
            p = Path(f)
            raw = p.read_text(encoding="utf-8", errors="replace") if p.is_file() else str(f)
            if check_escalation_needed(raw, current_mode) != "Micro":
                return "Estándar"
    return current_mode


def determine_escalation_reason(files: dict[str, str] | list[Any], mode: str) -> str:
    """Determina la causa exacta del escalado o de la permanencia en Micro."""
    if not files:
        return "Sin archivos .sqf detectados en la raíz analizada"
    if len(files) > 1:
        return f"Proyecto multi-archivo ({len(files)} archivos .sqf)"
    
    code = ""
    if isinstance(files, dict) and files:
        code = next(iter(files.values()))
    elif isinstance(files, list) and files:
        p = Path(files[0])
        code = p.read_text(encoding="utf-8", errors="replace") if p.is_file() else str(files[0])
    
    clean = strip_comments_and_strings(code)
    if NETWORK_SIGNALS_RE.search(clean):
        return "Señales de red / MP detectadas"
    if PERFORMANCE_SIGNALS_RE.search(clean):
        return "Señales de scheduler / rendimiento detectadas"
    if LIFECYCLE_SIGNALS_RE.search(clean):
        return "Scripts de ciclo de vida / configuración detectados"
    
    if mode == "Micro":
        return "Archivo único autocontenido sin señales de red ni scheduler"
    return "Configuración manual o modo previo preservado"


REPORT_SCHEMA_VERSION = 1
"""Versión del esquema de informe estructurado.

Contrato compartido entre el script, el prompt de la skill, los evals y
cualquier consumidor externo (MCP). Cambiar el formato de una línea de
hallazgo o de la sección RESUMEN exige subir esta versión.
"""


def format_findings_report(findings: list[SQFFinding], item_9_status: str | None = None) -> str:
    """Produce el informe de hallazgos estructurado de una línea por hallazgo más RESUMEN.

    Esquema v1 (ver ``references/report_format.md``):
      - Primera línea: ``REPORT_SCHEMA_VERSION: <n>``.
      - Una línea por hallazgo: ``[SEVERIDAD] archivo:linea (disciplina): descripcion``.
      - Última línea: ``RESUMEN: bloqueantes=N; sugerencias=N; no_verificado=N``.
    """
    lines: list[str] = [f"REPORT_SCHEMA_VERSION: {REPORT_SCHEMA_VERSION}"]
    bloqueantes = 0
    sugerencias = 0
    no_verificado = 0

    for f in findings:
        lines.append(f"[{f.severity}] {f.file}:{f.line} ({f.discipline}): {f.description}")
        if f.severity == "BLOQUEANTE":
            bloqueantes += 1
        elif f.severity == "SUGERENCIA":
            sugerencias += 1
        elif f.severity == "NO_VERIFICADO":
            no_verificado += 1

    if item_9_status == "NO_VERIFICADO" and no_verificado == 0:
        no_verificado = 1

    lines.append(f"RESUMEN: bloqueantes={bloqueantes}; sugerencias={sugerencias}; no_verificado={no_verificado}")
    return "\n".join(lines)


def summarize_escalation(mode: str, reason: str = "") -> str:
    """Produce el informe estructurado del resultado de triage / escalado de modo.

    Esquema v1. Es un documento DISTINTO al informe de hallazgos: su línea
    RESUMEN usa el formato ``modo=...; escalado=...``, no ``bloqueantes=...``.
    """
    lines: list[str] = [f"REPORT_SCHEMA_VERSION: {REPORT_SCHEMA_VERSION}", f"MODO: {mode}"]
    if reason:
        lines.append(f"MOTIVO: {reason}")
    escalado = "si" if mode != "Micro" else "no"
    lines.append(f"RESUMEN: modo={mode}; escalado={escalado}")
    return "\n".join(lines)
