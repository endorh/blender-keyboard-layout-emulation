import bpy

from .keyboard_layout import LayoutTranslation, event_type_to_char, char_to_event_type
from .preferences import kle_prefs, kmi_signature, kmi_modifier_string, keymap_id
from .constants import kle_logger


def reapply_keymap_translation(translation: LayoutTranslation, context=..., verbose=True, log_result=False):
    if context is ...:
        context = bpy.context
    prefs = kle_prefs(context)
    if not translation.is_valid() and not prefs.allow_key_conflicts_in_input_layout:
        msg = "Layout mapping is invalid. Fix errors before applying."
        if log_result:
            kle_logger.warn(msg)
        return False, msg

    remapped = prefs.remapped_keys
    remaps = []
    for km, kmi, info in prefs.pending_keymaps_to_emulate():
        original_type = kmi.type
        new_type = translation.map_input_type_to_output_type(original_type)
        if info is not None:
            # Update existing entry instead of creating a duplicate
            info['s'] = event_type_to_char(original_type)
            info['t'] = event_type_to_char(new_type)
            if verbose:
                kle_logger.debug(f"  !! reapplied {kmi.idname}: {info['s']} -> {info['t']}")
        else:
            kmj = remapped.setdefault(keymap_id(km), {})
            kmo = kmj.setdefault(kmi.idname, [])
            kmo.append({
                **kmi_signature(kmi),
                'm': kmi_modifier_string(kmi),
                's': event_type_to_char(original_type),
                't': event_type_to_char(new_type),
            })
        remaps.append((kmi, new_type))
        # if verbose:
        #     kle_logger.debug(
        #         f"  !! Serialized: {kmi.idname}, keys: {operator_properties_to_dict(kmi.properties).keys()}\n"
        #         f"    " + json.dumps(operator_properties_to_dict(kmi.properties), indent=2).replace('\n', '\n    ')
        #     )

    # Mark emulation as active before doing the actual remap
    prefs.remapped_keys = remapped

    try:
        for kmi, new_type in remaps:
            kmi.type = new_type
        msg = f"Remapped correctly {len(remaps)} keymap items!"
        if log_result:
            kle_logger.info(msg)
        return True, msg
    except Exception as e:
        msg = f"Failed to remap keymap items: {e}"
        if log_result:
            kle_logger.warn(msg)
        return False, msg


def freeze_map(d):
    if isinstance(d, (set, frozenset)):
        return frozenset(map(freeze_map, d))
    elif isinstance(d, dict):
        return frozenset([(k, freeze_map(v)) for k, v in d.items()])
    elif isinstance(d, (list, tuple)):
        return tuple(map(freeze_map, d))
    return d


def revert_keymap_translation(context=..., verbose=True, log_result=False):
    if context is ...:
        context = bpy.context
    prefs = kle_prefs(context)

    remapped = prefs.remapped_keys
    all_items = [
        (km_id, op_idname, info)
        for km_id, remapped_km in remapped.items()
        for op_idname, alts in remapped_km.items()
        for info in alts
    ]
    processed_items = []
    for km, kmi, info in prefs.remapped_keymap_items():
        km_id = keymap_id(km)
        op_idname = kmi.idname
        actual_type = kmi.type
        original_type = info.get('s', None)
        if original_type is not None:
            kmi.type = char_to_event_type(original_type)
        processed_items.append((km_id, op_idname, info))
    processed_items_set = set(freeze_map(processed_items))
    unprocessed_items = [item for item in all_items if freeze_map(item) not in processed_items_set]

    if verbose:
        # for km_id, op_idname, info in all_items:
        #     kle_logger.debug(f"  ! {km_id} > {op_idname} > {info}")
        # for km_id, op_idname, info in processed_items:
        #     kle_logger.debug(f"  ! proc: {km_id} > {op_idname} > {info}")
        for km_id, op_idname, info in unprocessed_items:
            kle_logger.debug(f"  ! not found: {km_id} > {op_idname} > {info}")
        kle_logger.debug(f"  ! all_items ({len(all_items)})")
        kle_logger.debug(f"  ! processed_items ({len(processed_items)})")
        kle_logger.debug(f"  ! unprocessed_items ({len(unprocessed_items)})")

    prefs.remapped_keys = None

    if not unprocessed_items:
        msg = f"Reverted correctly {len(processed_items)} items from keyboard layout emulation!"
        if log_result:
            kle_logger.info(msg)
        return True, msg
    else:
        msg = f"Could not find & revert {len(unprocessed_items)}/{len(all_items)} items (see console)! (reverted {len(processed_items)} items successfully). Consider restoring a keymap preset or manually revising your keymap."
        if log_result:
            kle_logger.warn(msg)
        return False, msg
