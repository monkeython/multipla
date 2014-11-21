"""Test third party plugin."""

__all__ = ['third_party']

third_party = object()

get_plugin = lambda: {'third_party', third_party}
