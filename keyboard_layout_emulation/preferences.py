from __future__ import annotations

from dataclasses import dataclass
import logging

import bpy

from typing import Any, Optional, List, Tuple, Dict, TYPE_CHECKING, Literal
import json

# noinspection PyUnresolvedReferences
from bpy.types import AddonPreferences, OperatorProperties, PropertyGroup, KeyConfig
from bpy.props import EnumProperty, StringProperty, BoolProperty, FloatProperty, PointerProperty

from .keyboard_layout import *
from .constants import *

__all__ = [
    # Registration handles
    'register',
    'unregister',
    # Preferences classes
    'KLEUIStateProperties',
    'KLEPreferences',
    # Exceptions
    'KLEPreferencesUnavailableException',
    # Accessors
    'kle_prefs',
    'get_current_keyconfig_set',
    'resolve_remapped_keymap_item',
    'is_remappable_keymap_item',
    'is_remapped_keymap_item',
    'layout_enum_items',
    'are_operator_properties_compatible',
    # Serialization utils
    'json_cached_loads',
    'json_set_loads',
    'json_set_dumps',
    'keyed_operator_properties',
    'keymap_id',
    'kmi_signature',
    'kmi_modifier_string',
    'operator_properties_to_dict',
    'operator_property_value_to_dict',
    'compact_operator_properties',
]

if TYPE_CHECKING:
    # Definitions for IDEs to understand assignments to Blender properties
    # (or at least assume they are defined as Any)
    def EnumProperty(*_, **__) -> Literal[str]: ...
    def StringProperty(*_, **__) -> Literal[str]: ...
    def BoolProperty(*_, **__) -> Literal[bool]: ...
    def FloatProperty(*_, **__) -> Literal[float]: ...
    def PointerProperty(*_, **__) -> Any: ...

keyed_operator_properties = {'name', 'data_path'}

_json_cache: Dict[str, Tuple[str, Any]] = {}
def json_cached_loads(cache_key: str, s: str, *, deserialize_list_encoded_sets=False, **kwargs) -> Any:
    """
    Deserialize cached JSON string with optional support for list-encoded sets.
    """
    if cache_key in _json_cache:
        cache_string, cache_value = _json_cache[cache_key]
        if cache_string == s:
            return cache_value
        if not s == '':
            del _json_cache[cache_key]
    new_value = json_set_loads(s, **kwargs) if deserialize_list_encoded_sets else json.loads(s, **kwargs)
    if s:
        _json_cache[cache_key] = (s, new_value)
    return new_value

def json_set_loads(s: str, **kwargs) -> Any:
    """
    Deserialize JSON string with support for list-encoded sets.
    """
    # We cannot really do this with JSONEncoder/Decoder because
    # it is not possible to change the way a JSONEncoder encodes
    # lists deep within an object without fully reimplementing it
    def patch(o):
        if isinstance(o, list):
            o = [patch(oo) for oo in o]
            if len(o) > 1:
                head = o[0]
                if isinstance(head, str):
                    if head == '\aset':
                        return set(o[1:])
                    elif head.startswith('\a\a'):
                        o[0] = head[1:]
        elif isinstance(o, dict):
            o = {k: patch(v) for k, v in o.items()}
        return o
    return patch(json.loads(s, **kwargs))

def json_set_dumps(o: Any, ensure_ascii=False, **kwargs) -> str:
    """
    Serialize JSON string with support for list-encoded sets.
    """
    def patch(oo):
        if isinstance(oo, set):
            oo = ['\aset'] + [patch(oo) for oo in oo]
        elif isinstance(oo, list):
            oo = [patch(oo) for oo in oo]
            if len(oo) > 0:
                head = oo[0]
                if isinstance(head, str) and head.startswith('\a'):
                    oo[0] = f'\a{head}'
        elif isinstance(oo, dict):
            oo = {k: patch(v) for k, v in oo.items()}
        return oo
    return json.dumps(patch(o), ensure_ascii=ensure_ascii, **kwargs)

def kle_prefs(context=...) -> KLEPreferences:
    """Return this add-on's preferences instance from bpy.context."""
    if context is ... or context is None:
        context = bpy.context
    try:
        return context.preferences.addons[addon_id].preferences
    except KeyError as e:
        raise KLEPreferencesUnavailableException()

class KLEPreferencesUnavailableException(Exception):
    pass

@dataclass
class KeyConfigSet:
    active: KeyConfig
    user: KeyConfig
    default: KeyConfig
    addon: KeyConfig

def get_current_keyconfig_set(context=...) -> KeyConfigSet:
    if context is ...:
        context = bpy.context
    kcs = context.window_manager.keyconfigs
    return KeyConfigSet(active=kcs.active, user=kcs.user, default=kcs.default, addon=kcs.addon)

def keymap_id(km) -> str:
    return f"{'modal:' if km.is_modal else ''}{km.space_type}.{km.region_type}:{km.name}"
def is_remappable_keymap_item(kmi, layout_translation) -> bool:
    if kmi.map_type != 'KEYBOARD' or kmi.value not in {'PRESS', 'RELEASE'}:
        return False
    return event_type_to_char(kmi.type) in layout_translation.remapped_input_characters

def is_remapped_keymap_item(kmi, layout_translation) -> bool:
    if kmi.map_type != 'KEYBOARD' or kmi.value not in {'PRESS', 'RELEASE'}:
        return False
    return event_type_to_char(kmi.type) in layout_translation.remapped_output_characters

def operator_property_value_to_dict(value) -> Any:
    if isinstance(value, (float, str, bool, int)):
        return value
    elif isinstance(value, set):
        return {operator_property_value_to_dict(v) for v in value}
    elif isinstance(value, dict):  # Doesn't occur
        return {k: operator_property_value_to_dict(v) for k, v in value.items() if isinstance(k, str)}
    elif isinstance(value, (PropertyGroup, OperatorProperties)):
        return operator_properties_to_dict(value)
    elif hasattr(value, '__len__'):
        return [operator_property_value_to_dict(v) for v in value]
    else:
        kle_logger.warn(f"  ! unsupported prop type: {type(value)}")
        # We only record the existence of properties when we can serialize them safely into JSON.
        # Nonetheless, the code above handles all the cases that Blender's keymap export feature does.
        #    See: blender/blender/scripts/modules/bl_keymap_utils/io.py#_kmi_properties_to_lines_recursive#string_value
        return None

