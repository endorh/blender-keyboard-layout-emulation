# Exporting keymap presets
When you apply keyboard layout emulation, all your keyboard shortcuts are
effectively remapped.

This means that if you export your keymap as a preset while emulation is active,
the exported preset will contain the layout emulation baked into it.

!!! note
    This can be useful if you want to share your remapped keymap, or
    import it later after uninstalling this extension, to avoid relying on it.
    
    However, if you import the preset and enable emulation, your preset will be then
    remapped by emulation a second time, which you probably don't want.

Your options on this matter are:

- Disable emulation before exporting the preset, if you want to use it
  with emulation, or share it with people who use other keyboard layouts.
- Export the preset with the emulation baked into it and then uninstall/disable
  this extension, if you don't want to rely on this extension afterwards.

### Caveats
Unfortunately, using presets to emulate QWERTY shortcuts has some limitations:

- Keyboard shortcuts added by other add-ons may get reverted the next time
  you restart Blender. This is a known Blender issue.
- Even some built-in keyboard shortcuts (like `node.duplicate_move`) may alse
  get reverted the next time you restart Blender.
  This seems to be a bug in Blender's ability to compare the value
  of some keyboard shortcuts.
  For example, if you edit it in the UI, it may sometimes fail to detect
  when you have reverted it manually to its default value.

!!! tip
    If you don't like the way this extension dynamically reapplies emulation every
    time you restart Blender, or after you install another add-on, you may disable
    these features in the extension's [preferences](preferences.md), rather than disabling
    the extension altogether.
