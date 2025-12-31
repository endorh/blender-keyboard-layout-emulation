from __future__ import annotations

from typing import Optional, Dict, Literal, TYPE_CHECKING
import json

import bpy
# noinspection PyUnresolvedReferences
from bpy.types import Operator
from bpy.props import BoolProperty, StringProperty, EnumProperty

from .constants import KLEOperators
from .keyboard_layout import us_qwerty_physical_remappable_keys, event_type_to_char_or_none, is_built_in_layout
from .preferences import kle_prefs, layout_enum_items
from .keymap_patch import reapply_keymap_translation, revert_keymap_translation

if TYPE_CHECKING:
    def BoolProperty(*_, **__) -> Literal[bool]: ...
    def StringProperty(*_, **__) -> Literal[str]: ...
    def EnumProperty(*_, **__) -> Literal[str]: ...


# Apply/revert layout emulation

class WM_OT_kle_apply_layout_emulation(Operator):
    bl_idname = KLEOperators.apply_layout_emulation
    bl_label = "Apply Layout Emulation"

    @classmethod
    def description(cls, context, properties):
        prefs = kle_prefs(context)
        if not prefs.is_emulation_active:
            mapping = prefs.get_preferred_layout_translation()
            if not prefs.is_preferred_layout_translation_applicable_and_non_trivial(ignore_trivial=True):
                if prefs.get_layout_translation(prefs.preferred_input_layout).is_valid():
                    return ("Cannot apply keyboard layout emulation because the selected target keyboard layout is not valid.\n\n"
                            "Edit it (by temporarily setting it as input keyboard layout) and fix it before applying the keyboard layout emulation")
                return ("Cannot apply keyboard layout emulation because the selected input keyboard layout is not valid.\n\n"
                        "Edit it (use the pencil icon on the left) and fix it before applying the keyboard layout emulation")
            if mapping.is_identity():
                return "Cannot apply keyboard layout emulation because the selected keyboard layouts require no emulation"
            return f"Apply keyboard layout emulation ({prefs.preferred_input_layout} → {prefs.preferred_target_layout})"
        if not prefs.has_pending_keymaps_to_emulate():
            return "Keyboard layout emulation is already applied.\nNo pending keymaps to be remapped were detected"
        return "Re-apply layout emulation to any pending keymaps.\nAlready remapped keyboard shortcuts will not be remapped twice.\n\nKeyboard layout emulation is automatically reapplied on restart by default"

    @classmethod
    def poll(cls, context):
        prefs = kle_prefs(context)
        if not prefs:
            return False
        # Only allow apply when the mapping is valid and non-trivial
        return prefs.is_preferred_layout_translation_applicable_and_non_trivial()

    def execute(self, context):
        prefs = kle_prefs(context)
        ui_state = prefs.ui_state(context)
        translation = prefs.get_preferred_layout_translation()

        success, msg = reapply_keymap_translation(translation, context)
        prefs.is_emulation_active = True
        ui_state.is_emulation_applied = True

        if success:
            if msg:
                self.report({'INFO'}, msg)
        else:
            self.report({'WARNING'}, msg or "Failed to apply layout emulation")
            return {'CANCELLED'}
        return {'FINISHED'}


class WM_OT_kle_revert_layout_emulation(Operator):
    bl_idname = KLEOperators.revert_layout_emulation
    bl_label = "Revert"

    @classmethod
    def description(cls, context, properties):
        prefs = kle_prefs(context)
        header = "Revert layout emulation"
        footer = ".\n\nYou may hide the warning button in the Keyboard Layout Emulation preferences" if prefs.display_large_warning_button else ""
        if prefs.is_emulation_active:
            return header + (
                ".\n\n"
                "Consider reverting keyboard layout emulation before editing any keymaps.\n"
                "Keyboard layout emulation automatically modifies all of your keymaps, but it is not possible to correctly track your modifications during emulation to exempt them from being remapped on the next restart"
            ) + footer
        else:
            return header + ".\nKeyboard layout emulation is not currently applied" + footer

    @classmethod
    def poll(cls, context):
        prefs = kle_prefs(context)
        return prefs.is_emulation_active

    def execute(self, context):
        prefs = kle_prefs(context)
        ui_state = prefs.ui_state(context)

        success, msg = revert_keymap_translation(context)
        prefs.is_emulation_active = False
        ui_state.is_emulation_applied = False

        if success:
            if msg:
                self.report({'INFO'}, msg)
        else:
            self.report({'WARNING'}, msg or "Failed to revert layout emulation")
            return {'CANCELLED'}
        return {'FINISHED'}

