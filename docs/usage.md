## Using Keyboard Layout Emulation
Ensure you have [installed the extension](installation.md).

Navigate to `Preferences > Keymap`.
You should see a bar on top of the keymap preset selector with two
keyboard layout selectors, which default to QWERTY, followed by an
`Apply` and a `Revert` button.

![Keyboard Layout Emulation](images/keymaps-top-bar.png)

There is also a gear button on the right end of the bar to reveal
the keyboard layout emulation [preferences](preferences.md).

### Quick Setup
1. Choose your preferred keyboard layout in the **input** layout selector.
   This is the second dropdown in the top bar, the one that isn't grayed out
   and is next to the `+` button.
2. Press the `Apply` button.
3. Observe how all the keyboard layouts below have been remapped accordingly.
   They will remain remapped until you press the `Revert` button again
   or disable/uninstall the extension.

If you cannot find your preferred keyboard layout in the dropdown,
you may also [define your own](defining-your-own-keyboard-layout.md).

### User Interface
#### **Target** keyboard layout selector
The leftmost dropdown in the top bar lets you choose a **target** keyboard layout.
For most purposes, this should be left as QWERTY, hence why it is
[disabled by default](preferences.md#allow-non-qwerty-target-layouts)
to avoid an easy beginner mistake.

This should be set to the keyboard layout for which the keymap preset you are using
was designed for, usually QWERTY.

#### **Input** keyboard layout selector
The second dropdown in the top bar lets you choose your **input** keyboard layout.
This is where you choose your preferred keyboard layout.

This value will be used to determine how the keyboard shortcuts should be remapped
so that your input is interpreted as if it was typed on a QWERTY layout rather
than your actual layout.

#### Keyboard layout editor
Besides the **input** keyboard layout selector, there are `+` and `-` buttons,
and a pencil button.
These let you define your own keyboard layouts and edit them.
Press the pencil button to reveal the keyboard layout editor.

![Keyboard layout editor](images/keyboard-layout-editor.png)

> No, I do not use the Spanish Dvorak layout, it's just a convenient example.

Built-in layouts cannot be edited. Instead, create a copy of them using the
`+` button, and give it a different name before editing it.

In the keyboard layout editor, press any key and subsequently type the key
it should correspond to on your layout to reassign it.
Press `Escape` or click anywhere to cancel reassigning a key.
Changes are immediately saved in your layout.

You may also use the `Import layout...` and `Export layout...` buttons to
import or export keyboard layouts as simple JSON files containing a mapping
of characters.

#### Applying and Reverting keyboard layout emulation
The `Apply` button enables keyboard layout emulation.

The emulation remaps all your keyboard shortcuts in a way that
pressing the corresponding QWERTY shortcut on your non-QWERTY
keyboard layout still triggers the action designed for QWERTY
layouts (e.g., pressing `O` in Dvorak will trigger `S` (Scale)).

This will not affect the text you input in properties, search fields
nor the text editor, so you can still type on your preferred keyboard layout.

Unfortunately, this is not a simple *apply and forget* operation.
> Once applied, the extension will remember this and reapply the remapping
> every time you restart Blender, open a new file, or install a new extension.
> This is necessary to ensure that keyboard shortcuts defined by other extensions
> are also reliably remapped.
> 
> Every remapped shortcut is remembered by the extension to avoid remapping
> the same shortcut twice over, as well as to ensure that we can reliably
> revert the remapping.

The `Revert` button reverts the remapping, and ensures it is not reapplied
again until you choose so.

##### Gotchas
There are a few shortcuts (e.g., `Node Editor (Global) > Duplicate`, i.e., `node.duplicate_move`)
that experience glitches in Blender, even if you remap them yourself as a user.

![Glitchy node duplicate shortcuts](images/glitchy-key-map-items-node-duplicate.png)

You may notice that when you revert emulation, these shortcuts may appear as if they were
still modified, but if you inspect them closely you will observe that they have been
properly reverted.
This appears to be a bug in Blender in the process of comparing these shortcuts to their
default values.
