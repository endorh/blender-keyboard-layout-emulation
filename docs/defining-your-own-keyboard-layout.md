# Defining your own keyboard layout
This extension provides several built-in keyboard layouts:

- QWERTY (default, standard US-QWERTY)
- Dvorak (standard US-Dvorak)
- Colemak
- AZERTY (French)
- QWERTZ (German)

Usually, you select these layouts in the **input** keyboard layout dropdown
from the top bar injected by this extension in the `Preferences > Keymap` menu.

![Keyboard layout emulation top bar](images/keymaps-top-bar.png)

## Creating a keyboard layout
To define your own keyboard layout, you must first give it a name.
To do so, press the `+` button besides the **input** keyboard layout dropdown.

!!! info "Do not confuse this with the button to create a new keymap preset"

You may first select the closest built-in layout in the dropdown,
to use it as an initial value.

## Editing a keyboard layout
Once you have chosen a name, press the pencil button besides the `+`/`-` buttons to
reveal the keyboard layout editor.

![Keyboard layout editor](images/keyboard-layout-editor.png)

Next, reassign all the keys you need in the editor.
Press any key and immediately type its corresponding key on your layout to reassign it.

???+ question "Why can does my key show up differently or not at all?"
    Blender cannot internally represent most non-standard keys.
    For example, pressing `'` (the apostrophe key), even on the default US-QWERTY layout,
    will display `"` (QUOTE) in Blender.
    
    This extension cannot do anything about this problem.
    If Blender does not recognize some keys of your layout as keys at all,
    this extension cannot help you.
    Instead, you should [report a bug](https://projects.blender.org/blender/blender/issues/new/choose)
    to Blender and request the team to add support for your keyboard.
    
    Ideally, Blender should be able to support any and all keys, present and future,
    but the current keymap system was designed poorly, implemented even more
    poorly, and has been awaiting a complete redesign for a long time.
    Unfortunately, no one is motivated enough to tackle this problem.
 
???+ question "I cannot avoid conflicts in my keyboard layout! What do I do?"
    If your keyboard layout is recognized in Blender in a way that it contains
    two keys corresponding to the same Blender recognized key (for example,
    if your layout contains separate keys for `'` and `"`), you may still
    apply the keyboard layout emulation.
    The extension remembers which was the original assignment of each remapped
    shortcut to be able to revert the emulation reliably even in this case.
    
    ![Conflict in the keyboard layout editor](images/keyboard-layout-editor-conflict.png)
    
    However, in this case, you will need to enable the `Allow conflicts` checkbox
    displayed below the keyboard layout editor.
    Naturally, in this case you will have two keys in your layout that trigger the same
    shortcut, since Blender cannot distinguish those two keys at all.

## Importing a keyboard layout
When you show the keyboard layout editor, it will also display buttons labeled
`Import layout...` and `Export layout...`.

These allow you to import and export keyboard layouts as simple JSON files.

!!! info "Alternatively, you can also import and export all the add-on's [preferences](preferences.md#import-preferences)"