# Add/remove custom layout
class WM_OT_kle_add_custom_layout(Operator):
    bl_idname = KLEOperators.add_custom_layout
    bl_label = "New Layout"
    bl_description = "Define a new keyboard layout"

    name: StringProperty(name="Layout Name", default="Layout")

    def invoke(self, context, event):
        context.window_manager.invoke_props_dialog(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "name")

    def execute(self, context):
        prefs = kle_prefs(context)

        name = (self.name or "").strip()
        if not name:
            self.report({'WARNING'}, "Layout name is empty")
            return {'CANCELLED'}
        if is_built_in_layout(name):
            self.report({'WARNING'}, "Cannot use built-in layout name")
            return {'CANCELLED'}
        if name in prefs.get_layout_names():
            self.report({'WARNING'}, "Layout with that name already exists")
            return {'CANCELLED'}

        # Copy current layout
        current_layout = prefs.preferred_input_layout
        initial = prefs.get_layout_translation(current_layout).in_out_dict
        prefs.set_custom_layout(name, initial)

        # Select new layout if not locked
        if prefs.is_layout_editable(current_layout, ignore_built_in=True):
            prefs.ui_state(context).current_input_layout = name

        self.report({'INFO'}, f"Created custom layout '{name}'")
        return {'FINISHED'}


class WM_OT_kle_remove_custom_layout(Operator):
    bl_idname = KLEOperators.remove_custom_layout
    bl_label = "Delete Layout"
    bl_description = (
        "Remove the currently selected input keyboard layout.\n"
        "You can only remove user-defined keyboard layouts"
    )

    layout: EnumProperty(
        name="Layout",
        description="Layout to delete",
        items=layout_enum_items,
        default=0,
    )

    # It's preferable to have both +/- buttons always active, as they convey their meaning faster this way.
    # The `execute` method still ensures no built-in layouts are deleted.
    # @classmethod
    # def poll(cls, context):
    #     prefs = kle_prefs(context)
    #     return prefs and not is_built_in_layout(getattr(prefs, 'emulated_layout', 'QWERTY'))

    def invoke(self, context, event):
        if is_built_in_layout(self.layout):
            self.report({'WARNING'}, "Cannot delete built-in layout")
            return {'CANCELLED'}
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        prefs = kle_prefs(context)
        layout = self.layout
        if not layout:
            self.report({'WARNING'}, "No layout selected")
            return {'CANCELLED'}
        if is_built_in_layout(layout):
            self.report({'WARNING'}, "Cannot delete built-in layout")
            return {'CANCELLED'}
        if not prefs.is_layout_editable(layout):
            self.report({'WARNING'}, "Cannot delete layout while applied to keymaps. Revert first.")
            return {'CANCELLED'}

        # Set current layout to 'QWERTY' if the previous value was deleted
        ui_state = prefs.ui_state(context)
        if ui_state.current_input_layout == layout:
            ui_state.current_input_layout = 'QWERTY'
        if prefs.preferred_input_layout == layout:
            prefs.preferred_input_layout = 'QWERTY'
        if ui_state.current_target_layout == layout:
            ui_state.current_target_layout = 'QWERTY'
        if prefs.preferred_target_layout == layout:
            prefs.preferred_target_layout = 'QWERTY'

        # Remove (set to None in prefs)
        prefs.set_custom_layout(layout, None)

        self.report({'INFO'}, f"Deleted custom layout '{layout}'")
        return {'FINISHED'}


