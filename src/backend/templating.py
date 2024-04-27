import jinja2

env = jinja2.Environment(
    loader=jinja2.PackageLoader("src.backend"),
    autoescape=jinja2.select_autoescape(),
    trim_blocks=True,
    lstrip_blocks=True
)


def render_template(template_name: str, context: dict) -> str:
    return env.get_template(template_name).render(**context)
