import os
from dataclasses import dataclass

from latex_parser.renderer import LatexBackend, parse_backend


@dataclass(frozen=True)
class Config:
    """Bot configuration loaded from environment variables."""

    telegram_token: str
    backend: LatexBackend
    max_expressions: int

    @classmethod
    def from_env(cls) -> "Config":
        token = os.getenv("TELEGRAM_TOKEN", "").strip()
        if not token:
            raise ValueError(
                "TELEGRAM_TOKEN environment variable is required but not set."
            )

        backend_raw = os.getenv("LATEX_BACKEND", "matplotlib")
        try:
            backend = parse_backend(backend_raw)
        except ValueError:
            backend = LatexBackend.MATPLOTLIB

        max_expr_raw = os.getenv("MAX_EXPRESSIONS_PER_MESSAGE", "5")
        try:
            max_expressions = int(max_expr_raw)
            if max_expressions < 1:
                raise ValueError
        except ValueError:
            max_expressions = 5

        return cls(
            telegram_token=token,
            backend=backend,
            max_expressions=max_expressions,
        )
