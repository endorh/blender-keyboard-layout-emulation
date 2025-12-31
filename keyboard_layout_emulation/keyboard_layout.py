from __future__ import annotations

from typing import Dict, Set, Tuple, Optional


__all__ = [
    'LayoutTranslation',
    'is_built_in_layout',
    'us_qwerty_physical_remappable_keys',
    'remappable_keymap_item_types',
    'event_type_to_char',
    'event_type_to_char_or_none',
    'char_to_event_type',
    'char_to_event_type_or_none',
]


us_qwerty_physical_remappable_keys = [
    # Letters
    *[chr(c) for c in range(ord('A'), ord('Z') + 1)],
    # Numbers
    *[str(i) for i in range(0, 10)],
    # Standard US-QWERTY keyboard symbols
    "`", "-", "=", "[", "]", ";", "'", ",", ".", "/", "\\",
]

# Set of remappable Blender Event Types
remappable_keymap_item_types = {
    *'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
    'ZERO',
    'ONE',
    'TWO',
    'THREE',
    'FOUR',
    'FIVE',
    'SIX',
    'SEVEN',
    'EIGHT',
    'NINE',
    # 'LEFT_CTRL',
    # 'LEFT_ALT',
    # 'LEFT_SHIFT',
    # 'RIGHT_ALT',
    # 'RIGHT_CTRL',
    # 'RIGHT_SHIFT',
    # 'OSKEY',
    # 'HYPER',
    # 'APP',
    'GRLESS',
    # 'ESC',
    # 'TAB',
    # 'RET',
    # 'SPACE',
    # 'LINE_FEED',
    # 'BACK_SPACE',
    # 'DEL',
    'SEMI_COLON',
    'PERIOD',
    'COMMA',
    'QUOTE',
    'ACCENT_GRAVE',
    'MINUS',
    'PLUS',
    'SLASH',
    'BACK_SLASH',
    'EQUAL',
    'LEFT_BRACKET',
    'RIGHT_BRACKET',
    # 'LEFT_ARROW',
    # 'DOWN_ARROW',
    # 'RIGHT_ARROW',
    # 'UP_ARROW',
    # 'NUMPAD_2',
    # 'NUMPAD_4',
    # 'NUMPAD_6',
    # 'NUMPAD_8',
    # 'NUMPAD_1',
    # 'NUMPAD_3',
    # 'NUMPAD_5',
    # 'NUMPAD_7',
    # 'NUMPAD_9',
    # 'NUMPAD_PERIOD',
    # 'NUMPAD_SLASH',
    # 'NUMPAD_ASTERIX',
    # 'NUMPAD_0',
    # 'NUMPAD_MINUS',
    # 'NUMPAD_ENTER',
    # 'NUMPAD_PLUS',
    # 'F1',
    # 'F2',
    # 'F3',
    # 'F4',
    # 'F5',
    # 'F6',
    # 'F7',
    # 'F8',
    # 'F9',
    # 'F10',
    # 'F11',
    # 'F12',
    # 'F13',
    # 'F14',
    # 'F15',
    # 'F16',
    # 'F17',
    # 'F18',
    # 'F19',
    # 'F20',
    # 'F21',
    # 'F22',
    # 'F23',
    # 'F24',
    # 'PAUSE',
    # 'INSERT',
    # 'HOME',
    # 'PAGE_UP',
    # 'PAGE_DOWN',
    # 'END',
}

