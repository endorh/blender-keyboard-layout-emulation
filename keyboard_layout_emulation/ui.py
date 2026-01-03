from __future__ import annotations
import sys
import time
from typing import List, Dict

import bpy
# noinspection PyUnresolvedReferences
from bpy.types import AddonPreferences, Operator, Panel, PropertyGroup

from .keyboard_layout import is_built_in_layout
from .preferences import kle_prefs, KLEPreferencesUnavailableException
from .operators import KLEOperators
from .constants import KLELinks, kle_logger

is_mac = sys.platform == 'darwin'

# Layout used to render a keyboard-like button grid
KEYBOARD_EDITOR_LAYOUT: List[List[Dict[str, object]]] = [
    # Function row
        [{"editable": False, "label": "Esc", "w": 1.2}] +
        [{"editable": False, "label": f"F{i}"} for i in range(1, 13)],
    # Number row
        [{"ch": "`", "w": 1.0}] +
        [{"ch": c} for c in "1234567890-="] +
        [{"editable": False, "label": "Backspace", "w": 2.0}],
    # First row
        [{"editable": False, "label": "Tab", "w": 1.5}] +
        [{"ch": c} for c in "QWERTYUIOP[]"] +
        [{"ch": "\\", "w": 1.5}],
    # Second row
        [{"editable": False, "label": "Caps", "w": 1.9}] +
        [{"ch": c} for c in "ASDFGHJKL;\""] +
        [{"editable": False, "label": "Enter", "w": 2.2}],
    # Third row
        [{"editable": False, "label": "Shift", "w": 1.6}] +
        [{"ch": c} for c in "<ZXCVBNM,./"] +
        [{"editable": False, "label": "Shift", "w": 3.1}],
    # Modifier row
        [
            {"editable": False, "label": "Ctrl"},
            {"editable": False, "label": "Win"},
            {"editable": False, "label": "Alt"},
            {"editable": False, "label": "Space", "w": 3.6},
            {"editable": False, "label": "Alt"},
            {"editable": False, "label": "Menu"},
            {"editable": False, "label": "Win"},
            {"editable": False, "label": "Ctrl"},
        ] if not is_mac else [
            {"editable": False, "label": "Control"},
            {"editable": False, "label": "Option"},
            {"editable": False, "label": "Command"},
            {"editable": False, "label": "Space", "w": 5.0},
            {"editable": False, "label": "Command"},
            {"editable": False, "label": "Option"},
        ],
]

# Transient state to conflate reapply requests
_keymap_prefs_reapply_requested = False

def reapply_from_keymap_prefs():
    global _keymap_prefs_reapply_requested
    from .event_handlers import on_reapply_requested
    on_reapply_requested()
    _keymap_prefs_reapply_requested = False

