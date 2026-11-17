from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

env = Environment(
    loader=FileSystemLoader(Path(__file__).parent / "templates"), autoescape=True
)


def build_pdf(filename: str, summary: dict, sandbox: bool) -> bytes:
    html = env.get_template("laporan.html").render(
        filename=filename,
        date=datetime.now().strftime("%d %B %Y %H:%M"),
        sandbox=sandbox,
        **summary,
    )
    return HTML(string=html).write_pdf()