def operator_properties_to_dict(properties) -> Dict[str, Any]:
    return {
        name: operator_property_value_to_dict(getattr(properties, name))
        # See blender/blender/scripts/modules/bl_keymap_utils/io.py#_kmi_properties_to_lines_recursive
        for name in properties.bl_rna.properties.keys() if name != 'rna_type'
    } if properties is not None else None


def compact_operator_properties(properties: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if properties is None:
        return None
    compacted = {
        k: compact_operator_properties(v) if isinstance(v, dict) else v
        for k, v in properties.items()
        if bool(v)
    }
    return compacted if compacted else None


def are_operator_properties_compatible(props1, stored_props) -> bool:
    return compact_operator_properties(operator_properties_to_dict(props1)) == stored_props


def kmi_modifier_string(kmi) -> str:
    hyper, oskey, ctrl, alt, shift = [getattr(kmi, name) for name in ('hyper', 'oskey', 'ctrl', 'alt', 'shift')]
    key_mod = kmi.key_modifier
    def op_ch(op, ch) -> str:
        return f"{'~' if op < 0 else ''}{ch}" if op != 0 else ""
    return f"{op_ch(hyper, '@')}{op_ch(oskey, '#')}{op_ch(ctrl, '^')}{op_ch(alt, '!')}{op_ch(shift, '+')}{key_mod if key_mod != 'NONE' else ''}"


def kmi_signature(kmi) -> Dict[str, Any]:
    s = {}
    properties = getattr(kmi, 'properties', None)
    if properties is not None:
        props = operator_properties_to_dict(properties)
        stored_props = compact_operator_properties(props)
        if stored_props:
            s['p'] = stored_props
            if stored_props != dict(stored_props):
                kle_logger.warn(f"  ! non-self-comparable properties: {kmi.idname} " + json_set_dumps(stored_props, indent=2).replace('\n', '\n    '))
    propvalue = getattr(kmi, 'propvalue', 'NONE')
    if propvalue != 'NONE':
        s['pv'] = propvalue
    return s


def resolve_remapped_keymap_item(kmi, per_op_kmi) -> Optional[Any]:
    # op = kmi.idname
    # if op not in remapped_km_journal:
    #     kle_logger.debug(f"  ! operator '{op}' not found in remapped keymap journal")
    #     return None
    # per_op_kmi = remapped_km_journal[op]
    kmi_properties = compact_operator_properties(operator_properties_to_dict(kmi.properties))
    kmi_propvalue = kmi.propvalue if kmi.propvalue != 'NONE' else None
    compatible = [s for s in per_op_kmi if kmi_properties == s.get('p', None) and kmi_propvalue == s.get('pv', None)]
    if len(compatible) == 1:
        return compatible[0]
    elif not compatible:
        kle_logger.debug(
            f"  ! non compatible properties!! ({kmi.idname})\n" +
            f"    props: " + json_set_dumps(kmi_properties, indent=2).replace('\n', '\n    ') + '\n' +
            f"    propvalue: {kmi_propvalue}\n" +
            f"    compatible: " + json_set_dumps(per_op_kmi, indent=2).replace('\n', '\n   ')
        )
        return None

    # kle_logger.debug(f"  > compatible properties")

    kmi_char = event_type_to_char(kmi.type)

    compatible_after = [s for s in compatible if kmi_char == s['t']]
    if len(compatible_after) == 1:
        return compatible_after[0]
    compatible_before = [s for s in compatible if kmi_char == s['s']]
    if len(compatible_before) == 1:
        return compatible_before[0]

    # Already some built-in shortcuts exist with duplicates that only differ in modifiers
    kmi_modifier = kmi_modifier_string(kmi)
    compatible = [s for s in compatible if kmi_modifier == s['m']]
    if len(compatible) == 1:
        return compatible[0]
    elif not compatible:
        return None

    compatible_after = [s for s in compatible if kmi_char == s['t']]
    if len(compatible_after) == 1:
        return compatible_after[0]
    compatible_before = [s for s in compatible if kmi_char == s['s']]
    if len(compatible_before) == 1:
        return compatible_before[0]

    if len(compatible_after) > 1 or len(compatible_before) > 1:
        kle_logger.debug(f"  ! multiple remapped keymap items found for operator '{kmi.idname}': {compatible_after or compatible_before}")
    return None


# It is important to ensure that strings returned by enum providers are kept referenced in Python.
# See https://docs.blender.org/api/5.0/bpy.props.html#bpy.props.EnumProperty
_layout_items_strings__desc_built_in = 'Built-in layout'
_layout_items_strings__desc_custom = 'User-defined keyboard layout'
def layout_enum_items(self, context) -> List[Tuple[str, str, str]]:
    """Enum provider for the layout dropdown in Add-on Preferences."""
    prefs = kle_prefs(context)

    # Built-in layouts
    items = list(LayoutTranslation.built_in_enum_items)

    # Custom layouts after a separator, if any
    custom_layouts = prefs.custom_layouts
    if custom_layouts:
        items += [None] + [
            (n, n, _layout_items_strings__desc_custom)
            for n in custom_layouts
        ]

    return items


def on_current_input_layout_update(self, context):
    prefs = kle_prefs(context)
    ui_state = prefs.ui_state(context)
    prefs.preferred_input_layout = ui_state.current_input_layout

def on_current_target_layout_update(self, context):
    prefs = kle_prefs(context)
    ui_state = prefs.ui_state(context)
    prefs.preferred_target_layout = ui_state.current_target_layout

def on_allow_non_qwerty_target_layouts_update(self, context):
    prefs = kle_prefs(context)
    ui_state = prefs.ui_state(context)

    if prefs.is_emulation_active:
        if prefs.preferred_target_layout != 'QWERTY':
            if not prefs.allow_non_qwerty_target_layouts:
                prefs.allow_non_qwerty_target_layouts = True
    else:
        if not prefs.allow_non_qwerty_target_layouts:
            if prefs.preferred_target_layout != 'QWERTY':
                prefs.preferred_target_layout = 'QWERTY'
                ui_state.current_target_layout = 'QWERTY'

def on_detect_addons_changes_update(self, context):
    from .ui import on_detect_addons_changes_update as ui_handler
    ui_handler(context)

def on_logging_level_update(self=..., context=...):
    prefs = kle_prefs(context)
    kle_logger.setLevel(
        logging.DEBUG if prefs.logging_level == 'DEBUG' else
        logging.INFO if prefs.logging_level == 'INFO' else
        logging.WARN if prefs.logging_level == 'WARN' else
        logging.ERROR
    )

def is_subkey_expanded(subkey, lst):
    return subkey in lst.splitlines()


class KLEUIStateProperties(PropertyGroup):
    """
    Transient UI state of the KLE addon, which needs not be saved.
    """

    layout_editor_visible: BoolProperty(
        name="Show Layout Editor",
        description="Show/hide the keyboard layout editor, within the Keymap preferences panel",
        default=False,
    )
    keymaps_panel_preferences_visible: BoolProperty(
        name="Show Keyboard Layout Emulation preferences",
        description="Show/hide the settings panel for the addon in the keymaps preferences panel",
    )

    # is_emulation_applied: BoolProperty(
    #     name="Emulation applied",
    #     description="Whether emulation has been applied at least once this session.",
    #     default=False,
    # )

    revert_on_uninstall: BoolProperty(
        name="Revert keyboard layout emulation when disabling/uninstalling this addon.",
        description="By default, keyboard layout emulation is automatically reverted whenever you disable/uninstall the Keyboard Layout Emulation addon.\n\nOnly uncheck this option if you want to uninstall the addon while keeping the remapped keymaps as they are",
        default=True,
    )

    uninstall_options_visible: BoolProperty(
        name="Show Uninstall options",
        description="Show/hide the uninstall options panel, within the addon preferences UI",
        default=False,
    )

    preferences_debug_visible: BoolProperty(
        name="Show Add-on Preferences Debug",
        description="Show/hide the addon preferences debug panel, within the addon preferences UI",
        default=False,
    )
    preferences_debug_custom_layouts_visible: BoolProperty(
        name="Show Custom Layouts Debug",
        description="Show/hide the custom layouts debug panel, within the addon preferences UI",
        default=False,
    )
    preferences_debug_general_prefs_visible: BoolProperty(
        name="Show Preferences Debug",
        description="Show/hide the preferences debug panel, within the addon preferences UI",
        default=False,
    )
    preferences_debug_custom_layouts_expanded_subkeys: StringProperty(
        name="Subkeys expanded in the debug display of custom layouts",
        description="Subkeys expanded in the debug display of custom layouts, newline separated",
        default="",
    )
    preferences_debug_remapped_keymaps_visible: BoolProperty(
        name="Show Remapped Keymaps Debug",
        description="Show/hide the remapped keymaps debug panel, within the addon preferences UI",
        default=False,
    )
    preferences_debug_remapped_keymaps_expanded_subkeys: StringProperty(
        name="Subkeys expanded in the debug display of remapped keymaps",
        description="Subkeys expanded in the debug display of remapped keymaps, newline separated",
        default="",
    )
    listening_key: StringProperty(
        name="Listening Key",
        description="Which key button is currently waiting for input in the keyboard layout editor, if any",
        default="",
    )

    current_input_layout: EnumProperty(
        name="Input Keyboard Layout",
        description=(
            "Input Keyboard Layout.\n"
            "When keyboard layout emulation is applied, all keymaps are remapped in order to emulate the Target Keyboard Layout (usually QWERTY), assuming that the system's keyboard layout matches the specified Input Keyboard Layout.\n"
            "This way, you will be able to use QWERTY shortcuts while typing text in your preferred input layout.\n\n"
            "Set this value to match your system's keyboard layout, or create a custom keyboard layout using the (+) button on the right if none of the built-ins match your system"
        ),
        items=layout_enum_items,
        default=0,
        update=on_current_input_layout_update,
    )
    current_target_layout: EnumProperty(
        name="Target Keyboard Layout",
        description=(
            "Target Keyboard Layout.\n"
            "Most users will only ever need to set this to QWERTY.\n\n"
            "Only specify a different value if you want to adapt your input keyboard layout to a keymap preset that was designed for a distinct, non-QWERTY, keyboard layout.\n\n"
            "By default, editing the target layout is restricted to make the UI easier to understand for new users. Open the preferences (top right corner) if you really need a non-QWERTY target keyboad layout"
        ),
        items=layout_enum_items,
        default=0,
        update=on_current_target_layout_update,
    )

class KLEPreferences(AddonPreferences):
    """Add-on preferences storing selected layout, mappings, journal, and UI flags."""
    bl_idname = addon_id

    def is_valid_layout(self, name: str):
        return is_built_in_layout(name) or name in self.custom_layouts

    hidden__preferred_input_layout: StringProperty(
        name="Preferred input keyboard layout",
        description="Last input keyboard layout selected by the user, either built-in or custom.",
        default='QWERTY',
        options={'HIDDEN'},
    )
    @property
    def preferred_input_layout(self) -> str:
        name = self.hidden__preferred_input_layout
        return name if self.is_valid_layout(name) else 'QWERTY'
    @preferred_input_layout.setter
    def preferred_input_layout(self, name: str):
        if self.is_valid_layout(name):
            self.hidden__preferred_input_layout = name

    hidden__preferred_target_layout: StringProperty(
        name="Preferred target keyboard layout",
        description="Last target keyboard layout selected by the user, either built-in or custom.",
        default='QWERTY',
        options={'HIDDEN'},
    )
    @property
    def preferred_target_layout(self) -> str:
        name = self.hidden__preferred_target_layout
        return name if self.is_valid_layout(name) else 'QWERTY'
    @preferred_target_layout.setter
    def preferred_target_layout(self, name: str):
        if self.is_valid_layout(name):
            self.hidden__preferred_target_layout = name

    allow_non_qwerty_target_layouts: BoolProperty(
        name="Allow non-QWERTY target layouts",
        description=(
            "Most users will never need to use a non-QWERTY target layout.\n\n"
            "Changing the target keyboard layout is disabled by default to make the UI easier to understand for new users"
        ),
        default=False,
        update=on_allow_non_qwerty_target_layouts_update,
    )
    reapply_on_keymaps_panel: BoolProperty(
        name="Reapply automatically from preferences",
        description=(
            "Reapply emulation automatically anytime pending keymaps are detected when the 'Preferences > Keymaps' panel is updated.\n\n"
            "This can be disruptive if you plan to edit the keymap while emulation is active, but it can help automatically fix some glitchy keyboard shortcuts that Blender tends to reset while you edit others (e.g., `node.duplicate_move`)"
        ),
        default=False,
    )
    reapply_on_keymaps_panel_delay: FloatProperty(
        name="Delay for emulation reapply on preferences update",
        description=(
            "Time to wait to reapply emulation from the moment pending keymaps are detected when the 'Preferences > Keymaps' panel is updated"
        ),
        min=0.0, soft_max=30.0, default=0.5, step=100, precision=2,
        subtype='TIME_ABSOLUTE', unit='TIME_ABSOLUTE',
    )
    reapply_on_reload: BoolProperty(
        name="Reapply emulation on reload/restart",
        description=(
            "Reapply emulation whenever Blender is restarted and after a new file is loaded.\n"
            "This ensures that other addon's keyboard shortcuts are reliably remapped.\n\n"
            "Remapped shortcuts are tracked to avoid remapping the same shortcut twice"
        ),
        default=True,
    )
    reapply_on_reload_delay: FloatProperty(
        name="Delay for emulation reapply on restart",
        description=(
            "Time to wait to reapply emulation a second time after restart (it is always applied immediately at least once).\n"
            "This setting exists to ensure that keyboard shortcuts registered later by addons are also reliably remapped.\n"
            "Individual shortcuts are tracked to avoid remapping the same shortcut twice.\n"
            "Set to 0 to only reapply once"
        ),
        min=0.0, soft_max=10.0, default=3.0, step=10, precision=2,
        subtype='TIME_ABSOLUTE', unit='TIME_ABSOLUTE',
    )
    detect_addon_changes: BoolProperty(
        name="Detect changes to installed addons to reapply emulation",
        description=(
            "Detect changes to installed addons and automatically reapply emulation.\n"
            "This ensures that the keyboard shortcuts of newly installed addons are immediately remapped.\n\n"
            "Changes are detected by polling the set of active add-ons on a timer, but only while the 'Preferences > Add-ons' panel is being updated, so this setting should not negatively affect performance"
        ),
        default=True,
        update=on_detect_addons_changes_update,
    )
    detect_addon_changes_polling_interval: FloatProperty(
        name="Polling interval for detecting changes to installed addons",
        description=(
            "Polling interval used to detect installed addons.\n\n"
            "Regardless of this setting, polling only occurs while the 'Preferences > Add-ons' panel is being updated.\n"
            "Set to 0 to poll on every draw call of the panel."
        ),
        min=0.0, soft_max=10.0, default=1.0, step=10, precision=2,
        subtype='TIME_ABSOLUTE', unit='TIME_ABSOLUTE',
    )
    display_large_warning_button: BoolProperty(
        name="Display large warning button",
        description="Display a large warning button above the keymaps prompting to revert emulation when emulation is active",
        default=True,
    )
    large_warning_button_height: FloatProperty(
        name="Height of large warning button",
        description="Height of the large warning button displayed above the keymaps preferences prompting to revert emulation",
        min=1.0, soft_max=5.0, max=100.0, default=1.5, step=50, precision=1,
    )
    large_warning_button_style: EnumProperty(
        items=[
            ('RED', 'Red', 'Alert button style'),
            ('BLUE', 'Blue', 'Depressed button style'),
            ('GRAY', 'Gray', 'Normal button style'),
        ],
        name="Large warning button style",
        description="Style of the large warning button displayed above the keymaps preferences prompting to revert emulation",
        default='BLUE',
    )
    allow_key_conflicts_in_input_layout: BoolProperty(
        name="Allow key conflicts in input layout",
        description=(
            "Allow key conflicts in the input layout.\n\n"
            "If enabled, key conflicts in the input layout will be allowed, since we record from which key was originally remapped every shortcut.\n"
            "Some keyboard layouts may be impossible to express in Blender without key conflicts due to the limited character range supported by Blender's keymap system."
        ),
    )
    logging_level: EnumProperty(
        items=[
            ('ERROR', "Error", "Log only errors"),
            ('WARN', "Warn", "Log only errors and warnings"),
            ('INFO', "Info", "Log errors, warnings and info messages"),
            ('DEBUG', "Debug", "Log everything, including debug messages"),
        ],
        name="Logging level",
        description="Logging level of messages displayed in the Blender's System Console",
        default='WARN',
        update=on_logging_level_update,
    )

    is_emulation_active: BoolProperty(
        name="Emulation active",
        description="Whether the user has enabled keyboard layout emulation, and keys should be remapped when possible. Editing the keyboard layout is also disabled while emulation is active",
        default=False,
    )

    # Data preferences (not to be edited directly)
    custom_layouts_json: StringProperty(
        name="Custom Layouts (JSON)",
        description="Serialized keyboard layout mappings (name -> us_qwerty_key -> layout_key)",
        default="",
    )
    @property
    def custom_layouts(self) -> Dict[str, Dict[str, str]]:
        # TODO: Ideally this would return a frozenmap to enforce setter semantics, but Python's not there yet
        json_value = self.custom_layouts_json
        d = json_cached_loads('kle_prefs:custom_layouts', json_value) if json_value else {}
        if not isinstance(d, dict):
            return {}
        for name in LayoutTranslation.built_in:
            if name in d:
                del d[name]
        return d
    @custom_layouts.setter
    def custom_layouts(self, value: Dict[str, Dict[str, str]]):
        if not isinstance(value, dict):
            raise ValueError(f"Expected dict, got {type(value)}")
        value = dict(value)
        for name in LayoutTranslation.built_in:
            if name in value:
                del value[name]
        self.custom_layouts_json = json.dumps(value)

    def get_custom_layout(self, name: str) -> Optional[Dict[str, str]]:
        layout = self.custom_layouts.get(name, None)
        if isinstance(layout, dict):
            removed_keys = []
            for qwerty_key, layout_key in layout.items():
                if not isinstance(qwerty_key, str) or not isinstance(layout_key, str):
                    removed_keys.append(qwerty_key)
            for key in removed_keys:
                del layout[key]
            return layout
        return None

    def set_custom_layout(self, name: str, layout: Optional[Dict[str, str]]):
        if is_built_in_layout(name):
            raise ValueError(f"Cannot override built-in layout '{name}'")
        if not self.is_layout_editable(name):
            raise ValueError(f"Cannot edit layout '{name}'")
        custom_layouts = self.custom_layouts

        if layout is None:
            if name in custom_layouts:
                del custom_layouts[name]
        else:
            custom_layouts[name] = layout
        self.custom_layouts = custom_layouts


    def update_layout_key(self, name: str, us_qwerty_key: str, new_key: str):
        if is_built_in_layout(name):
            raise ValueError(f"Cannot override built-in layout '{name}'")
        if not self.is_layout_editable(name):
            raise ValueError(f"Cannot edit layout '{name}'")
        layout = self.get_custom_layout(name)
        if layout is None:
            raise ValueError(f"No layout named '{name}'")
        layout[us_qwerty_key] = new_key
        self.set_custom_layout(name, layout)

    def get_preferred_layout_translation(self) -> LayoutTranslation:
        input = self.get_layout_translation(self.preferred_input_layout) or LayoutTranslation.QWERTY
        target = self.get_layout_translation(self.preferred_target_layout) or LayoutTranslation.QWERTY
        if target.is_identity():
            return input
        return LayoutTranslation.from_input_to_target(input, target)

    def is_preferred_layout_translation_applicable_and_non_trivial(self, *, ignore_trivial=False) -> bool:
        target = self.get_layout_translation(self.preferred_target_layout) or LayoutTranslation.QWERTY
        if not target.is_valid():
            return False
        input = self.get_layout_translation(self.preferred_input_layout) or LayoutTranslation.QWERTY
        if not self.allow_key_conflicts_in_input_layout and not input.is_valid():
            return False
        return ignore_trivial or not LayoutTranslation.from_input_to_target(input, target).is_identity()

    def get_layout_translation(self, name: str) -> Optional[LayoutTranslation]:
        if is_built_in_layout(name):
            return LayoutTranslation.built_in[name]
        layout_mapping = self.get_custom_layout(name)
        return LayoutTranslation.from_dict(layout_mapping) if layout_mapping is not None else None

    def get_layout_names(self) -> List[str]:
        return list(LayoutTranslation.built_in.keys()) + [
            k for k, v in self.custom_layouts.items() if isinstance(k, str) and isinstance(v, dict)
        ]

    def is_layout_editable(self, layout_name: str, *, ignore_built_in: bool=False):
        if not ignore_built_in and is_built_in_layout(layout_name):
            return False
        if self.is_emulation_active:
            return False
        return True

    remapped_keys_json: StringProperty(
        name="Journal of remapped keymap items per keyconfig (JSON) (do not edit!)",
        description="Serialized table of remapped items per keyconfig (keyconfig_name -> keymap -> operator -> keymap_item + remap_info)",
        default="",
    )
    @property
    def remapped_keys(self) -> Optional[Dict[str, Any]]:
        # TODO: Ideally this would return a frozenmap to enforce setter semantics, but Python's not there yet
        d = json_cached_loads(
            'kle_prefs:remapped_keys', self.remapped_keys_json, deserialize_list_encoded_sets=True
        ) if self.remapped_keys_json else {}
        return d if isinstance(d, dict) and d else {}
    @remapped_keys.setter
    def remapped_keys(self, value: Dict[str, Any]):
        self.remapped_keys_json = json_set_dumps(value)

    def get_remapped_keymaps(self) -> Optional[Dict[str, Any]]:
        keymaps = self.remapped_keys
        if not isinstance(keymaps, dict):
            return None
        removed_keymaps = []
        for keymap_key, items in keymaps.items():
            if not isinstance(keymap_key, str) or not isinstance(items, dict) or not items:
                removed_keymaps.append(keymap_key)
        for removed_keymap in removed_keymaps:
            del keymaps[removed_keymap]
        return keymaps if keymaps else None


    def ui_state(self, context=...) -> KLEUIStateProperties:
        if context is ...:
            context = bpy.context
        return context.window_manager.kle_ui_state

    def remapped_keymap_items(self, context=...):
        if context is ...:
            context = bpy.context
        remapped_keymaps = self.get_remapped_keymaps()
        if remapped_keymaps is None:
            return
        kcs = get_current_keyconfig_set(context)

        layout_translation = self.get_preferred_layout_translation()
        for km in kcs.user.keymaps:
            km_id = keymap_id(km)
            if km_id not in remapped_keymaps:
                continue
            remapped_km = remapped_keymaps[km_id]
            for kmi in km.keymap_items:
                if not is_remapped_keymap_item(kmi, layout_translation):
                    continue
                op = kmi.idname
                if not op in remapped_km:
                    continue
                remapped_op = remapped_km[op]
                rs = resolve_remapped_keymap_item(kmi, remapped_op)
                if rs is not None:
                    yield km, kmi, rs
                else:
                    kle_logger.debug(
                        f"  ! unresolved kmi: {kmi.idname} ({kmi.name}) -> {kmi_modifier_string(kmi)} & {kmi.type}\n" +
                        f"    props: " + json_set_dumps(
                            compact_operator_properties(operator_properties_to_dict(kmi.properties)), indent=2
                        ).replace('\n', '\n    ') + '\n' +
                        f"    candidates: " + json_set_dumps(remapped_op, indent=2).replace('\n', '\n    ')
                    )


    def pending_keymaps_to_emulate(self, context=...):
        if context is ...:
            context = bpy.context
        remapped_keymaps = self.get_remapped_keymaps()
        if remapped_keymaps is None:
            remapped_keymaps = {}
        kcs = get_current_keyconfig_set(context)
        # user_keymap_names = {km.name for km in kcs.user.keymaps}

        # kle_logger.debug(f"Potential keymaps ({len(kcs.user.keymaps)}): {[keymap_id(km) for km in kcs.user.keymaps]}")
        layout_translation = self.get_preferred_layout_translation()
        for km in kcs.user.keymaps:
            km_id = keymap_id(km)
            if km_id not in remapped_keymaps:
                for kmi in km.keymap_items:
                    if is_remappable_keymap_item(kmi, layout_translation):
                        # # This seems to be the case for `node.duplicate_move_linked` & friends, for some reason
                        # if kmi.idname == 'node.duplicate_move_linked':
                        #     kle_logger.debug(
                        #         f"  !! unresolved duplicate kmi km: {km_id} {kmi.idname} ({kmi.name}) -> {kmi_modifier_string(kmi)} & {kmi.type}\n" +
                        #         f"     props: " + json_set_dumps(compact_operator_properties(operator_properties_to_dict(kmi.properties)), indent=2).replace('\n', '\n    ') + '\n' +
                        #         f"     candidates: " + ', '.join(remapped_keymaps.keys())
                        #     )
                        yield km, kmi, None
            else:
                remapped_km = remapped_keymaps[km_id]
                for kmi in km.keymap_items:
                    if not is_remappable_keymap_item(kmi, layout_translation):
                        continue
                    op = kmi.idname
                    if not op in remapped_km:
                        # if kmi.idname == 'node.duplicate_move_linked':
                        #     kle_logger.debug(
                        #         f"  !! unresolved duplicate kmi op: {kmi.idname} ({kmi.name}) -> {kmi_modifier_string(kmi)} & {kmi.type}\n" +
                        #         # f"     props: " + json_set_dumps(compact_operator_properties(operator_properties_to_dict(kmi.properties)), indent=2).replace('\n', '\n    ') + '\n' +
                        #         f"     candidates: " + ', '.join(remapped_km.keys())
                        #     )
                        yield km, kmi, None
                        continue
                    rs = resolve_remapped_keymap_item(kmi, remapped_km[op])
                    if rs is None or event_type_to_char(kmi.type) == rs.get('s', None):
                        # if kmi.idname == 'node.duplicate_move_linked':
                        #     kle_logger.debug(
                        #         f"  !! unresolved duplicate kmi: {rs}, ({kmi.type})\n" +
                        #         f"     props: " + json_set_dumps(compact_operator_properties(operator_properties_to_dict(kmi.properties)), indent=2).replace('\n', '\n    ') + '\n' +
                        #         f"     candidates: " + json_set_dumps(remapped_km[op], indent=2).replace('\n', '\n    ')
                        #     )
                        yield km, kmi, rs
    def has_pending_keymaps_to_emulate(self):
        return next(self.pending_keymaps_to_emulate(), None) is not None
    def bounded_number_of_pending_keymaps_to_emulate(self, limit: int = 100) -> Optional[int]:
        it = iter(self.pending_keymaps_to_emulate())
        for i in range(limit):
            if next(it, None) is None:
                return i
        return None

    def draw(self, context):
        """Draw the add-on preferences block with controls and optional editor."""
        layout = self.layout
        column = layout.column(align=True)

        # Header
        hdr = column.row(align=True)
        split = hdr.split(factor=0.6)
        hdr_left = split.row()
        hdr_right = split.row()
        hdr_left.label(text="Go to 'Preferences > Keymap'")
        hdr_right.alignment = 'RIGHT'
        hdr_right.operator(
            KLEOperators.Info.addon_info,
            text="More info", icon='QUESTION',
            emboss=False
        )

        # Storage data preview
        ui_state = self.ui_state(context)
        def arrow_icon(show: bool) -> str:
            return 'DOWNARROW_HLT' if show else 'RIGHTARROW'

        box = column.box()
        col = box.column()
        header = col.row(align=True)
        split = header.split(factor=0.7, align=False)
        header_left, header_right = split.row(align=True), split.row(align=True)
        header_left.alignment = 'LEFT'
        header_left.prop(
            ui_state, "preferences_debug_visible",
            text="Debug addon preferences", emboss=False,
            icon=arrow_icon(ui_state.preferences_debug_visible))

        ir = header_right.row(align=True)
        # if self.is_emulation_active:
        #     ir.alert = True
        ir.operator(
            KLEOperators.import_addon_preferences,
            text="Import...", icon='IMPORT',
        )
        er = header_right.row(align=True)
        er.operator(
            KLEOperators.export_addon_preferences,
            text="Export...", icon='EXPORT',
        )

        if ui_state.preferences_debug_visible:
            indent_factor = 0.02
            split = col.column().split(factor=indent_factor)
            _, col = split.column(), split.column()

            header = col.row(align=True)
            header.alignment = 'LEFT'
            header.prop(
                ui_state, "preferences_debug_general_prefs_visible",
                text="Preferences", emboss=False,
                icon=arrow_icon(ui_state.preferences_debug_general_prefs_visible))
            if ui_state.preferences_debug_general_prefs_visible:
                split = col.row().split(factor=indent_factor * 2)
                _, right = split.column(), split.column()
                right.label(text=f"preferred_input_layout: {self.hidden__preferred_input_layout}", icon='DOT')
                right.label(text=f"preferred_target_layout: {self.hidden__preferred_target_layout}", icon='DOT')
                right.label(text=f"reapply_on_keymaps_panel: {self.reapply_on_keymaps_panel}", icon='DOT')
                right.label(text=f"reapply_on_keymaps_panel_delay: {self.reapply_on_keymaps_panel_delay}", icon='DOT')
                right.label(text=f"reapply_on_reload: {self.reapply_on_reload}", icon='DOT')
                right.label(text=f"reapply_on_reload_delay: {self.reapply_on_reload_delay}", icon='DOT')
                right.label(text=f"detect_addon_changes: {self.detect_addon_changes}", icon='DOT')
                right.label(text=f"detect_addon_changes_polling_interval: {self.detect_addon_changes_polling_interval}", icon='DOT')
                right.label(text=f"display_large_warning_button: {self.display_large_warning_button}", icon='DOT')
                right.label(text=f"large_warning_button_style: {self.large_warning_button_style}", icon='DOT')
                right.label(text=f"allow_key_conflicts_in_input_layout: {self.allow_key_conflicts_in_input_layout}", icon='DOT')
                right.label(text=f"logging_level: {self.logging_level}", icon='DOT')
                right.label(text=f"is_emulation_active: {self.is_emulation_active}", icon='DOT')

            header = col.row(align=True)
            header.alignment = 'LEFT'
            header.prop(
                ui_state, "preferences_debug_custom_layouts_visible",
                text="Custom Layouts", emboss=False,
                icon=arrow_icon(ui_state.preferences_debug_custom_layouts_visible))
            if ui_state.preferences_debug_custom_layouts_visible:
                split = col.row().split(factor=indent_factor)
                _, right = split.column(), split.column()
                for name, mapping in self.custom_layouts.items():
                    expanded = is_subkey_expanded(name, ui_state.preferences_debug_custom_layouts_expanded_subkeys)
                    row = right.row()
                    row.alignment = 'LEFT'
                    op = row.operator(
                        KLEOperators.debug_toggle_expanded_subkey,
                        text=name,
                        icon=arrow_icon(expanded),
                        emboss=False,
                    )
                    op.prefs_prop = 'preferences_debug_custom_layouts_expanded_subkeys'
                    op.subkey = name
                    if expanded:
                        split = right.row().split(factor=indent_factor)
                        _, cc = split.column(), split.column()
                        lines = json.dumps(mapping, indent=2).splitlines()
                        if "{" in lines: lines.remove("{")
                        if "}" in lines: lines.remove("}")
                        for line in lines:
                            cc.label(text=line)

            header = col.row(align=True)
            header.alignment = 'LEFT'
            header.prop(
                ui_state, "preferences_debug_remapped_keymaps_visible",
                text="Remapped keymaps", emboss=False,
                icon=arrow_icon(ui_state.preferences_debug_remapped_keymaps_visible))
            if ui_state.preferences_debug_remapped_keymaps_visible:
                remapped_expanded_subkeys = ui_state.preferences_debug_remapped_keymaps_expanded_subkeys
                remapped_expanded_subkeys_prop = 'preferences_debug_remapped_keymaps_expanded_subkeys'

                split = col.row().split(factor=indent_factor)
                _, right = split.column(), split.column()
                for km_id, remapped_km in self.remapped_keys.items():
                    km_subkey = km_id
                    km_expanded = is_subkey_expanded(km_subkey, remapped_expanded_subkeys)
                    row = right.row()
                    row.alignment = 'LEFT'
                    op = row.operator(
                        KLEOperators.debug_toggle_expanded_subkey,
                        text=km_id,
                        icon=arrow_icon(km_expanded),
                        emboss=False,
                    )
                    op.prefs_prop = remapped_expanded_subkeys_prop
                    op.subkey = km_subkey

                    if km_expanded:
                        split = right.row().split(factor=indent_factor)
                        _, ccc = split.column(), split.column()
                        for op_name, op_list in remapped_km.items():
                            op_subkey = f"{km_subkey}:{op_name}"
                            op_expanded = is_subkey_expanded(op_subkey, remapped_expanded_subkeys)
                            row = ccc.row()
                            row.alignment = 'LEFT'
                            op = row.operator(
                                KLEOperators.debug_toggle_expanded_subkey,
                                text=op_name,
                                icon=arrow_icon(op_expanded),
                                emboss=False,
                            )
                            op.prefs_prop = remapped_expanded_subkeys_prop
                            op.subkey = op_subkey

                            if op_expanded:
                                split = ccc.row().split(factor=indent_factor)
                                _, cccc = split.column(), split.column()
                                for i, remap_info in enumerate(op_list):
                                    info_subkey = f"{op_subkey}:{i}"
                                    info_expanded = is_subkey_expanded(info_subkey, remapped_expanded_subkeys)
                                    row = cccc.row()
                                    row.alignment = 'LEFT'
                                    mod = remap_info['m']
                                    text = f"{i}: {mod}{' & ' if mod and mod[-1].isalpha() else ''}{remap_info['s']} → {remap_info['t']}"
                                    op = row.operator(
                                        KLEOperators.debug_toggle_expanded_subkey,
                                        text=text,
                                        icon=arrow_icon(info_expanded),
                                        emboss=False,
                                    )
                                    op.prefs_prop = remapped_expanded_subkeys_prop
                                    op.subkey = info_subkey

                                    if info_expanded:
                                        split = cccc.row().split(factor=indent_factor)
                                        _, ccccc = split.column(), split.column()
                                        lines = json_set_dumps(remap_info, indent=2).splitlines()
                                        if "{" in lines: lines.remove("{")
                                        if "}" in lines: lines.remove("}")
                                        for line in lines:
                                            ccccc.label(text=line)

        box = column.box()
        col = box.column()
        header = col.row(align=True)
        header.alignment = 'LEFT'
        header.prop(
            ui_state, "uninstall_options_visible",
            text="Uninstall options", emboss=False,
            icon=arrow_icon(ui_state.uninstall_options_visible))

        if ui_state.uninstall_options_visible:
            indent_factor = 0.02
            split = col.column().split(factor=indent_factor)
            _, opt_col = split.column(), split.column()

            row = opt_col.row(align=True)
            row.alert = True
            row.prop(ui_state, "revert_on_uninstall")

            footer = col.row(align=True)
            footer.alert = True
            footer.label(text="Uninstall options are not saved. They will reset the next time you restart Blender.", icon='HELP')


    def export_to_json(
            self, *,
            include_custom_layouts=True,
            include_remapped_keymaps=False
    ) -> str:
        return json_set_dumps({
            "addon_id": addon_id,
            "preferences_version": preferences_version,
            "preferences": {
                pref: getattr(self, pref) for pref, condition in [
                    (pref, True) if isinstance(pref, str) else pref
                    for pref in [
                        "preferred_input_layout",
                        "preferred_target_layout",
                        "allow_non_qwerty_target_layouts",
                        "reapply_on_keymaps_panel",
                        "reapply_on_keymaps_panel_delay",
                        "reapply_on_reload",
                        "reapply_on_reload_delay",
                        "detect_addon_changes",
                        "detect_addon_changes_polling_interval",
                        "display_large_warning_button",
                        "large_warning_button_height",
                        "large_warning_button_style",
                        "allow_key_conflicts_in_input_layout",
                        "logging_level",
                        "is_emulation_active",
                        ("custom_layouts", include_custom_layouts),
                        ("remapped_keys", include_remapped_keymaps),
                    ]
                ] if condition
            },
        }, indent=2)

    def import_from_json(
            self, json_prefs: str, *,
            context=...,
            import_emulation_status=False,
            ignore_emulation_lock=False,
            inverse_update_custom_layouts=False,
            update_custom_layouts=False,
            overwrite_custom_layouts=False,
            import_remapped_keymaps=False,
    ):
        if context is ...:
            context = bpy.context
        imported_prefs = json_set_loads(json_prefs)
        if import_emulation_status:
            from .keymap_patch import reapply_keymap_translation, revert_keymap_translation
        else:
            reapply_keymap_translation, revert_keymap_translation = None, None

        try:
            ui_state = self.ui_state(context)

            if imported_prefs.get('addon_id', None) != addon_id:
                raise ValueError("Unsupported JSON preferences.")
            imported_version = imported_prefs.get('preferences_version', (0, 0))
            if imported_version[0] != preferences_version[0]:
                raise ValueError("Unsupported JSON preferences.")
            p = imported_prefs.get('preferences', {})

            # Revert emulation before import
            if import_emulation_status and self.is_emulation_active:
                revert_keymap_translation(context, log_result=True)
                self.is_emulation_active = False
                ui_state.is_emulation_applied = False

            # Preserve emulated layouts
            locked_input_custom_layout = self.preferred_input_layout if self.is_emulation_active and not ignore_emulation_lock else None
            if is_built_in_layout(locked_input_custom_layout):
                locked_input_custom_layout = None
            locked_input_custom_layout_value = dict(self.custom_layouts.get(locked_input_custom_layout, {})) if locked_input_custom_layout is not None else None
            locked_output_custom_layout = self.preferred_target_layout if self.is_emulation_active and not ignore_emulation_lock else None
            if is_built_in_layout(locked_output_custom_layout):
                locked_output_custom_layout = None
            locked_output_custom_layout_value = dict(self.custom_layouts.get(locked_output_custom_layout, {})) if locked_output_custom_layout is not None else None

            if not self.is_emulation_active or import_emulation_status or ignore_emulation_lock:
                self.preferred_input_layout = p.get('preferred_input_layout', self.preferred_input_layout)
                self.preferred_target_layout = p.get('preferred_target_layout', self.preferred_target_layout)
                if import_emulation_status or ignore_emulation_lock:
                    self.is_emulation_active = p.get('is_emulation_active', self.is_emulation_active)

            for imported_pref in [
                "reapply_on_keymaps_panel",
                "reapply_on_keymaps_panel_delay",
                "reapply_on_reload",
                "reapply_on_reload_delay",
                "detect_addon_changes",
                "detect_addon_changes_polling_interval",
                "allow_non_qwerty_target_layouts",
                "display_large_warning_button",
                "large_warning_button_height",
                "large_warning_button_style",
                "allow_key_conflicts_in_input_layout",
                "logging_level",
            ]:
                setattr(self, imported_pref, p.get(imported_pref, getattr(self, imported_pref)))

            if overwrite_custom_layouts:
                custom_layouts = p.get('custom_layouts', {})
            elif update_custom_layouts:
                custom_layouts = self.custom_layouts
                custom_layouts.update(p.get('custom_layouts', {}))
            elif inverse_update_custom_layouts:
                custom_layouts = p.get('custom_layouts', {})
                custom_layouts.update(self.custom_layouts)
            else:
                custom_layouts = self.custom_layouts

            if locked_input_custom_layout is not None:
                custom_layouts[locked_input_custom_layout] = locked_input_custom_layout_value
            if locked_output_custom_layout is not None:
                custom_layouts[locked_output_custom_layout] = locked_output_custom_layout_value

            self.custom_layouts = custom_layouts

            if import_remapped_keymaps:
                self.remapped_keys = p.get('remapped_keys', {})

            # Reapply emulation after import
            if import_emulation_status and self.is_emulation_active:
                translation = self.get_preferred_layout_translation()
                reapply_keymap_translation(translation, context, log_result=True)
                ui_state.is_emulation_applied = True

            init_ui_state()

        except Exception as e:
            raise ValueError(f"Malformed JSON preferences: {e}") from e


def init_ui_state():
    context = bpy.context
    prefs = kle_prefs(context)
    ui_state = prefs.ui_state(context)
    ui_state.current_input_layout = prefs.preferred_input_layout
    ui_state.current_target_layout = prefs.preferred_target_layout

    on_logging_level_update()


def register():
    # Register preferences classes
    bpy.utils.register_class(KLEUIStateProperties)
    bpy.utils.register_class(KLEPreferences)

    # Register UI state as a WindowManager property
    bpy.types.WindowManager.kle_ui_state = PointerProperty(type=KLEUIStateProperties)

    # Initialize UI state
    init_ui_state()

def unregister():
    # Remove UI state from the WindowManager
    del bpy.types.WindowManager.kle_ui_state

    # Unregister preferences classes
    bpy.utils.unregister_class(KLEPreferences)
    bpy.utils.unregister_class(KLEUIStateProperties)