# Import/export layout
class WM_OT_kle_export_layout_json(Operator):
    bl_idname = KLEOperators.export_layout_json
    bl_label = "Export JSON"
    bl_description = "Export the current layout mapping to a JSON file"

    layout: StringProperty(
        name="Layout",
        description="Layout to export",
        default="QWERTY"
    )
    filepath: StringProperty(
        name="File Path",
        description="Path to export the layout JSON",
        default="",
        subtype='FILE_PATH',
    )
    filter_glob: StringProperty(
        default="*.json",
        options={'HIDDEN'},
    )

    def invoke(self, context, event):
        # Suggest a default file name based on current layout
        prefs = kle_prefs(context)
        if not self.layout:
            self.layout = prefs.preferred_input_layout
        if not self.filepath:
            self.filepath = f"{self.layout if self.layout != 'QWERTY' else 'layout'}.json"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        prefs = kle_prefs(context)
        layout = self.layout
        if not layout:
            self.report({'WARNING'}, "No layout selected")
            return {'CANCELLED'}
        translation = prefs.get_layout_translation(layout)
        if translation is None:
            self.report({'WARNING'}, f"No keyboard layout named '{layout}'")
            return {'CANCELLED'}
        path = (self.filepath or '').strip()
        if not path:
            self.report({'WARNING'}, "No file path provided")
            return {'CANCELLED'}
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(translation.in_out_dict, f, ensure_ascii=False, indent=2, sort_keys=True)
        except Exception as e:
            self.report({'ERROR'}, f"Failed to export: {e}")
            return {'CANCELLED'}
        self.report({'INFO'}, f"Exported layout '{layout}' to {path}")
        return {'FINISHED'}


def on_WM_OT_kle_import_layout_json__layout_name_search(self, context, edit_text):
    prefs = kle_prefs(context)
    suggestions = [
        name
        for name, lower in [(name, name.lower()) for name in sorted(prefs.custom_layouts.keys())]
        if all(ch in lower for ch in edit_text.lower()) and edit_text != name
    ]
    names = set(suggestions)
    suggestions = [(name, "Existing user-defined layout") for name in suggestions]
    if edit_text and edit_text not in names:
        suggestions.append((edit_text, "New user-defined layout"))
    return suggestions
class WM_OT_kle_import_layout_json(Operator):
    bl_idname = KLEOperators.import_layout_json
    bl_label = "Import JSON"
    bl_description = "Import a layout mapping from a JSON file.\n\nBy default, it will overwrite this layout"

    layout_name: StringProperty(
        name="Layout Name",
        description="Name of the layout to import (will replace any existing layout with the same name)",
        default="Imported Layout",
        search=on_WM_OT_kle_import_layout_json__layout_name_search,
        options={'TEXTEDIT_UPDATE'},
    )
    filepath: StringProperty(
        name="File Path",
        description="Path to import the layout JSON from",
        default="",
        subtype='FILE_PATH',
    )
    filter_glob: StringProperty(
        default="*.json",
        options={'HIDDEN'},
    )

    @property
    def inferred_layout_name(self) -> str:
        path = (self.filepath or '').strip()
        name = path.rsplit('/', maxsplit=1)[-1].rsplit('\\', maxsplit=1)[-1].rsplit('.', maxsplit=1)[0] if path else 'Imported Layout'
        return f"{name} (User)" if is_built_in_layout(name) else name

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        prefs = kle_prefs(context)

        path = (self.filepath or '').strip()
        if not path:
            self.report({'WARNING'}, "No file path provided")
            return {'CANCELLED'}

        layout_name = self.layout_name
        if not layout_name:
            layout_name = self.inferred_layout_name

        if is_built_in_layout(layout_name):
            self.report({'WARNING'}, f"Cannot edit built-in layout: {layout_name}")
            return {'CANCELLED'}
        if not prefs.is_layout_editable(layout_name) or prefs.is_emulation_active:
            self.report({'WARNING'}, "Cannot modify layout while emulation is active. Revert emulation first.")
            return {'CANCELLED'}

        # Parse JSON
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            self.report({'ERROR'}, f"Failed to read JSON: {e}")
            return {'CANCELLED'}

        # Validate mapping structure
        if not isinstance(data, dict):
            self.report({'ERROR'}, "JSON must be an object of {physical: mapped}")
            return {'CANCELLED'}
        mapping: Dict[str, str] = {}
        try:
            for k, v in data.items():
                mapping[str(k)] = str(v)
        except Exception:
            self.report({'ERROR'}, "Invalid mapping values; must be strings")
            return {'CANCELLED'}

        # Restrict keys to known physical keys
        # valid_keys = set(us_qwerty_physical_remappable_keys)
        # cleaned = {k: v for k, v in mapping.items() if k in valid_keys}
        # # If nothing remains, abort
        # if not cleaned:
        #     self.report({'ERROR'}, "No valid physical keys found in JSON")
        #     return {'CANCELLED'}
        cleaned = mapping

        prefs.set_custom_layout(layout_name, cleaned)
        prefs.preferred_input_layout = layout_name
        ui_state = prefs.ui_state(context)
        ui_state.current_input_layout = layout_name
        self.report({'INFO'}, f"Imported JSON into layout '{layout_name}'")
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.label(text="Import options")
        alert = False
        if is_built_in_layout(self.layout_name):
            alert = True
            warn_row = col.row()
            warn_row.alert = True
            warn_row.label(text=f"Reserved name: {self.layout_name}", icon='ERROR')
        else:
            prefs = kle_prefs(context)
            if self.layout_name in prefs.custom_layouts:
                warn_row = col.row()
                warn_row.alert = True
                warn_row.label(text=f"'{self.layout_name}' will be overwritten.", icon='INFO')
            elif not self.layout_name:
                inferred = self.inferred_layout_name
                overwritten = inferred in prefs.custom_layouts
                info_row = col.row()
                if overwritten:
                    info_row.alert = True
                info_row.label(
                    text=
                        f"'{inferred}' name will be used." if not overwritten
                        else f"'{inferred}' will be overwritten.",
                    icon='INFO' if not overwritten else 'ERROR')
            else:
                info_row = col.row()
                info_row.label(text=f"'{self.layout_name}' name is available.", icon='INFO')
        row = col.row(align=True)
        if alert:
            row.alert = True
        row.prop(self, "layout_name", text="Name")


