"""
Keyboard Layout Emulation - Blender add-on

Automatically reassigns all keyboard shortcuts to emulate a QWERTY keyboard layout on a
user-specified non-QWERTY keyboard layout, allowing users to type QWERTY keyboard shortcuts
while typing text in their preferred keyboard layout.

See https://endorh.github.io/blender-extensions/keyboard-layout-emulation/
"""

from . import constants, preferences, operators, ui, event_handlers

__all__ = [
    # Registration handles
    'register',
    'unregister',
    # Submodules
    'constants',
    'preferences',
    'operators',
    'ui',
    'event_handlers',
]

registered_modules = (
    preferences,
    operators,
    ui,
    event_handlers,
)

def register():
    for module in registered_modules:
        module.register()
def unregister():
    for module in reversed(registered_modules):
        module.unregister()
