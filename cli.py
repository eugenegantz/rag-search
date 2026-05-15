#!/usr/bin/env python3
"""
RAG CLI -- клиент к единому демону.
Все команды работают через HTTP к daemon.py (модели загружены один раз).
"""

import os
import sys
import json
import subprocess
import signal
import time
import typing
from pathlib import Path
from typing import List

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from client import RAGClient, is_daemon_alive
from core.paths import PID_FILE, PORT_FILE
from app_config.config import config

app = typer.Typer(
    help="RAG CLI. Требует запущенного демона (python cli.py daemon start).",
    rich_markup_mode="rich",
)

console = Console()

DAEMON_HOST = config["daemon"]["host"]
DAEMON_PORT = config["daemon"]["port"]


# ═══════════════════════════════════════════════
# КОМАНДА: daemon (управление фоновым процессом)
# ═══════════════════════════════════════════════

@app.command()
def daemon(
    action: str = typer.Argument(..., help="start | stop | status | restart"),
    port: int = typer.Option(DAEMON_PORT, "--port", "-p"),
    force: bool = typer.Option(False, "--force", "-f", help="Force kill при остановке"),
):
    """
    Управление фоновым демоном RAG.
    """
    if action == "start":
        if is_daemon_alive():
            url = RAGClient().base_url
            console.print(f"[yellow]Демон уже запущен:[/yellow] {url}")
            raise typer.Exit(0)

        console.print(f"[blue]Запуск демона на порту {port}...[/blue]")
        console.print("[dim]Модели загружаются в фоне (~10-30 сек)...[/dim]")

        # Кросс-платформенный detached запуск
        popen_kwargs: dict[str, object] = dict(
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if sys.platform == "win32":
            popen_kwargs["creationflags"] = (
                subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            popen_kwargs["start_new_session"] = True

        proc = subprocess.Popen([sys.executable, "daemon.py"], **popen_kwargs) # type: ignore

        # Ждем, пока демон создаст PORT_FILE
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task("Ожидание инициализации...", total=None)
            for _ in range(60):  # Таймаут 60 сек
                time.sleep(1)
                if is_daemon_alive():
                    break
                if proc.poll() is not None:
                    console.print("[red]Демон упал при старте[/red]")
                    raise typer.Exit(1)
            else:
                console.print("[red]Таймаут ожидания демона[/red]")
                raise typer.Exit(1)

        console.print(f"[bold green]✓ Демон запущен[/bold green] на http://{DAEMON_HOST}:{port}")
        console.print("[dim]Веб-интерфейс: http://{host}:{port}[/dim]".format(host=DAEMON_HOST, port=port))

    elif action == "stop":
        if not is_daemon_alive():
            console.print("[yellow]Демон не запущен[/yellow]")
            PID_FILE.unlink(missing_ok=True)
            PORT_FILE.unlink(missing_ok=True)
            return

        if not force:
            # Graceful shutdown через API
            try:
                client = RAGClient()
                client.shutdown()
                # Ждем завершения до 5 сек
                for _ in range(5):
                    time.sleep(1)
                    if not is_daemon_alive():
                        break
                else:
                    console.print("[yellow]Graceful shutdown не удался, используем force...[/yellow]")
                    force = True
            except Exception as e:
                console.print(f"[yellow]Ошибка graceful shutdown: {e}, используем force...[/yellow]")
                force = True

        if force:
            if not PID_FILE.exists():
                console.print("[yellow]PID-файл не найден, чистим файлы[/yellow]")
            else:
                pid = int(PID_FILE.read_text().strip())
                try:
                    os.kill(pid, signal.SIGTERM)
                except ProcessLookupError:
                    console.print("[yellow]Процесс не найден, чистим файлы[/yellow]")

        PID_FILE.unlink(missing_ok=True)
        PORT_FILE.unlink(missing_ok=True)
        console.print("[bold green]✓ Демон остановлен[/bold green]")

    elif action == "status":
        if is_daemon_alive():
            client = RAGClient()
            health = client.health()
            console.print(f"[bold green]● Демон активен[/bold green] -- {client.base_url}")
            console.print(f"  backend ready: {health.get('backend_ready')}")
            console.print(f"  Веб-интерфейс: {client.base_url}")
        else:
            console.print("[bold red]● Демон остановлен[/bold red]")

    elif action == "restart":
        try:
            daemon("stop", force=force)
        except SystemExit:
            pass
        time.sleep(1)
        daemon("start", port=port)


# ═══════════════════════════════════════════════
# КОМАНДА: ask
# ═══════════════════════════════════════════════

@app.command()
def ask(
    query: str = typer.Argument(..., help="Поисковый запрос"),
    top_k: int = typer.Option(10, "--top-k", "-k"),
    raw: bool = typer.Option(False, "--raw", help="Сырой markdown без рендера"),
    json_output: bool = typer.Option(False, "--json", "-j"),
):
    """
    RAG-поиск по индексированным документам.
    """
    if not is_daemon_alive():
        console.print(
            "[bold red]Демон не запущен.[/bold red] "
            "Запустите: [bold]python cli.py daemon start[/bold]"
        )
        raise typer.Exit(1)

    try:
        client = RAGClient()
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task("Поиск...", total=None)
            res = client.search(query, top_k=top_k)
    except Exception as e:
        console.print(f"[red]Ошибка демона: {e}[/red]")
        raise typer.Exit(1)

    # --- Вывод результата ---
    if not res.get("results"):
        console.print("[red]Нет результатов[/red]")
        raise typer.Exit(1)

    result = res["results"][0]

    if result.get("error"):
        console.print(f"[bold red]Ошибка:[/bold red] {result['error']}")
        raise typer.Exit(1)

    if json_output:
        console.print(json.dumps(result, ensure_ascii=False, indent=4))
        return

    if raw:
        console.print(result["content"])
    else:
        md = Markdown(result["content"])
        console.print(Panel(md, title="Ответ", border_style="blue"))

    # Ссылки
    if result.get("refs"):
        table = Table(title="Источники", show_header=True)
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Файл", style="green")
        table.add_column("Примечание", style="dim")

        for ref in result["refs"]:
            table.add_row(
                ref.get("id", ""),
                Path(ref.get("filepath", "")).name,
                ref.get("note", ""),
            )
        console.print(table)


# ═══════════════════════════════════════════════
# КОМАНДА: index (подкоманды add / list / remove)
# ═══════════════════════════════════════════════

index_app = typer.Typer(
    help="Управление индексом документов",
    no_args_is_help=True,
)
app.add_typer(index_app, name="index")


@index_app.command("add")
def index_add(
    files: List[str] = typer.Argument(..., help="Файлы для индексации"),
):
    """
    Добавить документы в индекс.
    """
    if not is_daemon_alive():
        console.print(
            "[bold red]Демон не запущен.[/bold red] "
            "Запустите: [bold]python cli.py daemon start[/bold]"
        )
        raise typer.Exit(1)

    client = RAGClient()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task("Индексация...", total=None)
        res = client.index(files)

    if res.get("error"):
        console.print(f"[red]{res['error']}[/red]")
        raise typer.Exit(1)
    console.print(f"[green]✓ {res.get('message')}[/green]")


@index_app.command("list")
def index_list():
    """
    Показать индексированные файлы.
    """
    client = RAGClient()
    res = client.files()

    if res.get("error"):
        console.print(f"[red]{res['error']}[/red]")
        raise typer.Exit(1)

    filepaths: list[str] = res["filepaths"]

    if not filepaths:
        console.print("[yellow]Индекс пуст.[/yellow]")
        return

    table = Table(title="Индексированные документы")
    table.add_column("#", style="dim", justify="right")
    table.add_column("Путь к файлу", style="green")

    for i, fp in enumerate(filepaths, 1):
        table.add_row(str(i), fp)

    console.print(table)
    console.print(f"\nВсего: [bold]{len(filepaths)}[/bold] файлов")


@index_app.command("query")
def index_query(
    query: str = typer.Argument(..., help="Запрос"),
    format: str = typer.Option("table", "--format", "-f"),
    type_filter: str = typer.Option(None, "--type", help="Фильтр по типу: image"),
):
    """
    Поиск файлов без LLM.
    """
    client = RAGClient()

    query_args: dict[str, typing.Any] = {
        "query": query,
    }

    if "image" == type_filter:
        query_args["rtype"] = "image"

    res = client.index_query(**query_args)

    if res.get("error", ""):
        console.print(f"[red]{res['error']}[/red]")
        raise typer.Exit(1)

    metas: list[dict[str, str]] = res["meta"]

    if not metas:
        console.print("[yellow]Индекс пуст.[/yellow]")
        return
    
    if "list" == format or "ls" == format:
        for i, row in enumerate(metas):
            print(row["filepath"])
    else:
        table = Table(title="Файлы")
        table.add_column("#", style="dim", justify="right")
        table.add_column("Путь к файлу", style="green")

        for i, row in enumerate(metas):
            table.add_row(str(i), row["filepath"])

        console.print(table)
        console.print(f"\nВсего: [bold]{len(metas)}[/bold] файлов")


@index_app.command("remove")
def index_remove(
    filepath: str = typer.Argument(..., help="Файл для удаления из индекса"),
):
    """
    Удалить файл из индекса.
    """
    client = RAGClient()
    res = client.remove(filepath)

    if res.get("error", ""):
        console.print(f"[red]{res['error']}[/red]")
        raise typer.Exit(1)

    console.print(f"[green]✓ Удалено[/green]")



if __name__ == "__main__":
    app()
