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

    # ui_state = prefs.ui_state(context)
    # if ui_state.is_emulation_applied:
    #     kle_logger.info(f"Layout emulation was already applied to keymap, skipping this pass.")
    #     return
    translation = prefs.get_preferred_layout_translation()

    success, msg = reapply_keymap_translation(translation, context)
    if not success:
        kle_logger.warn(f"Failed to apply layout emulation on reload:\n  {msg}")
    else:
        kle_logger.info(f"Applied layout emulation on reload:\n  {msg}")

    # ui_state.is_emulation_applied = True


def maybe_revert_translation_on_uninstall(context=...):
    if context is ...:
        context = bpy.context
    prefs = kle_prefs(context)
    ui_state = prefs.ui_state(context)
    if not prefs.is_emulation_active or not ui_state.revert_on_uninstall:
        return

    # if not ui_state.is_emulation_applied:
    #     kle_logger.info(f"Layout emulation was already reverted, skipping this pass during unload.")
    #     return

    success, msg = revert_keymap_translation(context)
    if not success:
        kle_logger.warn(f"Failed to revert layout emulation on unload:\n  {msg}")
    else:
        kle_logger.info(f"Reverted keyboard layout emulation on unload:\n  {msg}")

    # ui_state.is_emulation_applied = False


def on_addons_set_change():
    maybe_reapply_translation_deferred(for_reload=False)

def on_reapply_requested():
    maybe_reapply_translation(for_reload=False)

# _msgbus_subscriber_owner = object()
# def register_msgbus_subscribers():
#     pass
#     # This doesn't work, `Preferences.addons` is not an RNA property
#     # bpy.msgbus.subscribe_rna(
#     #     key=(bpy.types.Preferences, "addons"),
#     #     owner=_msgbus_subscriber_owner,
#     #     args=(),
#     #     notify=on_addon_set_change,
#     # )
#
# def unregister_msgbus_subscribers():
#     bpy.msgbus.clear_by_owner(_msgbus_subscriber_owner)


@persistent
def on_load_post(*_, **__):
    """Re-register msgbus subscribers after loading a new file."""
    # register_msgbus_subscribers()
    maybe_reapply_translation_deferred()


def register():
    # Register handlers
    bpy.app.handlers.load_post.append(on_load_post)
    bpy.app.handlers.load_post_fail.append(on_load_post)
    # register_msgbus_subscribers()

    # Reapply translation if appropriate
    maybe_reapply_translation_deferred()

def unregister():
    # Revert translation if appropriate
    maybe_revert_translation_on_uninstall()

    # Unregister handlers
    # unregister_msgbus_subscribers()
    bpy.app.handlers.load_post.remove(on_load_post)
    bpy.app.handlers.load_post_fail.remove(on_load_post)
