import asyncio
import logging

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from src.bootstrap import bootstrap_rag_service
from src.core.prompts import MAIN_SYSTEM_PROMPT
from src.settings import load_settings

# Configure logging to be quiet by default (silence httpx and others)
logging.basicConfig(level=logging.WARNING)
for logger_name in ["src", "httpx", "openai"]:
    logging.getLogger(logger_name).setLevel(logging.WARNING)

console = Console()


async def main():
    settings = load_settings()
    rag_service = bootstrap_rag_service()

    console.print(
        Panel(
            f"[bold blue]RAG Agent (Clean Architecture)[/bold blue]\n"
            f"LLM: [green]{settings.llm_model}[/green]\n"
            f"DB: [green]{settings.db_type.capitalize()}[/green]",
            style="blue",
        )
    )

    while True:
        try:
            query = Prompt.ask("\n[bold green]Pregunta").strip()

            if query.lower() in ["exit", "quit", "q"]:
                break

            if not query:
                continue

            # --- Reasoning Flow ---
            with console.status(
                "[bold blue]Analizando y buscando en la base de conocimientos...",
                spinner="dots",
            ):
                matches, search_query = await rag_service.search(query, limit=5)

            # Show the "thinking" result
            if search_query.lower() != query.lower():
                console.print(
                    f"[dim]🔎 Buscando por: [italic]{search_query}[/italic][/dim]"
                )

            if not matches:
                console.print(
                    "[yellow]No se encontró información relevante para esta consulta. Respondiendo con conocimiento general...[/yellow]"
                )
            else:
                unique_docs = list(set([m.document_title for m in matches]))
                console.print(
                    f"[dim]🔍 Encontrados {len(matches)} fragmentos en: [italic]{', '.join(unique_docs)}[/italic][/dim]"
                )

            console.print("[bold blue]Asistente:[/bold blue] ", end="")

            # --- Stream Response ---
            response = await rag_service.answer(query, MAIN_SYSTEM_PROMPT)

            if isinstance(response, str):
                console.print(response)
            else:
                async for chunk in response:
                    console.print(chunk, end="")
                console.print()

            # --- Show Sources ---
            if matches:
                sources_text = "\n".join(
                    [f"• {m.document_title} ({m.document_source})" for m in matches[:3]]
                )
                console.print(
                    Panel(
                        f"[bold dim]Fuentes utilizadas:[/bold dim]\n{sources_text}",
                        style="dim",
                        padding=(0, 1),
                    )
                )

        except KeyboardInterrupt:
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


if __name__ == "__main__":
    asyncio.run(main())
