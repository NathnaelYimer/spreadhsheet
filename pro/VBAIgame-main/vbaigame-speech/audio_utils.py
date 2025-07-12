import sounddevice as sd

def list_input_devices():
    """Return a list of available input (microphone) devices as (index, name) tuples."""
    devices = sd.query_devices()
    input_devices = []
    for idx, dev in enumerate(devices):
        if dev['max_input_channels'] > 0:
            input_devices.append((idx, dev['name']))
    return input_devices


def get_first_microphone_device():
    """Return the index of the first available microphone device, or None if not found."""
    devices = sd.query_devices()
    for idx, dev in enumerate(devices):
        if dev['max_input_channels'] > 0 and ('mic' in dev['name'].lower() or 'microphone' in dev['name'].lower()):
            return idx
    # Fallback: just return the first input device
    for idx, dev in enumerate(devices):
        if dev['max_input_channels'] > 0:
            return idx
    return None
