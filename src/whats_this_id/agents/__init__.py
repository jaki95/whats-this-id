from importlib import import_module

# Lazy import to avoid heavy dependencies at package load time
__all__ = [
    "TracklistSearchCrew",
]


def __getattr__(name: str):
    if name == "TracklistSearchCrew":
        module = import_module("whats_this_id.agents.tracklist_finder.crew")
        return getattr(module, "TracklistSearchCrew")
    raise AttributeError(name)
