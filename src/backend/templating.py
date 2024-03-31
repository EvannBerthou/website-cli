import jinja2

env = jinja2.Environment(
    loader=jinja2.PackageLoader("src.backend"),
    autoescape=jinja2.select_autoescape()
)


def render_template(template_name: str, context: dict):
    return env.get_template(template_name).render(**context)
