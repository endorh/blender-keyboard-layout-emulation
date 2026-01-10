## Keyboard Layout Emulation – an extension for Blender

> [!TIP]
> You are in the `docs` branch, which contains the editable sources of the user manual for this extension.
> You may want to:
> - Read the [user manual](https://endorh.github.io/blender-keyboard-layout-emulation/)
> - Go to the [main](https://github.com/endorh/blender-keyboard-layout-emulation) branch for source code

This Blender extension automatically reassigns all keyboard shortcuts to emulate a QWERTY
keyboard layout on a user-specified non-QWERTY keyboard layout, allowing users to type
QWERTY keyboard shortcuts while typing text in their preferred keyboard layout.

This allows users to benefit from the default keyboard shortcuts without changing their
keyboard layout for typing text/using shortcuts, making use of the design effort already
spent by others in designing the default keyboard shortcuts.

The default keyboard shortcuts include well over a thousand keyboard shortcuts involving
remappable keyboard keys. Tailoring all keyboard shortcuts to a different keyboard layout
in a way that is convenient for one-hand typing and with good mnemonics in the
corresponding layout is not a task everyone can afford.

### Building the manual
The docs in this branch are built using [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/).

To build them locally:
1. Install `mkdocs`: `pip install mkdocs`
2. Run `python -m mkdocs build` from the root of the repository.
   Refer to its [documentation](https://www.mkdocs.org/user-guide/cli/#mkdocs-build) for more options.

The docs are built automatically on every push to the `docs` branch, and deployed to GitHub Pages
([here](https://endorh.github.io/blender-keyboard-layout-emulation/)).
This is achieved by the
[build-docs](https://github.com/endorh/blender-keyboard-layout-emulation/edit/docs/.github/workflows/build-docs.yml)
workflow.

### Release process
When a new version is released, the quick link in the
[docs/installation.md](docs/installation.md)
file has to be updated to point to the new release.
