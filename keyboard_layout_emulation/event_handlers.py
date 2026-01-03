from __future__ import annotations

import bpy
from bpy.app.handlers import persistent

from .keymap_patch import reapply_keymap_translation, revert_keymap_translation
from .preferences import kle_prefs
from .constants import kle_logger

def maybe_reapply_translation_deferred(context=..., *, for_reload=True):
    prefs = kle_prefs(context)
    if prefs.is_emulation_active and prefs.reapply_on_reload:
        bpy.app.timers.register(
            lambda: maybe_reapply_translation(context, for_reload=for_reload),
            first_interval=0)
        deferred_wait_time = prefs.reapply_on_reload_delay
        if deferred_wait_time > 0:
            bpy.app.timers.register(
                lambda: maybe_reapply_translation(context, for_reload=for_reload),
                first_interval=deferred_wait_time)


def maybe_reapply_translation(context=..., *, for_reload=True):
    if context is ...:
        context = bpy.context

    prefs = kle_prefs(context)
    if not prefs.is_emulation_active or for_reload and not prefs.reapply_on_reload:
        return

    translation = prefs.get_preferred_layout_translation()

    success, msg = reapply_keymap_translation(translation, context)
    if not success:
        kle_logger.warn(f"Failed to apply layout emulation on reload:\n  {msg}")
    else:
        kle_logger.info(f"Applied layout emulation on reload:\n  {msg}")


def maybe_revert_translation_on_uninstall(context=...):
    if context is ...:
        context = bpy.context
    prefs = kle_prefs(context)
    ui_state = prefs.ui_state(context)
    if not prefs.is_emulation_active or not ui_state.revert_on_uninstall:
        return

    success, msg = revert_keymap_translation(context)
    if not success:
        kle_logger.warn(f"Failed to revert layout emulation on unload:\n  {msg}")
    else:
        kle_logger.info(f"Reverted keyboard layout emulation on unload:\n  {msg}")


def on_addons_set_change():
    maybe_reapply_translation_deferred(for_reload=False)

def on_reapply_requested():
    maybe_reapply_translation(for_reload=False)


@persistent
def on_load_post(*_, **__):
    """Re-register msgbus subscribers after loading a new file."""
    maybe_reapply_translation_deferred()


def register():
    # Register handlers
    bpy.app.handlers.load_post.append(on_load_post)
    bpy.app.handlers.load_post_fail.append(on_load_post)

    # Reapply translation if appropriate
    maybe_reapply_translation_deferred()

def unregister():
    # Revert translation if appropriate
    maybe_revert_translation_on_uninstall()

    # Unregister handlers
    bpy.app.handlers.load_post.remove(on_load_post)
    bpy.app.handlers.load_post_fail.remove(on_load_post)
