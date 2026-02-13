__all__ = ["Config", "process_pdf", "run_gui"]


def __getattr__(name):
    if name == "Config":
        from .config import Config
        return Config
    if name == "process_pdf":
        from .pipeline import process_pdf
        return process_pdf
    if name == "run_gui":
        from .gui import run_gui
        return run_gui
    raise AttributeError(name)
