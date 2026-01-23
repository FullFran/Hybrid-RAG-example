import argparse
import asyncio
import glob
import os

from rich.console import Console
from rich.progress import Progress

from src.bootstrap import bootstrap_ingest_service

console = Console()


async def main():
    parser = argparse.ArgumentParser(
        description="Document Ingestion (Clean Architecture)"
    )
    parser.add_argument(
        "--documents", "-d", default="documents", help="Documents folder"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Wipe all documents before starting",
    )
    args = parser.parse_args()

    ingest_service = bootstrap_ingest_service()

    if args.clean:
        console.print("[yellow]Cleaning database...[/yellow]")
        await ingest_service.clean()
        console.print("[green]Database cleaned.[/green]")
        if not args.documents or not os.path.exists(args.documents):
            return

    if not os.path.exists(args.documents):
        console.print(f"[red]Error: Directory {args.documents} not found.[/red]")
        return

    # Simple discovery for this example
    files = []
    for ext in ["*.pdf", "*.md", "*.txt", "*.docx"]:
        files.extend(glob.glob(os.path.join(args.documents, "**", ext), recursive=True))

    if not files:
        console.print("[yellow]No compatible files found.[/yellow]")
        return

    console.print(f"Found {len(files)} files to process.")

    with Progress() as progress:
        task = progress.add_task("[cyan]Ingesting...", total=len(files))

        for file_path in files:
            try:
                await ingest_service.ingest_file(file_path=file_path)
                progress.update(task, advance=1)
            except Exception as e:
                console.print(f"[red]Error processing {file_path}: {e}[/red]")

    console.print("\n[bold green]✓ Ingestion completed.[/bold green]")


if __name__ == "__main__":
    asyncio.run(main())
