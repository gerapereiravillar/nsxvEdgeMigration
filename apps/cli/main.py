import typer
from pathlib import Path
from apps.cli.wiring import export_edge_xml_usecase

app = typer.Typer()

@app.command()
def export(org: str, edge: str, out: Path = Path("edge.xml")):
    export_edge_xml = export_edge_xml_usecase()
    data = export_edge_xml(org, edge)
    out.write_bytes(data)
    typer.echo(f"Saved -> {out}")

if __name__ == "__main__":
    app()