def draw_in_keymap_prefs(self, context):
    """
    Prepended block shown inside Keymap preferences panel.
    """
    global _keymap_prefs_reapply_requested

    prefs = kle_prefs(context)
    ui_state = prefs.ui_state(context)

    ui_layout = self.layout
    box = ui_layout.box()
    col = box.column(align=True)

    target_layout_name = prefs.preferred_target_layout
    layout_name = prefs.preferred_input_layout
    if layout_name is None:
        layout_name = 'QWERTY'
    is_built_in = is_built_in_layout(layout_name)
    is_editable = prefs.is_layout_editable(layout_name, ignore_built_in=True)
    input_layout_mapping = prefs.get_layout_translation(layout_name)
    target_layout_mapping = prefs.get_layout_translation(target_layout_name)

    split = col.split(factor=0.60, align=False)
    left = split.row(align=True)
    right = split.row(align=True)

    # Left: dropdown + +/- + edit toggle
    # Layout selector disabled when a keymap has this layout applied
    li = left.row(align=False)
    if not is_editable:
        li.operator(KLEOperators.Info.layout_locked, text="", icon='LOCKED', emboss=False)
    else:
        li.operator(KLEOperators.Info.layout_unlocked, text="", icon='UNLOCKED', emboss=False)
    lr = left.row(align=True)
    lr.enabled = is_editable
    split = lr.split(factor=0.30, align=True)
    lr_target, lr_input = split.row(align=False), split.row(align=True)
    lr_target.enabled = is_editable and prefs.allow_non_qwerty_target_layouts
    if not target_layout_mapping.is_valid():
        lr_target.alert = True
    lr_target.prop(ui_state, "current_target_layout", text="")

    icon_row = lr_input.row(align=False)
    icon_row.label(text="", icon="BACK")
    lr_input.prop(ui_state, "current_input_layout", text="")
    lr_input.operator(KLEOperators.add_custom_layout, text="", icon='ADD')
    lr_input.operator(KLEOperators.remove_custom_layout, text="", icon='REMOVE').layout = layout_name
    er = left.row(align=True)
    if not input_layout_mapping.is_valid() and not prefs.allow_key_conflicts_in_input_layout:
        er.alert = True
    er.operator(
        KLEOperators.toggle_edit_layout,
        text="",
        icon='GREASEPENCIL',
        depress=ui_state.layout_editor_visible,
    )

    # Right: Apply / Revert, right-aligned
    # right.alignment = 'RIGHT'
    ar = right.row(align=True)
    is_emulation_active = prefs.is_emulation_active
    has_pending_keymaps_to_apply = prefs.has_pending_keymaps_to_emulate()
    label = "Apply"
    if is_emulation_active and has_pending_keymaps_to_apply:
        if prefs.reapply_on_keymaps_panel and not _keymap_prefs_reapply_requested:
            bpy.app.timers.register(reapply_from_keymap_prefs, first_interval=prefs.reapply_on_keymaps_panel_delay)
            _keymap_prefs_reapply_requested = True
        # label = "Re-Apply?"
        bound = 99
        pending_number = prefs.bounded_number_of_pending_keymaps_to_emulate(bound)
        label = f"Re-Apply ({pending_number if pending_number is not None else str(bound) + '+'})"
    ar.enabled = has_pending_keymaps_to_apply
    ar.operator(KLEOperators.apply_layout_emulation, text=label, icon='ANIM')
    rr = right.row(align=True)
    rr.enabled = is_emulation_active
    # if is_emulation_active:
    #     rr.alert = True
    rr.operator(KLEOperators.revert_layout_emulation, text="Revert", icon='LOOP_BACK')
    right.separator()
    sr = right.row(align=False)
    sr.operator(
        KLEOperators.toggle_keymaps_panel_preferences,
        text="", icon='PREFERENCES', depress=ui_state.keymaps_panel_preferences_visible
    )

    if ui_state.keymaps_panel_preferences_visible:
        col.separator()
        sub = col.box()
        header = sub.row()
        header.label(text="Keyboard Layout Emulation preferences")
        header_right = header.row(align=False)
        header_right.alignment = 'RIGHT'
        header_right.operator(KLEOperators.Info.addon_info, text="More info", icon='QUESTION', emboss=False)
        header_right.operator("wm.url_open", text="Help", icon='URL').url = KLELinks.help
        row = sub.column(align=False)
        split = row.split(factor=0.52, align=False)
        left, right = split.column(align=False), split.column(align=False)
        split = left.column(align=False).split(factor=0.98, align=False)
        left, _ = split.column(align=False), split.column(align=False)
        row = left.row(align=True)
        row.enabled = is_editable
        row.prop(prefs, "allow_non_qwerty_target_layouts")
        split = left.row().split(factor=0.35, align=False)
        left_l, left_r = split.row(align=False), split.row(align=False)
        left_l.prop(prefs, "display_large_warning_button", text="Warning button")
        left_r.enabled = prefs.display_large_warning_button
        split = left_r.split(factor=0.4, align=False)
        left_r_l, left_r_r = split.row(align=False), split.row(align=False)
        left_r_l.prop(prefs, "large_warning_button_height", text="Size")
        left_r_r.prop(prefs, "large_warning_button_style", expand=True)
        split = left.row(align=True).split(factor=0.35, align=False)
        left_l, left_r = split.row(align=True), split.row(align=True)
        left_l.label(text="Logging level")
        left_r.prop(prefs, "logging_level", expand=True)

        split = right.row().split(factor=0.65, align=True)
        right_l, right_r = split.column(align=True), split.column(align=True)
        right_l.prop(prefs, "reapply_on_keymaps_panel", text="Reapply automatically here")
        right_r.enabled = prefs.reapply_on_keymaps_panel
        right_r.prop(prefs, "reapply_on_keymaps_panel_delay", text="Delay")
        split = right.row().split(factor=0.65, align=True)
        right_l, right_r = split.column(align=True), split.column(align=True)
        right_l.prop(prefs, "reapply_on_reload", text="Reapply emulation on restart")
        right_r.enabled = prefs.reapply_on_reload
        right_r.prop(prefs, "reapply_on_reload_delay", text="Delay")
        split = right.row().split(factor=0.65, align=True)
        right_l, right_r = split.column(align=True), split.column(align=True)
        right_l.prop(prefs, "detect_addon_changes", text="Detect add-on installation")
        right_r.enabled = prefs.detect_addon_changes
        right_r.prop(prefs, "detect_addon_changes_polling_interval", text="Interval")


    # Subpanel for editing the selected input keyboard layout
    if ui_state.layout_editor_visible:
        is_layout_editable = is_editable and not is_built_in
        listening_key = ui_state.listening_key

        col.separator()
        sub = col.box()
        header = sub.row()
        split = header.split(factor=0.6, align=True)
        left = split.row(align=True)
        right = split.row(align=True)

        icon = 'UNLOCKED' if is_layout_editable else 'LOCKED'
        if is_built_in:
            msg = f"Use [+] above to edit a copy of this built-in layout: {layout_name}"
        elif not is_editable:
            msg = f"Revert emulation to edit this layout."
        elif listening_key:
            msg = f"Press the key [{listening_key}] should correspond to... (Esc/click to cancel)"
        else:
            msg = f"Edit layout: {layout_name}"
        left.label(text=msg, icon=icon)

        right.alignment = 'RIGHT'
        ir = right.row(align=True)
        # ir.enabled = is_layout_editable
        op = ir.operator(KLEOperators.import_layout_json, text="Import layout...", icon='IMPORT')
        op.layout_name = layout_name if is_layout_editable else ''
        op.filepath = f"{layout_name}.json"
        er = right.row(align=True)
        op = er.operator(KLEOperators.export_layout_json, text="Export layout...", icon='EXPORT')
        op.layout = layout_name
        op.filepath = f"{layout_name}.json"

        # Load conflicting keys from input keyboard layout
        conflicting_keys = input_layout_mapping.conflicting_keys()
        conflicting_keys = set(conflicting_keys) if conflicting_keys else set()

        # Draw each display row with optimized recursive splitting
        for keys in KEYBOARD_EDITOR_LAYOUT:
            r = sub.row(align=True)
            if not is_layout_editable:
                r.enabled = False

            # Precompute cumulative weights for efficient drawing
            cumulative_weights = [0.0]
            running_sum = 0.0
            for k in keys:
                w = k.get('w', 1.0)
                running_sum += w
                cumulative_weights.append(running_sum)

            total_weight = cumulative_weights[-1] if cumulative_weights else 0.0

            # Recursive function to draw keys with minimal splits
            def draw_keys_recursive(
                    parent_layout, start_idx: int, end_idx: int, start_weight: float, end_weight: float):
                if start_idx >= end_idx:
                    return

                if end_idx - start_idx == 1:
                    # Draw single key
                    k = keys[start_idx]
                    if isinstance(k, dict):
                        if k.get("editable", True):
                            qw_ch = str(k.get("ch", ""))
                            if qw_ch:
                                is_listening = ui_state.listening_key == qw_ch
                                ch = input_layout_mapping.map_input_to_output(qw_ch)
                                label = '...' if is_listening else ch
                                red = ch in conflicting_keys and not is_listening
                                if red:
                                    parent_layout.alert = True
                                    # label = f'[{label}]'
                                op = parent_layout.operator(
                                    KLEOperators.capture_key_for_mapping,
                                    text=label,
                                    depress=is_listening,
                                )
                                op.physical = qw_ch
                                op.layout = layout_name
                        else:
                            # Non-editable key: render grayed-out button for context
                            parent_layout.enabled = False
                            label = str(k.get("label", ""))
                            parent_layout.operator(KLEOperators.Info.non_editable_key, text=label)
                else:
                    # Split in half
                    split_idx = (start_idx + end_idx) // 2
                    range_weight = end_weight - start_weight
                    split_weight = cumulative_weights[split_idx]

                    left_weight = split_weight - start_weight
                    factor = left_weight / range_weight

                    # Create split with the correct factor
                    split_layout = parent_layout.split(factor=factor)  # align=True
                    left_row = split_layout.row(align=True)
                    right_row = split_layout.row(align=True)

                    # Recursively draw each half
                    draw_keys_recursive(left_row, start_idx, split_idx, start_weight, split_weight)
                    draw_keys_recursive(right_row, split_idx, end_idx, split_weight, end_weight)

            # Start recursive drawing
            if keys:
                draw_keys_recursive(r, 0, len(keys), 0.0, total_weight)

        if conflicting_keys:
            row = sub.row()
            if not prefs.allow_key_conflicts_in_input_layout:
                row.alert = True
            split = row.split(factor=0.65, align=False)
            left, right = split.row(align=True), split.row(align=True)
            left.label(text=f"Conflicting physical keys: {', '.join(conflicting_keys)}", icon='ERROR')
            right.alignment = 'RIGHT'
            right.prop(prefs, "allow_key_conflicts_in_input_layout", text="Allow conflicts")

    if prefs.is_emulation_active and prefs.display_large_warning_button:
        row = ui_layout.row(align=True)
        if prefs.large_warning_button_style == 'RED':
            row.alert = True
        row.scale_y = prefs.large_warning_button_height
        row.operator(
            KLEOperators.revert_layout_emulation,
            text="Keyboard Layout Emulation is active. Consider disabling it before editing keymaps.",
            icon='ERROR', depress=prefs.large_warning_button_style == 'BLUE',
        )

