import typer

app = typer.Typer(
    name="datapulse",
    help="Profile datasets and benchmark analytical engines.",
)


@app.callback()
def main() -> None:
    """DataPulse command-line application."""
