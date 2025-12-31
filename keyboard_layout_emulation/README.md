## Keyboard Layout Emulation (Blender add-on)

Automatically reassigns all keyboard shortcuts to emulate a QWERTY keyboard layout on a
user-specified non-QWERTY keyboard layout, allowing users to type QWERTY keyboard shortcuts
while typing text in their preferred keyboard layout.

This allows users to benefit from the default keyboard shortcuts without changing their
keyboard layout for typing text/using shortcuts, making use of the design effort already
spent by others in designing the default keyboard shortcuts.

The default keyboard shortcuts include well over a thousand keyboard shortcuts involving
remappable keyboard keys. Tailoring all keyboard shortcuts to a different keyboard layout
in a way that is convenient for one-hand typing and with good mnemonics in the
corresponding layout is not a task everyone can afford.

### Usage
The add-on injects a dropdown above the usual "Preferences > Keymap" screen, allowing
the user to select an input keyboard layout on top of which to emulate QWERTY.
This dropdown includes buttons to add and edit new custom keyboard layouts, displaying
a keyboard-shaped editor right below.

Besides this dropdown there are buttons to apply the keyboard layout emulation and revert it.
When applied, be careful because newly created keyboard shortcuts will get remapped after
the next reload, so it is recommended to revert the emulation before creating or editing
keyboard shortcuts.
Keyboard shortcuts added by add-ons, even if installed later on, will get remapped on every
reload/file load, but no shortcut will ever be remapped twice. We keep a list of which
keyboard shortcuts we remapped, and from which key to which key for that purpose.

The emulation is automatically reverted if you ever disable or uninstall this add-on
to avoid damaging your keymaps.
If you save or export a keymap preset while the emulation is active, the saved/exported
keymap preset will contain the baked keyboard shortcuts reassigned by the emulation.
Hence, if you disable emulation, load it, and re-enable emulation, it will be re-remapped
twice, something you probably don't want.
Either revert the emulation before saving/exporting if you plan to use emulation over that
preset, or create presets that contain the baked emulation and don't use emulation with them.

In other words, you can use this add-on just to generate presets, disable it,
and then use those presets.
However, this will likely not allow you to consistently remap add-on keyboard shortcuts.

### Technical details and ranting
This entire add-on would not be necessary if Blender allowed matching keyboard shortcuts by
scan code, rather than the fragile, idiosyncratic, per-platform pipeline it uses:
```
    OS keyboard event -> ASCII character -> GHOST character -> Blender character
```
(GHOST is Blender's input layer library)

For example, Blender could never distinguish between a `'` (single quote) key and a
`"` (double quote key) if a keyboard ever used two different keys for these characters,
as both get mapped to the same Blender character (QUOTE).

While ideally the add-on would hook onto the keyboard event processing pipeline, this is not
possible from the Python API (for good reason).
Instead, we have to resort to the only available workaround: permanently modifying the user's
preferences, reassigning all of their shortcuts to emulate the specified layout.

This unfortunate workaround would be simple, were it not for the fact that Blender's support
for customizing keyboard shortcuts is very poorly designed and even more poorly implemented.
A redesign of this system has been requested but not addressed for decades.
For instance, some of its flaws that affect us are:

- Only a subset of ASCII characters are supported (as exemplified above)
- [bug] Some built-in keyboard shortcuts (e.g., `node.duplicate_move` and friends) get reset
  after every restart/loading a new file, unless the user is using a keymap preset imported
  from Python that was exported including those problematic built-in shortcuts.
- Keyboard shortcuts defined by add-ons cannot be modified persistently because add-ons are
  loaded too late during initialization, resulting in add-ons registering their keyboard
  shortcuts after the user's keymap has been loaded and never being updated with the user
  changes.
- Keyboard shortcuts (referred to internally in Blender as "keymap items") do not have stable
  unique identifiers, which makes tracking them across restarts unreliable.
- User preferences cannot be modified when Blender is unregistering add-ons as part of the
  natural shutdown process when Blender is being quit, thus we cannot reliably
  undo our reassignment on shutdown.

> [!NOTE]
> (Off topic)
> Another grave flaw of Blender's keymap system is that users are presented with a lie.
> A lie that even the wording of the user manual appears to believe:
> Users can save different "keymap presets" and even export them as Python scripts.
> Although the interface displays a dropdown with the last loaded "keymap preset"
> above the keymap configuration, keyboard shortcuts edited in the interface are only
> ever stored in a unique user keymap, not on a per-"keymap preset" basis.
> This defies user expectations because a dropdown displaying a "keymap preset" is
> naturally understood as displaying the *current* keymap preset,
> not the *last applied* "keymap preset".
> 
> Only when a "keymap preset" is created does it capture the current user keymap.
> When a "keymap preset" is selected in the dropdown, its stored user keymap is simply read
> to override the current user keymap.
> 
> To illustrate how absurd the current implementation is, observe that the only way
> to effectively *update* an existing "keymap preset" is:
> 
> 1. Save the desired user keymap as a "keymap preset" with a *different name*,
>    because overwriting presets is not allowed.
> 2. Delete the old "keymap preset"
> 3. Save again with the desired —now free— name
> 4. Delete the temporary "keymap preset" created in the first step.
> 
> While these "preset" semantics can be found in many other parts of Blender, they are not
> practical nor intuitive for handling user preferences and are very poorly conveyed
> by the user interface.
> 
> ---
> Even more flaws can be easily pointed out. For example, despite keyboard shortcut definitions
> being an order-sensitive list, Blender does not allow users to reorder them.
> If you are ever bored, please contribute to a future redesign of this system.

To overcome the limitations of the existing keymap system in Blender, this add-on is forced to:

- Update the reassignment of all keyboard shortcuts on every restart/file load.
- Keep a list with fingerprints of all reassigned shortcuts, to track which got
  reset during the last restart/file load, and which are still reassigned,
  as well as to be able to reliably revert the reassignment.
- Revert the reassignment whenever the add-on is unregistered.
  While this serves no purpose during a normal shutdown of Blender, as in that case it is already
  too late to modify user preferences; it does ensure that the user keymaps are not permanently
  altered if the user decides to manually disable or uninstall the add-on.

This ensures that even add-on keyboard shortcuts and glitchy shortcuts (`node.duplicate_move`)
are reliably reassigned for as long as keyboard layout emulation is active.