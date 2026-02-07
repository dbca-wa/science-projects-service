#!/bin/bash
# Wrapper to run flake8 and show output but never fail
poetry run flake8 "$@" >&2
exit 0
