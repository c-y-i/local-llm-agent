#!/usr/bin/env python3
"""Read-only local LLM stack monitor. Run with: python3 monitor.py"""
import control_panel as _app

_app.APP_TITLE = "Local LLM Monitor"
_app.APP_EYEBROW = "Read-only runtime"
_app.APP_SUBTITLE = "Monitor services, runtime health, loaded models, GPU, CPU, and memory without exposing control actions."
_app.DEFAULT_CONTROLS = "0"
_app.DEFAULT_PORT = "8765"

from control_panel import *  # noqa: F401,F403,E402


if __name__ == "__main__":
    _app.main()
