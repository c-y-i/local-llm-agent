"""Shared path configuration for the local-llm-agent CLI and dashboards."""

from __future__ import annotations

import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
ENV_FILE = REPO_ROOT / ".env"
ENV_EXAMPLE = REPO_ROOT / ".env.example"

_PARAM_EXPANSION = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*):-([^}]*)\}")


def _expand(value: str) -> str:
    def replace(match: re.Match[str]) -> str:
        name, default = match.groups()
        return os.environ.get(name) or _expand(default)

    previous = None
    while previous != value:
        previous = value
        value = _PARAM_EXPANSION.sub(replace, value)
    return os.path.expandvars(os.path.expanduser(value))


def load_env_file(path: Path = ENV_FILE) -> None:
    """Load simple KEY=VALUE entries without executing the file."""
    if not path.is_file():
        return
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        os.environ[key] = _expand(value)


def get_paths() -> dict[str, Path]:
    load_env_file()
    llm_root = Path(os.environ.get("LLM_ROOT", "~/LLM")).expanduser().resolve()
    values = {
        "llm_root": llm_root,
        "models": Path(os.environ.get("LLM_MODELS_DIR", llm_root / "models")),
        "llama_cpp": Path(os.environ.get("LLAMA_CPP_ROOT", llm_root / "llama.cpp")),
        "ollama": Path(os.environ.get("OLLAMA_ROOT", llm_root / "ollama")),
        "ollama_models": Path(
            os.environ.get("OLLAMA_MODELS", llm_root / "ollama" / "models" / "llm")
        ),
        "hf_home": Path(os.environ.get("HF_HOME", llm_root / "huggingface")),
        "strata_home": Path(os.environ.get("STRATA_HOME", llm_root / "strata")),
        "strata_models": Path(
            os.environ.get("STRATA_MODELS_DIR", llm_root / "models" / "strata")
        ),
        "venvs": Path(os.environ.get("LLM_VENVS_DIR", llm_root / "venvs")),
        "run": Path(os.environ.get("LLM_RUN_DIR", llm_root / "run")),
    }
    return {name: path.expanduser().resolve() for name, path in values.items()}


def ensure_directories(paths: dict[str, Path] | None = None) -> dict[str, Path]:
    paths = paths or get_paths()
    for name in (
        "llm_root",
        "models",
        "llama_cpp",
        "ollama",
        "ollama_models",
        "hf_home",
        "strata_home",
        "strata_models",
        "venvs",
        "run",
    ):
        paths[name].mkdir(parents=True, exist_ok=True)
    return paths


def export_paths(paths: dict[str, Path] | None = None) -> None:
    paths = paths or get_paths()
    exports = {
        "LLM_ROOT": "llm_root",
        "LLM_MODELS_DIR": "models",
        "LLAMA_CPP_ROOT": "llama_cpp",
        "OLLAMA_ROOT": "ollama",
        "OLLAMA_MODELS": "ollama_models",
        "HF_HOME": "hf_home",
        "STRATA_HOME": "strata_home",
        "STRATA_MODELS_DIR": "strata_models",
        "LLM_VENVS_DIR": "venvs",
        "LLM_RUN_DIR": "run",
    }
    for env_name, path_name in exports.items():
        os.environ[env_name] = str(paths[path_name])
