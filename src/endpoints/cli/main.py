import asyncio
import logging

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from src.bootstrap import bootstrap_agent_service
from src.core.prompts import MAIN_SYSTEM_PROMPT
from src.settings import load_settings

# Configure logging - silence all debug output
logging.basicConfig(level=logging.ERROR)
for name in ["httpx", "httpcore", "hpack", "openai", "src"]:
    logging.getLogger(name).setLevel(logging.ERROR)

console = Console()


async def main():
    settings = load_settings()
    agent = bootstrap_agent_service()

    console.print(
        Panel(
            f"[bold blue]RAG Agent (ReAct Mode)[/bold blue]\n"
            f"LLM: [green]{settings.llm_model}[/green]\n"
            f"DB: [green]{settings.db_type.capitalize()}[/green]\n"
            f"Mode: [yellow]Conservative (busca si hay duda)[/yellow]",
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

            with console.status(
                "[bold blue]El agente está decidiendo cómo responder...",
                spinner="dots",
            ):
                # The agent decides whether to search or respond directly
                result = await agent.chat(query, MAIN_SYSTEM_PROMPT, limit=5)

            # --- Explainability: Show reasoning ---
            if result.searched:
                console.print(
                    "[dim]🤖 Decisión: [bold]BUSCAR[/bold] en la base de conocimientos[/dim]"
                )
                if result.search_query:
                    console.print(
                        f"[dim]🔎 Buscando por: [italic]{result.search_query}[/italic][/dim]"
                    )
            else:
                console.print(
                    "[dim]🤖 Decisión: Responder [bold]DIRECTAMENTE[/bold] (conocimiento general)[/dim]"
                )

            console.print("[bold blue]Asistente:[/bold blue] ", end="")

            # --- Stream Response ---
            response = result.response
            if isinstance(response, str):
                console.print(response)
            else:
                async for chunk in response:
                    console.print(chunk, end="")
                console.print()

            # --- Show Sources ---
            if result.searched and result.matches:
                sources_text = "\n".join(
                    [
                        f"• {m.document_title} ({m.document_source})"
                        for m in result.matches[:3]
                    ]
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
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