# Export/import addon preferences
class WM_OT_kle_export_addon_preferences(Operator):
    bl_idname = KLEOperators.export_addon_preferences
    bl_label = "Export KLE Addon Preferences"
    bl_description = "Export the addon preferences to a JSON file"

    # File picker properties
    filepath: StringProperty(
        name="File Path",
        description="Path to export the addon preferences JSON",
        default="kle_preferences.json",
        subtype='FILE_PATH',
    )
    filter_glob: StringProperty(
        default="*.json",
        options={'HIDDEN'},
    )

    # Filters
    include_custom_layouts: BoolProperty(
        name="Include custom layouts",
        description="Include all custom layouts defined in the 'Preferences > Keymaps' panel",
        default=True,
    )
    include_remapped_keymaps: BoolProperty(
        name="Include remapped keymaps",
        description="ONLY FOR DEBUG. Include the journal of remapped keymaps.",
        default=False,
        options={'SKIP_SAVE'},
    )

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        prefs = kle_prefs(context)
        with open(self.filepath, 'w') as f:
            f.write(prefs.export_to_json(
                include_remapped_keymaps=self.include_remapped_keymaps,
            ))

        self.report({'INFO'}, f"Exported addon preferences to '{self.filepath}'")
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        col.label(text="Export filters")
        col.prop(self, "include_custom_layouts")

        debug_box = col.box()
        debug_box.alert = True
        debug_col = debug_box.column()
        debug_col.label(text="Options for debug only", icon='ERROR')
        debug_col.prop(self, "include_remapped_keymaps")


