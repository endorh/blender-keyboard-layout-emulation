import logging

import bpy

from .keyboard_layout import LayoutTranslation, event_type_to_char, char_to_event_type
from .preferences import kle_prefs, keymap_id, KmiFingerprint, KmiAssignmentDiff


def reapply_keymap_translation(translation: LayoutTranslation, context=...):
    if context is ...:
        context = bpy.context
    prefs = kle_prefs(context)
    logger = prefs.logger

    if not translation.is_valid() and not prefs.allow_key_conflicts_in_input_layout:
        msg = "Layout mapping is invalid. Fix errors before applying."
        if logger:
            logger.warning(msg)
        return False, msg

    remapped = prefs.remapped_keys
    remaps = []
    for km, kmi, fingerprint, diff in prefs.pending_keymaps_to_emulate():
        original_type = kmi.type
        new_type = translation.map_input_type_to_output_type(original_type)
        if diff is not None:
            # Update existing entry instead of creating a duplicate
            diff.source_char = event_type_to_char(original_type)
            diff.target_char = event_type_to_char(new_type)
            if logger:
                logger.debug(f"  !! reapplied {kmi.idname}: {diff.source_char} -> {diff.target_char}")
        else:
            kmj = remapped.setdefault(keymap_id(km), {})
            kmo = kmj.setdefault(kmi.idname, [])
            kmo.append((
                KmiFingerprint.from_kmi(kmi, logger=logger),
                KmiAssignmentDiff.from_kmi_and_types(kmi, original_type, new_type),
            ))
        remaps.append((kmi, new_type))
        # if prefs.logger and prefs.logger.isEnabledFor(logging.DEBUG):
        #     prefs.logger.debug(
        #         f"  !! Serialized: {kmi.idname}, keys: {operator_properties_to_dict(kmi.properties).keys()}\n"
        #         f"    " + json.dumps(operator_properties_to_dict(kmi.properties), indent=2).replace('\n', '\n    ')
        #     )

    # Commit remap journal before performing the remap
    prefs.remapped_keys = remapped

    try:
        for kmi, new_type in remaps:
            kmi.type = new_type
        msg = f"Remapped correctly {len(remaps)} keymap items!"
        if logger:
            logger.info(msg)
        return True, msg
    except Exception as e:
        msg = f"Failed to remap keymap items: {e}"
        if logger:
            logger.warning(msg)
        return False, msg


def freeze_map(d):
    if isinstance(d, (set, frozenset)):
        return frozenset(map(freeze_map, d))
    elif isinstance(d, dict):
        return frozenset([(k, freeze_map(v)) for k, v in d.items()])
    elif isinstance(d, (list, tuple)):
        return tuple(map(freeze_map, d))
    elif hasattr(d.__class__, 'encode_json'):
        d = freeze_map(d.__class__.encode_json(d))
    return d


def revert_keymap_translation(context=...):
    if context is ...:
        context = bpy.context
    prefs = kle_prefs(context)
    logger = prefs.logger

    remapped = prefs.remapped_keys
    all_items = freeze_map([
        (km_id, op_idname, fingerprint, diff)
        for km_id, remapped_km in remapped.items()
        for op_idname, alts in remapped_km.items()
        for fingerprint, diff in alts
    ])
    processed_items = []
    for km, kmi, fingerprint, diff in prefs.remapped_keymap_items():
        km_id = keymap_id(km)
        op_idname = kmi.idname
        original_char = diff.source_char
        if original_char is not None:
            kmi.type = char_to_event_type(original_char)
        processed_items.append((km_id, op_idname, fingerprint, diff))
    processed_items_set = set(freeze_map(processed_items))
    unprocessed_items = [item for item in all_items if item not in processed_items_set]

    if logger and logger.isEnabledFor(logging.DEBUG):
        # for km_id, op_idname, fingerprint, diff in all_items:
        #     prefs.loggerlogger.debug(f"  ! {km_id} > {op_idname} > {fingerprint} > {diff}")
        # for km_id, op_idname, fingerprint, diff in processed_items:
        #     prefs.logger.debug(f"  ! proc: {km_id} > {op_idname} > {fingerprint} > {diff}")
        for km_id, op_idname, fingerprint, diff in unprocessed_items:
            logger.debug(f"  ! not found: {km_id} > {op_idname} > {fingerprint} > {diff}")
        logger.debug(f"  ! all_items ({len(all_items)})")
        logger.debug(f"  ! processed_items ({len(processed_items)})")
        logger.debug(f"  ! unprocessed_items ({len(unprocessed_items)})")

    prefs.remapped_keys = None

    if not unprocessed_items:
        msg = f"Reverted correctly {len(processed_items)} items from keyboard layout emulation!"
        if logger:
            logger.info(msg)
        return True, msg
    else:
        msg = f"Could not find & revert {len(unprocessed_items)}/{len(all_items)} items (see console)! (reverted {len(processed_items)} items successfully). Consider restoring a keymap preset or manually revising your keymap."
        if logger:
            logger.warning(msg)
        return False, msg