# State variables for deferred add-on list polling
_last_addons_prefs_draw_time = 0.0
_last_addons_prefs_poll_time = 0.0
_last_active_addons_set = set()
_addon_check_scheduled = False

def draw_in_addons_prefs(self, context):
    """
    Prepended block shown in the add-ons preferences panel.

    We do not show any UI, this draw code is simply installed to get draw updates
    from the add-ons panel.
    """
    on_addon_menu_draw_call(context)

def draw_in_extensions_prefs(self, context):
    """
    Prepended block shown in the extensions preferences panel.

    We do not show any UI, this draw code is simply installed to get draw updates
    from the extensions panel.
    """
    on_addon_menu_draw_call(context)

def on_addon_menu_draw_call(context):
    global _addon_check_scheduled, _last_addons_prefs_draw_time, _last_addons_prefs_poll_time

    prefs = kle_prefs(context)
    if not prefs.detect_addon_changes or not prefs.is_emulation_active:
        return

    # kle_logger.debug(f"... add-ons prefs draw call")

    poll_interval = prefs.detect_addon_changes_polling_interval
    if poll_interval <= 0:
        addon_changes_poll()
    else:
        _last_addons_prefs_draw_time = time.time()
        if not _addon_check_scheduled:
            _addon_check_scheduled = True
            _last_addons_prefs_poll_time = _last_addons_prefs_draw_time
            bpy.app.timers.register(scheduled_addon_changes_poll, first_interval=poll_interval)