class WM_OT_kle_import_addon_preferences(Operator):
    bl_idname = KLEOperators.import_addon_preferences
    bl_label = "Import KLE Addon Preferences"
    bl_description = "Import addon preferences from a JSON file"

    # File picker properties
    filepath: StringProperty(
        name="File Path",
        description="Path to import the addon preferences JSON from",
        default="kle_preferences.json",
        subtype='FILE_PATH',
    )
    filter_glob: StringProperty(
        default="*.json",
        options={'HIDDEN'},
    )

    # Filters
    import_emulation_status: BoolProperty(
        name="Import emulation status",
        description="Automatically apply/revert emulation to match imported settings.",
        default=True,
    )
    import_custom_layouts: EnumProperty(
        items=[
            ('NO', 'No', 'Do not import custom layouts from file'),
            ('UPDATE', 'Update', 'Update custom layouts from file, without deleting any layouts currently defined with other names'),
            ('REPLACE', 'Replace', 'Replace custom layouts with layouts from file, erasing any currently defined layouts'),
            ('ADD', 'Add', 'Import only custom layouts with names not already defined'),
        ],
        name="Layouts",
        description="How should custom layouts be imported from the imported preferences",
        default='UPDATE',
    )
    import_preferences_locked_by_emulation: BoolProperty(
        name="Import preferences locked by emulation",
        description="ONLY FOR DEBUG. Import preferences that are usually locked while emulation is active even when emulation is active.",
        default=False,
        options={'SKIP_SAVE'},
    )
    import_remapped_keymaps: BoolProperty(
        name="Import remapped keymaps",
        description="ONLY FOR DEBUG. Import the journal of remapped keymaps.",
        default=False,
        options={'SKIP_SAVE'},
    )

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        prefs = kle_prefs(context)
        with open(self.filepath, 'r') as f:
            prefs.import_from_json(
                f.read(),
                context=context,
                import_emulation_status=self.import_emulation_status,
                ignore_emulation_lock=self.import_preferences_locked_by_emulation,
                inverse_update_custom_layouts=self.import_custom_layouts == 'ADD',
                update_custom_layouts=self.import_custom_layouts == 'UPDATE',
                overwrite_custom_layouts=self.import_custom_layouts == 'REPLACE',
                import_remapped_keymaps=self.import_remapped_keymaps,
            )

        self.report({'INFO'}, f"Imported addon preferences from '{self.filepath}'")
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        col.label(text="Import options")
        col.prop(self, "import_emulation_status")

        custom_layout_box = col.box()
        custom_layout_box.label(text="Import custom layouts")
        custom_layout_box.prop(self, "import_custom_layouts", expand=True)

        debug_box = col.box()
        debug_box.alert = True
        debug_col = debug_box.column()
        debug_col.label(text="Options for debug only", icon='ERROR')
        debug_col.prop(self, "import_preferences_locked_by_emulation")
        debug_col.prop(self, "import_remapped_keymaps")

# UI

class WM_OT_kle_toggle_edit_layout(Operator):
    bl_idname = KLEOperators.toggle_edit_layout
    bl_label = "Edit Keyboard Layout"

    @classmethod
    def description(cls, context, properties):
        prefs = kle_prefs(context)
        ui_state = prefs.ui_state(context)
        warning = ''
        if not prefs.get_layout_translation(prefs.preferred_input_layout).is_valid() and not prefs.allow_key_conflicts_in_input_layout:
            warning = ".\n\nThe selected input layout contains conflicting keys. Fix them before enabling emulation"
        return f"{'Hide' if ui_state.layout_editor_visible else 'Display'} the keyboard layout editor{warning}"

    def execute(self, context):
        prefs = kle_prefs(context)
        ui_state = prefs.ui_state(context)

        # We don't check if the layout is editable or not
        # It is useful to display the editor, even if locked,
        # in case the user wants to see the current layout
        ui_state.layout_editor_visible = not bool(ui_state.layout_editor_visible)
        # self.report({'INFO'}, "Toggled Edit Layout panel")
        return {'FINISHED'}


class WM_OT_kle_toggle_keymaps_panel_preferences(Operator):
    bl_idname = KLEOperators.toggle_keymaps_panel_preferences
    bl_label = "Keyboard layout emulation preferences"
    bl_description = "Show the Keyboard Layout Emulation preferences panel"

    def execute(self, context):
        prefs = kle_prefs(context)
        ui_state = prefs.ui_state(context)

        ui_state.keymaps_panel_preferences_visible = not bool(ui_state.keymaps_panel_preferences_visible)
        # self.report({'INFO'}, "Toggled Keyboard layout emulation settings panel")
        return {'FINISHED'}