# Blender Event Type -> ASCII character/name
event_type_to_char_dict = {
    **{k: k for k in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"},
    'ZERO': '0',
    'ONE': '1',
    'TWO': '2',
    'THREE': '3',
    'FOUR': '4',
    'FIVE': '5',
    'SIX': '6',
    'SEVEN': '7',
    'EIGHT': '8',
    'NINE': '9',
    # 'LEFT_CTRL': "LCtrl",
    # 'LEFT_ALT': "LAlt",
    # 'LEFT_SHIFT': "LShift",
    # 'RIGHT_ALT': "RAlt",
    # 'RIGHT_CTRL': "RCtrl",
    # 'RIGHT_SHIFT': "RShift",
    # 'OSKEY': "OS",
    # 'HYPER': "Hyp",
    # 'APP': "App,
    'GRLESS': "<",
    # 'ESC': "Esc",
    # 'TAB': "Tab",
    # 'RET': "Return",
    # 'SPACE': "Space",
    # 'LINE_FEED': "Line",
    # 'BACK_SPACE': "Back",
    # 'DEL': "Del",
    'SEMI_COLON': ";",
    'PERIOD': ".",
    'COMMA': ",",
    # Blender does not define an event type for `'`, but uses QUOTE indistinctively for it (besides `"`)
    # See blender/intern/ghost/intern/GHOST_SystemWin32.cc#processSpecialKey
    #   (but only if you're prepared to witness case-by-case translation of
    #    Windows Virtual Key codes -> characters -> GHOST event types
    #    that only handles OEM keys for French keyboards, by mapping it to F13)
    'QUOTE': "\"",
    'ACCENT_GRAVE': "`",
    'MINUS': "-",
    'PLUS': "+",
    'SLASH': "/",
    'BACK_SLASH': "\\",
    'EQUAL': "=",
    'LEFT_BRACKET': "[",
    'RIGHT_BRACKET': "]",
    # 'LEFT_ARROW',
    # 'DOWN_ARROW',
    # 'RIGHT_ARROW',
    # 'UP_ARROW',
    # 'NUMPAD_2',
    # 'NUMPAD_4',
    # 'NUMPAD_6',
    # 'NUMPAD_8',
    # 'NUMPAD_1',
    # 'NUMPAD_3',
    # 'NUMPAD_5',
    # 'NUMPAD_7',
    # 'NUMPAD_9',
    # 'NUMPAD_PERIOD',
    # 'NUMPAD_SLASH',
    # 'NUMPAD_ASTERIX',
    # 'NUMPAD_0',
    # 'NUMPAD_MINUS',
    # 'NUMPAD_ENTER',
    # 'NUMPAD_PLUS',
    # 'F1',
    # 'F2',
    # 'F3',
    # 'F4',
    # 'F5',
    # 'F6',
    # 'F7',
    # 'F8',
    # 'F9',
    # 'F10',
    # 'F11',
    # 'F12',
    # 'F13',
    # 'F14',
    # 'F15',
    # 'F16',
    # 'F17',
    # 'F18',
    # 'F19',
    # 'F20',
    # 'F21',
    # 'F22',
    # 'F23',
    # 'F24',
    # 'PAUSE',
    # 'INSERT',
    # 'HOME',
    # 'PAGE_UP',
    # 'PAGE_DOWN',
    # 'END',
}
char_to_keymap_type_dict = {
    ch: typ for typ, ch in event_type_to_char_dict.items()
}

def event_type_to_char(event_type: str) -> str:
    return event_type_to_char_dict.get(event_type, event_type)
def event_type_to_char_or_none(event_type: str) -> str:
    return event_type_to_char_dict.get(event_type, None)
def char_to_event_type(char: str) -> str:
    return char_to_keymap_type_dict.get(char, char)
def char_to_event_type_or_none(char: str) -> str:
    return char_to_keymap_type_dict.get(char, None)


class LayoutTranslation:
    """
    Represents the translation between a keyboard layout and QWERTY.
    """

    def __init__(self, in_out_dict: Dict[str, str], out_in_dict: Dict[str, str]=...):
        in_out = {i: o for i, o in in_out_dict.items() if i != o}
        if out_in_dict is ...:
            non_remapped_keys = {k for k in us_qwerty_physical_remappable_keys if k not in in_out}
            conflicting_keys = set()
            out_in = {}
            for k, v in in_out.items():
                if v in out_in or v in non_remapped_keys:
                    conflicting_keys.add(v)
                else:
                    out_in[v] = k
        else:
            conflicting_keys = set()
            out_in = {o: i for o, i in out_in_dict.items() if o != i}
            for i, o in in_out.items():
                if o not in out_in or out_in[o] != i:
                    conflicting_keys.add(i)
            for o, i in out_in.items():
                if i not in in_out or in_out[i] != o:
                    conflicting_keys.add(i)
        self._in_out_dict = in_out
        self._out_in_dict = out_in
        self._conflicting_keys = conflicting_keys

    @classmethod
    def identity(cls) -> LayoutTranslation:
        return LayoutTranslation({}, {})

    @classmethod
    def from_dict(cls, in_out: Dict[str, str], out_in: Dict[str, str]=...) -> LayoutTranslation:
        return LayoutTranslation(in_out, out_in)

    @classmethod
    def from_qwerty_string_mapping(cls, qwerty: str, replace: str) -> LayoutTranslation:
        """
        Create a key mapping between two strings, one for QWERTY symbols, another for their
        alternative characters, spelled in the same order.
        Spaces are ignored in both strings, allowed for clarity and alignment.
        Consider using a triple-quoted string to avoid escaping special characters.
        """
        return LayoutTranslation({
            qwerty_key: alternative_key
            for qwerty_key, alternative_key in zip(
                qwerty.replace(' ', ''), replace.replace(' ', ''))
        })

    @classmethod
    def inverse(cls, layout: LayoutTranslation) -> LayoutTranslation:
        return LayoutTranslation(layout._out_in_dict, layout._in_out_dict)

    @classmethod
    def compose(cls, *layouts: LayoutTranslation) -> LayoutTranslation:
        if not layouts:
            return cls.identity()
        in_out = dict(layouts[-1]._in_out_dict)
        out_in = dict(layouts[0]._out_in_dict)
        for layout in reversed(layouts[:-1]):
            in_out.update({
                i: in_out.get(o, o)
                for i, o in layout._in_out_dict.items()
            })
        for layout in layouts[1:]:
            out_in.update({
                o: out_in.get(i, i)
                for o, i in layout._out_in_dict.items()
            })
        return LayoutTranslation(in_out, out_in)

    @classmethod
    def from_input_to_target(cls, input_translation, target_translation):
        return cls.compose(input_translation, cls.inverse(target_translation))

    QWERTY: LayoutTranslation
    AZERTY: LayoutTranslation
    QWERTZ: LayoutTranslation
    dvorak: LayoutTranslation
    colemak: LayoutTranslation

    built_in: Dict[str, LayoutTranslation]
    built_in_enum_items: Tuple[Optional[Tuple[str, str, str]], ...]

    @property
    def in_out_dict(self) -> Dict[str, str]:
        return dict(self._in_out_dict)
    @property
    def out_in_dict(self) -> Dict[str, str]:
        return dict(self._out_in_dict)

    @property
    def remapped_input_characters(self) -> Set[str]:
        return set(self._in_out_dict.keys())

    @property
    def remapped_output_characters(self) -> Set[str]:
        return set(self._out_in_dict.keys())

    def map_input_to_output(self, key: str) -> str:
        return self._in_out_dict.get(key, key)
    def map_output_to_input(self, key: str) -> str:
        return self._out_in_dict.get(key, key)

    def map_input_type_to_output_type(self, event_type: str) -> str:
        return char_to_event_type(self.map_input_to_output(event_type_to_char(event_type)))
    def map_output_type_to_input_type(self, event_type: str) -> str:
        return char_to_event_type(self.map_output_to_input(event_type_to_char(event_type)))

    def conflicting_keys(self) -> Set[str]:
        return self._conflicting_keys
    def is_valid(self):
        return not self._conflicting_keys
    def is_identity(self):
        return not self._in_out_dict and not self._out_in_dict

    def update(self, in_out: Dict[str, str], out_in: Dict[str, str]=...) -> LayoutTranslation:
        # Notice that this is different from composing, it's overriding
        # In particular, we care about the idempotent maps in `in_out`/`out_in`
        new_in_out = dict(self._in_out_dict)
        new_in_out.update(in_out)
        if out_in is ...:
            out_in = {}
            for i, o in in_out.items():
                if o not in out_in:
                    out_in[o] = i
        new_out_in = dict(self._out_in_dict)
        new_out_in.update(out_in)
        return LayoutTranslation(new_in_out, new_out_in)
    def update_key(self, in_key: str, out_key: str) -> LayoutTranslation:
        return self.update({in_key: out_key})

    def copy(self):
        return self.__copy__()
    def __copy__(self):
        return LayoutTranslation(dict(self._in_out_dict), dict(self._out_in_dict))


# Built-in layouts
LayoutTranslation.QWERTY = LayoutTranslation.identity()
LayoutTranslation.AZERTY = LayoutTranslation.from_qwerty_string_mapping(
    # We don't remap `.` as `:` because Blender doesn't support `:` as an input key.
    # However, I imagine the GHOST library translates `:` in French layouts as `.`
    "QA  WZ  ;M,",
    "AQ  ZW  M,;")
LayoutTranslation.QWERTZ = LayoutTranslation.from_qwerty_string_mapping(
    "YZ",
    "ZY")
LayoutTranslation.dvorak = LayoutTranslation.from_qwerty_string_mapping(
    # Blender's input pipeline treats `'` and `"` as `QUOTE`, but prefers `"` when displaying it.
    # Regrettably, we need to conform here, and write the Dvorak layout using `"` in place of `'`:
    """  -=  QWERTYUIOP[]\  ASDFGHJKL;"  ZXCVBNM,./  """,
    """  []  ",.PYFGCRL/=\  AOEUIDHTNS-  ;QJKXBMWVZ  """)
LayoutTranslation.colemak = LayoutTranslation.from_qwerty_string_mapping(
    # For Colemak we don't replace `'` by `"`, since it will be optimized away
    # as an idempotent mapping anyways.
    """  QWERTYUIOP[]\  ASDFGHJKL;'  ZXCVBNM,./  """,
    """  QWFPGJLUY;[]\  ARSTDHNEIO'  ZXCVBKM,./  """)

LayoutTranslation.built_in = {
    'QWERTY': LayoutTranslation.QWERTY,
    'AZERTY': LayoutTranslation.AZERTY,
    'QWERTZ': LayoutTranslation.QWERTZ,
    'Dvorak': LayoutTranslation.dvorak,
    'Colemak': LayoutTranslation.colemak,
}
# It is important to ensure that strings returned by enum providers are kept referenced in Python.
# See https://docs.blender.org/api/5.0/bpy.props.html#bpy.props.EnumProperty
LayoutTranslation.built_in_enum_items = (
    ('QWERTY', 'QWERTY', "Standard US-QWERTY keyboard layout"),
    None,  # Separator
    ('AZERTY', 'AZERTY', "French AZERTY keyboard layout.\nDoes not remap `'`, `[`, `]` and `.` due to Blender's inability to represent internally accents/dollar/colon keys."),
    ('QWERTZ', 'QWERTZ', "German QWERTZ keyboard layout.\nDoes not remap any keys with accentuated characters due to Blender's inability to represent them internally."),
    None,  # Separator
    ('Dvorak', 'Dvorak', "Standard US-Dvorak keyboard layout.\nThe `'` key is represented as `\"` due to Blender's inability to represent it distinctly."),
    ('Colemak', 'Colemak', "Colemak keyboard layout"),
)

def is_built_in_layout(layout_name: str) -> bool:
    return layout_name in LayoutTranslation.built_in
