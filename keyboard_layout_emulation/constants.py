from __future__ import annotations

import logging


__all__ = [
    'addon_id',
    'preferences_version',
    'KLEOperators',
    'kle_logger',
]


addon_id = __package__
preferences_version = (1, 0)


class KLEOperators:
    """Operator IDs"""
    apply_layout_emulation = "wm.kle_apply_layout_emulation"  # WM_OT_kle_apply_layout_emulation
    revert_layout_emulation = "wm.kle_revert_layout_emulation"  # WM_OT_kle_revert_layout_emulation
    add_custom_layout = "wm.kle_add_custom_layout"  # WM_OT_kle_add_custom_layout
    remove_custom_layout = "wm.kle_remove_custom_layout"  # WM_OT_kle_remove_custom_layout
    export_layout_json = "wm.kle_export_layout_json"  # WM_OT_kle_export_layout_json
    import_layout_json = "wm.kle_import_layout_json"  # WM_OT_kle_import_layout_json
    export_addon_preferences = "wm.kle_export_layout_preferences"  # WM_OT_kle_export_addon_preferences
    import_addon_preferences = "wm.kle_import_layout_preferences"  # WM_OT_kle_import_addon_preferences
    toggle_edit_layout = "wm.kle_toggle_edit_layout"  # WM_OT_kle_toggle_edit_layout
    toggle_keymaps_panel_preferences = "wm.kle_toggle_keymaps_panel_preferences"  # WM_OT_kle_toggle_keymaps_panel_preferences
    capture_key_for_mapping = "wm.kle_capture_key_for_mapping"  # WM_OT_kle_capture_key_for_mapping
    debug_toggle_expanded_subkey = "wm.kle_debug_toggle_expanded_subkey"  # WM_OT_kle_debug_toggle_expanded_subkey

    class Info:
        """No-op operators used only to display tooltips."""
        non_editable_key = "wm.kle_non_editable_key"  # WM_OT_kle_non_editable_key
        layout_unlocked = "wm.kle_layout_unlocked_info"  # WM_OT_kle_layout_unlocked_info
        layout_locked = "wm.kle_layout_locked_info"  # WM_OT_kle_layout_locked_info
        addon_info = "wm.kle_addon_info"  # WM_OT_kle_addon_info


_kle_logger_formatter = logging.Formatter('%(asctime)s [Keyboard Layout Emulation] %(message)s')
_kle_logger_handler = logging.StreamHandler()
_kle_logger_handler.setFormatter(_kle_logger_formatter)

kle_logger = logging.getLogger(__package__)
kle_logger.setLevel(logging.INFO)
kle_logger.addHandler(_kle_logger_handler)