def _event_to_char(event) -> Optional[str]:
    # Try unicode/ascii if available
    ch = getattr(event, 'unicode', '') or getattr(event, 'ascii', '')
    if ch:
        # Normalize to single visible character if possible
        if len(ch) == 1:
            ch = ch.upper() if ch.isalpha() else ch
        if ch in us_qwerty_physical_remappable_keys:
            return ch
    t = getattr(event, 'type', '')
    # TODO: This is a blocker if we want to allow remapping non-character keys (e.g., Backspace/Function keys)
    return event_type_to_char_or_none(t)

class WM_OT_kle_capture_key_for_mapping(Operator):
    bl_idname = KLEOperators.capture_key_for_mapping
    bl_label = "Assign Key Mapping"
    bl_description = "Edit key assignment for this emulated layout"

    physical: StringProperty(name="Physical Key", default="")
    layout: EnumProperty(
        name="Layout",
        description="Layout to edit",
        items=layout_enum_items,
        default=0,
    )

    _capturing: bool = False

    @classmethod
    def description(self, context, properties):
        if is_built_in_layout(properties.layout):
            return f"Cannot reassign keys of built-in layout.\nCreate a copy to edit this layout."
        return f"Reassign key [{properties.physical}] for layout: {properties.layout}"

    def invoke(self, context, event):
        prefs = kle_prefs(context)
        physical, layout = self.physical, self.layout
        if not self.physical or not layout:
            self.report({'WARNING'}, "No physical key or layout specified.")
            return {'CANCELLED'}
        if is_built_in_layout(layout):
            self.report({'WARNING'}, "Cannot edit built-in layout.")
            return {'CANCELLED'}
        if not prefs.is_layout_editable(layout):
            self.report({'WARNING'}, "Cannot modify layout while applied to keymaps. Revert first.")
            return {'CANCELLED'}

        # Mark which key is listening so UI can show it as pressed
        ui_state = prefs.ui_state(context)
        ui_state.listening_key = physical

        # Register modal handler
        context.window_manager.modal_handler_add(self)
        self._capturing = True

        self.report({'INFO'}, f"Press a key to assign to '{physical}' (ESC or mouse click to cancel)")
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        prefs = kle_prefs(context)
        ui_state = prefs.ui_state(context)

        physical, layout = self.physical, self.layout

        # Cancel conditions: ESC or any mouse button click anywhere
        cancel_mouse = event.type in {'LEFTMOUSE', 'MIDDLEMOUSE', 'RIGHTMOUSE'} and event.value == 'PRESS'
        cancel_esc = event.type == 'ESC' and event.value == 'PRESS'

        if cancel_mouse or cancel_esc:
            self._capturing = False
            ui_state.listening_key = ""

            self.report({'INFO'}, "Remapping cancelled")

            # Tag area for immediate redraw
            bpy.app.timers.register(context.area.tag_redraw, first_interval=0)

            return {'CANCELLED'}

        # Only react on key presses
        if event.value != 'PRESS':
            return {'RUNNING_MODAL'}
        mapped = _event_to_char(event)
        if mapped is None:
            return {'RUNNING_MODAL'}

        # Normalize to single-char mapping
        prefs.update_layout_key(layout, physical, mapped)
        prefs.ui_state(context).listening_key = ""
        self._capturing = False

        self.report({'INFO'}, f"{physical} → {mapped}")

        # Tag area for immediate redraw
        bpy.app.timers.register(context.area.tag_redraw, first_interval=0)

        return {'FINISHED'}


# UI Debug
class WM_OT_kle_debug_toggle_expanded_subkey(Operator):
    bl_idname = KLEOperators.debug_toggle_expanded_subkey
    bl_label = "Show Content"
    bl_description = "Expand item"

    subkey: StringProperty(
        name="Subkey",
        description="Subkey to toggle",
        default=""
    )
    prefs_prop: StringProperty(
        name="Preferences Property",
        description="Property to edit within the preferences",
        default=""
    )

    def execute(self, context):
        prefs = kle_prefs(context)
        ui_state = prefs.ui_state(context)

        prefs_prop = self.prefs_prop
        if not prefs_prop or not hasattr(ui_state, prefs_prop):
            self.report({'WARNING'}, "Invalid preferences property specified.")
            return {'CANCELLED'}

        subkey = self.subkey
        if not subkey:
            self.report({'WARNING'}, "No subkey specified.")
            return {'CANCELLED'}

        prop = getattr(ui_state, prefs_prop)
        lines = prop.splitlines()
        is_shown = subkey in lines
        if is_shown:
            lines.remove(subkey)
            prop = '\n'.join(lines)
        else:
            prop = f"{prop}\n{subkey}"

        setattr(ui_state, prefs_prop, prop)
        return {'FINISHED'}


