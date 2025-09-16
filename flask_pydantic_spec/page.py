from flask import (
    Blueprint,
    Flask,
    jsonify,
    redirect,
    render_template,
)
from typing import Callable, TYPE_CHECKING
from werkzeug import Response as WerkzeugResponse

if TYPE_CHECKING:
    from .spec import FlaskPydanticSpec


def render_doc(*, spec: "FlaskPydanticSpec", doc_name: str) -> str:
    return render_template(
        [f"{prefix.rstrip('/')}/{doc_name}" for prefix in spec.config.TEMPLATE_DIRS],
        config=spec.config,
    )


def default_redirect(spec: "FlaskPydanticSpec") -> WerkzeugResponse:
    return redirect(f"./{spec.config.UI}", 307)


def register_pages(
    spec: "FlaskPydanticSpec",
    bp: Blueprint | Flask,
    *,
    create_sub_bp: str | None = "apidoc",
    add_template_paths: bool = True,
) -> None:
    sub_bp: Blueprint | Flask
    if create_sub_bp:
        sub_bp = Blueprint(
            create_sub_bp,
            __name__,
            template_folder="templates",
        )
        sub_bp.add_url_rule(
            f"/{spec.config.PATH}/",
            "index",
            lambda: default_redirect(spec=spec),
        )
    else:
        sub_bp = bp

    # create the lambda in a function to work around weird doc_name re-binding in for-loop
    def make_doc_route(doc_name: str) -> Callable[[], str]:
        return lambda: render_doc(spec=spec, doc_name=doc_name)

    for route in spec.config._SUPPORT_UI:
        sub_bp.add_url_rule(
            f"/{spec.config.PATH}/{route}",
            route,
            make_doc_route(f"{route}.html"),
        )

    sub_bp.add_url_rule(spec.config.spec_url, "openapi", lambda: jsonify(spec.spec))
    if create_sub_bp:
        assert isinstance(sub_bp, Blueprint)
        bp.register_blueprint(sub_bp)
