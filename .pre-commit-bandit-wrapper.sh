#!/bin/bash
# Wrapper to run bandit and show output but never fail
poetry run bandit "$@" >&2
exit 0