# UI Info
class WM_OT_kle_non_editable_key(Operator):
    bl_idname = KLEOperators.Info.non_editable_key
    bl_label = "Cannot remap this key"
    bl_description = "Cannot remap this key"

    key: StringProperty(name="Key", default="")

    def execute(self, context):
        return {'CANCELLED'}


class WM_OT_kle_layout_unlocked_info(Operator):
    bl_idname = KLEOperators.Info.layout_unlocked
    bl_label = "Choose an input keyboard layout to emulate"
    bl_description = (
        "Keyboard layout emulation lets you automatically remap your entire keymap to emulate a QWERTY keyboard layout when using a non-QWERTY keyboard layout.\n"
        "This lets you use QWERTY keyboard shortcuts while still being able to type text in Blender using your preferred keyboard layout.\n\n"
        "The remap is reapplied on every restart (taking care to not remap the same shortcut twice over).\n"
        "This ensures that even shortcuts added by other addons are remapped reliably.\n\n"
        "It is recommended that you revert the emulation before editing any keymaps"
    )

    def execute(self, context):
        return {'CANCELLED'}


class WM_OT_kle_layout_locked_info(Operator):
    bl_idname = KLEOperators.Info.layout_locked
    bl_label = "Revert the active emulation to change layout"
    bl_description = (
        "Keyboard layout emulation persistently modifies your keymap.\n"
        "You must revert the active emulation before changing/editing which keyboard layout to emulate"
    )

    def execute(self, context):
        return {'CANCELLED'}


class WM_OT_kle_addon_info(Operator):
    bl_idname = KLEOperators.Info.addon_info
    bl_label = "Keyboard Layout Emulation"
    bl_description = (
        "This add-on injects a dropdown menu above the usual 'Preferences > Keymap' panel, to configure emulation of QWERTY keyboard shortcuts on non-QWERTY keyboard layouts.\n\n"
        "Keyboard layout emulation is achieved by persistently reassigning your keymap on every restart (so add-on shortcuts can be reliably reassigned). Tracking user modifications of the keymap is not possible so, for best results, consider temporarily disabling emulation every time you want to manually edit your keymap.\n\n"
        "If you export a keymap preset while emulation is active, it will contain the remapping baked into it. You may want to use this add-on to only generate remapped presets, but bear in mind that remapping add-on shortcuts using a preset may not be possible due to flaws in Blender's keymap system.\n\n"
        "Unless you opt out in the 'Uninstall options' in 'Preferences > Add-ons', your keymap will be automatically restored when this add-on is disabled or uninstalled."
    )

    def execute(self, context):
        return {'CANCELLED'}


_registered_classes = (
    WM_OT_kle_apply_layout_emulation,
    WM_OT_kle_revert_layout_emulation,
    WM_OT_kle_add_custom_layout,
    WM_OT_kle_remove_custom_layout,
    WM_OT_kle_export_layout_json,
    WM_OT_kle_import_layout_json,
    WM_OT_kle_export_addon_preferences,
    WM_OT_kle_import_addon_preferences,
    WM_OT_kle_toggle_edit_layout,
    WM_OT_kle_toggle_keymaps_panel_preferences,
    WM_OT_kle_capture_key_for_mapping,
    WM_OT_kle_debug_toggle_expanded_subkey,
    WM_OT_kle_non_editable_key,
    WM_OT_kle_layout_unlocked_info,
    WM_OT_kle_layout_locked_info,
    WM_OT_kle_addon_info,
)

def register():
    for cls in _registered_classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(_registered_classes):
        bpy.utils.unregister_class(cls)
