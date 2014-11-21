"""Test pluggable module."""

__all__ = ['plugin']

plugin = object()

get_plugin = lambda: {'plugin', plugin}
