# to-codigo

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![PyPI](https://img.shields.io/badge/PyPI-to--codigo-orange)

```
  ████████╗ ██████╗ ███████╗███╗   ██╗
  ╚══██╔══╝██╔═══██╗██╔════╝████╗  ██║
     ██║   ██║   ██║█████╗  ██╔██╗ ██║
     ██║   ██║   ██║██╔══╝  ██║╚██╗██║
     ╚██████╔╝███████╗███████╗██║ ╚████║
     ╚═╝    ╚═════╝ ╚══════╝╚═╝  ╚═══╝

  v1.0.0  —  Analizador de Código e Inventario
```

---

## Español

**to-codigo** es un analizador de código e inventario de proyectos que escanea directorios completos, detecta automáticamente el lenguaje de programación de cada archivo, y genera métricas detalladas: líneas de código, comentarios y líneas en blanco.

### Características

- **Detección automática de 40+ lenguajes** — Python, JavaScript, TypeScript, Java, C/C++, Go, Rust, Ruby, PHP, y más.
- **Conteo inteligente de comentarios** — Motor basado en datos (data-driven) que soporta comentarios de línea, bloque, y multilinea para cada lenguaje.
- **TODO/FIXME/HACK tracking** — Detecta marcadores `TODO`, `FIXME`, `HACK`, `XXX`, `BUG`, `NOTE` en comentarios con números de línea.
- **HTML Dashboard** — Reporte HTML autocontenido (offline) con tarjetas de resumen, gráficos de barras CSS, gráficos de pie SVG, tabla ordenable, top 10 archivos y sección de deuda técnica.
- **Markdown Report** — Reporte `.md` con tablas GitHub, top files y sección de TODOs.
- **Diff Mode** — Compara el scan actual con un reporte JSON anterior para ver crecimiento/shrink por lenguaje.
- **Top N Files** — Muestra los N archivos más grandes por LOC.
- **Shell Completion** — Genera scripts de autocompletado para bash, zsh y fish.
- **Multiprocessing** — Procesamiento paralelo con `ProcessPoolExecutor` para escanear repositorios grandes rápidamente.
- **5 formatos de salida** — CSV, Excel (XLSX), JSON, HTML Dashboard y Markdown.
- **Audit Tracking** — Modo de seguimiento de auditoría donde **el Excel es la fuente de verdad**. El auditor marca archivos directamente en el Excel con dropdowns (Si/No). La herramienta detecta archivos modificados (por tamaño + fecha) entre escaneos y señala cuáles necesitan re-auditoría. Estados: Auditado, Pendiente, Modificado, Nuevo.
- **Soporte .gitignore** — Respeta tus reglas de gitignore cuando lo necesites.
- **Detección por shebang** — Identifica scripts sin extensión (`#!/usr/bin/env python3`).
- **CLI con Rich UX** — Banner ASCII, barra de progreso, tabla de resultados con colores.
- **Bug-free** — Incluye el fix para el bug de comentarios `#` en PHP (que versiones anteriores ignoraban).
- **Docker** — Listo para correr en contenedores.

### Instalación

```bash
pip install to-codigo
```

### Inicio rápido

```bash
# Escanear el directorio actual (genera reporte.csv)
to-codigo .

# HTML Dashboard interactivo
to-codigo . -o dashboard --format html

# Excel con estilos
to-codigo ./src -o mi-reporte --format xlsx

# Markdown para pegar en GitHub
to-codigo . --format md

# TODO tracking + Top 10 archivos
to-codigo . --todos --top 10

# Diff contra un reporte anterior
to-codigo . --format json -o current --diff previous.json

# Shell completion
to-codigo --completion bash > /etc/bash_completion.d/to-codigo
```

---

## English

**to-codigo** is a code analyzer and project inventory tool that scans directories, auto-detects the programming language of each file, and generates detailed metrics: code lines, comment lines, and blank lines.

### Features

- **Auto-detection of 40+ languages** — Python, JavaScript, TypeScript, Java, C/C++, Go, Rust, Ruby, PHP, and more.
- **Intelligent comment counting** — Data-driven engine supporting line comments, block comments, and multi-line comments per language.
- **TODO/FIXME/HACK tracking** — Detects `TODO`, `FIXME`, `HACK`, `XXX`, `BUG`, `NOTE` markers in comments with line numbers.
- **HTML Dashboard** — Self-contained HTML report (offline) with summary cards, CSS bar charts, SVG pie charts, sortable table, top 10 files and tech debt section.
- **Markdown Report** — `.md` report with GitHub tables, top files and TODO section.
- **Diff Mode** — Compare current scan against a previous JSON report to see growth/shrink per language.
- **Top N Files** — Show the top N files by LOC.
- **Shell Completion** — Generate completion scripts for bash, zsh and fish.
- **Multiprocessing** — Parallel processing via `ProcessPoolExecutor` for fast scanning of large repos.
- **5 output formats** — CSV, Excel (XLSX), JSON, HTML Dashboard and Markdown.
- **Audit Tracking** — Security audit mode where **Excel is the source of truth**. The auditor marks files directly in the Excel using dropdowns (Si/No). The tool detects modified files (by size + mtime) between scans and flags which ones need re-auditing. States: Auditado, Pendiente, Modificado, Nuevo.
- **.gitignore support** — Honors your gitignore rules when needed.
- **Shebang detection** — Identifies extensionless scripts (`#!/usr/bin/env python3`).
- **Rich CLI UX** — ASCII banner, progress bar, color-coded results table.
- **Bug-free** — Includes the PHP `#` comment fix (previous versions missed this).
- **Docker** — Container-ready.

### Installation

```bash
pip install to-codigo
```

### Quick Start

```bash
# Scan current directory (generates reporte.csv)
to-codigo .

# Interactive HTML Dashboard
to-codigo . -o dashboard --format html

# Styled Excel
to-codigo ./src -o my-report --format xlsx

# Markdown for GitHub
to-codigo . --format md

# TODO tracking + Top 10 files
to-codigo . --todos --top 10

# Diff against previous report
to-codigo . --format json -o current --diff previous.json

# Shell completion
to-codigo --completion zsh >> ~/.zshrc
```

---

## CLI Flags

| Flag | Description | Default |
|------|-------------|---------|
| `ruta_raiz` | Directorio a escanear (posicional) | `.` |
| `-o, --output` | Nombre base del archivo de salida | `reporte` |
| `--format` | Formato de salida: `csv`, `xlsx`, `json`, `html`, `md` | `csv` |
| `--todos` | Escanear TODO/FIXME/HACK/NOTE markers | Off |
| `--top N` | Mostrar top N archivos por LOC | Off (0) |
| `--diff PATH` | Comparar contra reporte JSON anterior | Off |
| `--completion` | Generar autocompletado: `bash`, `zsh`, `fish` | — |
| `--exclude-dirs` | Directorios a excluir | `.git node_modules __pycache__ .vscode ...` |
| `--exclude-ext` | Extensiones a excluir (`.log .tmp`) | None |
| `--include-ext` | Solo escanear estas extensiones | All |
| `--no-recursive` | No descender a subdirectorios | Recursive |
| `--respect-gitignore` | Respetar `.gitignore` | Off |
| `--workers` | Procesos paralelos | CPU count |
| `--verbose` | Mostrar warnings de archivos omitidos | Off |
| `--no-banner` | Omitir el banner ASCII | Show banner |
| `--version` | Mostrar version | — |
| `--audit` | Habilitar modo de seguimiento de auditoria (Excel como estado) | Off |

## Output Formats

### CSV
Reporte RFC 4180 con una fila por archivo (incluye columnas TODOs y FIXMEs) + sección de resumen por lenguaje al final. Con `--audit`, añade columnas `Auditado` y `Estado` y una sección `Resumen de Auditoria` al final.

### XLSX
Excel con headers estilizados (azul), auto-filtro, filas congeladas, y sección de resumen (naranja) con totales por lenguaje. Incluye columnas TODOs y FIXMEs. Con `--audit`, añade:
- Columna `Auditado` con **data validation dropdown** (Si/No) — el auditor hace clic y selecciona
- Columna `Estado` (Auditado / Pendiente / Modificado / Nuevo) — solo lectura
- **Conditional formatting**: verde (Auditado), amarillo (Modificado), azul (Nuevo)
- Sección `Resumen de Auditoria` con conteos y LOC por estado
- Requiere `openpyxl`.

### JSON
JSON estructurado con array `files` (detalle por archivo con campos todos/fixmes/hacks/notes) y objeto `summary` (totales por lenguaje). Incluye timestamp de generación. Con `--audit`, cada archivo incluye `audit_status` y `audit_marked`, y se añade `audit_summary` a nivel raíz.

### HTML Dashboard
Dashboard HTML autocontenido (sin dependencias externas, funciona offline). Incluye:
- Banner ASCII en bloque `<pre>` estilizado
- **Tarjetas de resumen**: Total archivos, Total LOC, Total comentarios, Lenguajes detectados
- **Gráfico de barras**: LOC por lenguaje (barras CSS puras)
- **Gráfico de pie**: Distribución de archivos por lenguaje (SVG inline con stroke-dasharray)
- **Tabla ordenable**: Desglose detallado por archivo (sort vanilla JS)
- **Top 10 archivos** por LOC en sección destacada
- **Sección de Deuda Técnica**: TODOs/FIXMEs/HACKs agrupados por tipo
- Tema oscuro (Tokyo Night palette): background `#1a1b26`, accent cyan `#7dcfff`, green `#9ece6a`, orange `#ff9e64`, red `#f7768e`
- CSS responsivo (flexbox/grid)
- Timestamp de generación al pie

```bash
to-codigo . --format html -o dashboard
# Genera dashboard.html — ábrelo en cualquier navegador
```

Con `--audit`, el dashboard incluye además:
- **Barra de progreso de auditoría** con % auditado (LOC)
- **Tarjetas de auditoría**: Auditados, Modificados, Nuevos, Pendientes, % Progreso
- **Columna de checkboxes** interactiva en la tabla (clic para marcar/desmarcar)
- **Columna Estado** con badges de colores: Auditado (verde ✓), Pendiente (gris), Modificado (naranja ⚠), Nuevo (azul +)
- **Botones de filtro**: Todos / Auditados / Modificados / Nuevos / Pendientes
- **Exportar a Excel** (descarga CSV con estado actual)
- **Auto-save** en localStorage con indicador "Guardado ✓"
- **Actualización en tiempo real** de progreso al marcar checkboxes

### Markdown
Reporte `.md` con tablas GitHub-flavored, sección de top 10 archivos y sección de deuda técnica. Con `--audit`, añade columna `Auditado` (✓/✗) y sección `Audit Summary`.

```bash
to-codigo . --format md -o report
# Genera report.md — pégalo en cualquier README, issue o wiki
```

---

## Audit Tracking

El modo de auditoría permite a los auditores de seguridad rastrear qué archivos han sido revisados durante una auditoría de código. **El Excel/CSV/JSON es la fuente de verdad** — no hay archivo de estado separado.

### Flujo de trabajo

```bash
# 1. Primera ejecución: genera Excel con columnas Auditado (todas "No") y Estado (todas "Nuevo")
to-codigo ./project --audit --format xlsx -o reporte

# 2. El auditor abre el Excel, marca "Auditado = Si" en los archivos revisados, guarda y cierra

# 3. Segunda ejecución: la herramienta detecta el Excel anterior
to-codigo ./project --audit --format xlsx -o reporte

# La herramienta compara tamaño + fecha de modificación de cada archivo contra el reporte anterior:
# - Auditado: marcado "Si" Y sin cambios → mantiene la marca
# - Pendiente: marcado "No" Y sin cambios → sigue pendiente
# - Modificado: marcado "Si" PERO el archivo cambió → RESET a "No" (¡re-auditar!)
# - Nuevo: archivo no estaba en el reporte anterior
```

### Detección de cambios

```
                          Detección de Cambios
╭──────────────────────────────────┬────────────┬───────────────────────────────╮
│ Estado                           │   Cantidad │ Detalle                       │
├──────────────────────────────────┼────────────┼───────────────────────────────┤
│ Auditados sin cambios            │        450 │ ████████████░░░░░░  15.4%     │
│ Archivos modificados (Alerta!)   │         23 │ Requieren re-auditoría        │
│ Archivos nuevos                  │         67 │ Sin auditar                   │
│ Archivos pendientes              │      2,381 │ Sin auditar                   │
│ Archivos eliminados              │         12 │ Ya no existen                 │
╰──────────────────────────────────┴────────────┴───────────────────────────────╯
```

### Estados de auditoría

| Estado | Descripción | Color en Excel | Marca Auditado |
|--------|-------------|----------------|----------------|
| **Auditado** | Revisado y sin cambios desde el último escaneo | Verde claro | Si |
| **Pendiente** | No revisado y sin cambios | Default | No |
| **Modificado** | Fue revisado PERO el archivo cambió (necesita re-auditoría) | Amarillo claro | No (reset) |
| **Nuevo** | No estaba en el reporte anterior | Azul claro | No |

---

## TODO/FIXME Tracking

Usa `--todos` para escanear marcadores en comentarios:

```bash
to-codigo . --todos
```

Detecta `TODO`, `FIXME`, `HACK`, `XXX`, `BUG`, `NOTE` con números de línea exactos. Los marcadores aparecen en:
- La tabla de resumen por lenguaje (columnas TODOs y FIXMEs)
- Una tabla dedicada de Tech Debt con colores por tipo
- Todos los formatos de reporte (CSV, XLSX, JSON, HTML, Markdown)

---

## Top Files

Usa `--top N` para ver los N archivos más grandes:

```bash
to-codigo . --top 10
```

---

## Diff Mode

Compara el scan actual con un reporte JSON anterior:

```bash
# Genera reporte base
to-codigo . --format json -o baseline

# ... tiempo después, haz cambios al código ...

# Compara
to-codigo . --format json -o current --diff baseline.json
```

Muestra:
- Crecimiento/shrink de LOC por lenguaje (verde ↑ / rojo ↓)
- Archivos agregados, removidos y modificados
- TODOs nuevos vs resueltos

---

## Docker

```bash
# Build
docker build -t to-codigo .

# Run
docker run --rm -v "$(pwd):/app" to-codigo .

# HTML Dashboard
docker run --rm -v "$(pwd):/app" to-codigo . --format html -o /app/dashboard
```

---

## Shell Completion

Genera scripts de autocompletado para bash, zsh o fish:

```bash
# Bash
to-codigo --completion bash | sudo tee /etc/bash_completion.d/to-codigo

# Zsh
to-codigo --completion zsh > "${fpath[1]}/_to-codigo"

# Fish
to-codigo --completion fish > ~/.config/fish/completions/to-codigo.fish
```

---

## CI (GitHub Actions)

Incluye `.github/workflows/ci.yml` que corre los tests en Python 3.10, 3.11, 3.12 y 3.13:

```yaml
on: [push, pull_request]
jobs:
  test:
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12', '3.13']
```

---

## Supported Languages

Python, JavaScript, TypeScript, React (JS/TS), Java, C#, C, C++, Go, Rust, Ruby, PHP, Perl, Shell, Bash, SQL, HTML, CSS, SCSS, Sass, Less, XML, JSON, YAML, Markdown, R, MATLAB, Swift, Kotlin, Scala, Clojure, Haskell, Lua, Dart, Elixir.

## Examples

```bash
# Reporte completo de un proyecto Angular
to-codigo ./my-angular-app --format html --exclude-dirs node_modules dist

# Solo metricas de codigo con TODOs
to-codigo . --include-ext .py .ts .js .go .rs --format json --todos

# HTML dashboard con top 20 archivos
to-codigo . --format html --top 20

# Escaneo rapido sin recursividad
to-codigo . --no-recursive --format csv
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).
