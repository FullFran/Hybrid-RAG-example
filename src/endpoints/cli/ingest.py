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
        description="Ingesta de documentos (Clean Architecture)"
    )
    parser.add_argument(
        "--documents", "-d", default="documents", help="Carpeta de documentos"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Borrar todos los documentos antes de empezar",
    )
    args = parser.parse_args()

    ingest_service = bootstrap_ingest_service()

    if args.clean:
        console.print("[yellow]Limpiando base de datos...[/yellow]")
        await ingest_service.clean()
        console.print("[green]Base de datos limpia.[/green]")
        if not args.documents or not os.path.exists(args.documents):
            return

    if not os.path.exists(args.documents):
        console.print(f"[red]Error: Directorio {args.documents} no encontrado.[/red]")
        return

    # Simple discovery for this example
    files = []
    for ext in ["*.pdf", "*.md", "*.txt", "*.docx"]:
        files.extend(glob.glob(os.path.join(args.documents, "**", ext), recursive=True))

    if not files:
        console.print("[yellow]No se encontraron archivos compatibles.[/yellow]")
        return

    console.print(f"Encontrados {len(files)} archivos para procesar.")

    with Progress() as progress:
        task = progress.add_task("[cyan]Ingestando...", total=len(files))

        for file_path in files:
            try:
                # We reuse the logic for reading but here we just simulate for brevity
                # In a real scenario, we'd use Docling here too or pass it to the service
                from src.ingestion.ingest import (
                    DocumentIngestionPipeline,
                    IngestionConfig,
                )

                # We can reuse the pipeline reader or move it to infra/docling
                pipeline = DocumentIngestionPipeline(IngestionConfig())
                content, docling_doc = pipeline._read_document(file_path)
                title = pipeline._extract_title(content, file_path)

                await ingest_service.ingest_file(
                    file_path=file_path,
                    content=content,
                    title=title,
                    docling_doc=docling_doc,
                )
                progress.update(task, advance=1)
            except Exception as e:
                console.print(f"[red]Error procesando {file_path}: {e}[/red]")

    console.print("\n[bold green]✓ Ingesta completada.[/bold green]")


if __name__ == "__main__":
    asyncio.run(main())