def scheduled_addon_changes_poll():
    global _addon_check_scheduled, _last_addons_prefs_draw_time, _last_addons_prefs_poll_time
    try:
        # kle_logger.debug(f"... scheduled poll: {_last_addons_prefs_poll_time} [{_last_addons_prefs_draw_time}]")
        if _last_addons_prefs_poll_time < _last_addons_prefs_draw_time:
            prefs = kle_prefs()
            # Re-register timer
            bpy.app.timers.register(scheduled_addon_changes_poll, first_interval=prefs.detect_addon_changes_polling_interval)
            _last_addons_prefs_poll_time = time.time()
            # kle_logger.debug(f"    re-registered")
        else:
            _addon_check_scheduled = False
            # kle_logger.debug(f"    last")
        addon_changes_poll()
    except KLEPreferencesUnavailableException:
        # Handler triggered after add-on was uninstalled, skip
        kle_logger.debug("! Skipped add-on changes poll, add-on preferences unavailable. Add-on was likely disabled/uninstalled.")
        return

def get_current_set_of_addons(context=...) -> set[str]:
    if context is ...:
        context = bpy.context
    return {addon.module for addon in context.preferences.addons}

def addon_changes_poll():
    global _last_active_addons_set
    current_addons = get_current_set_of_addons()
    # kle_logger.debug(f"... ! poll")

    # This should only occur on the first poll
    if not _last_active_addons_set:
        _last_active_addons_set = current_addons
        # kle_logger.debug(f"    first poll, skipped")
    elif _last_active_addons_set != current_addons:
        _last_active_addons_set = current_addons
        # kle_logger.debug(f"    active addons changed, re-running event handlers")
        from .event_handlers import on_addons_set_change
        on_addons_set_change()
    else:
        # kle_logger.debug(f"    no change")
        pass


_addons_draw_hook_installed = False
def on_detect_addons_changes_update(context=...):
    global _addons_draw_hook_installed
    prefs = kle_prefs(context)
    if prefs.detect_addon_changes != _addons_draw_hook_installed:
        if _addons_draw_hook_installed:
            remove_addons_menu_draw_hooks()
            _addons_draw_hook_installed = False
        else:
            append_addons_menu_draw_hooks()
            _addons_draw_hook_installed = True


def append_addons_menu_draw_hooks():
    bpy.types.USERPREF_PT_addons.prepend(draw_in_addons_prefs)
    bpy.types.USERPREF_PT_extensions.prepend(draw_in_extensions_prefs)
    # kle_logger.debug(f"! Installed addons draw hook")

def remove_addons_menu_draw_hooks():
    bpy.types.USERPREF_PT_addons.remove(draw_in_addons_prefs)
    bpy.types.USERPREF_PT_extensions.remove(draw_in_extensions_prefs)
    # kle_logger.debug(f"! Removed addons draw hook")


def register():
    global _addons_draw_hook_installed

    bpy.types.USERPREF_PT_keymap.prepend(draw_in_keymap_prefs)

    # Deferred registration to ensure preferences are loaded
    bpy.app.timers.register(on_detect_addons_changes_update, first_interval=1)

def unregister():
    global _addons_draw_hook_installed

    bpy.types.USERPREF_PT_keymap.remove(draw_in_keymap_prefs)

    if _addons_draw_hook_installed:
        remove_addons_menu_draw_hooks()
        _addons_draw_hook_installed = False
