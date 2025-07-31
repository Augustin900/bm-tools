import math
import re
import os
import glob

#############################CONFIGURATION#############################
config = {
    'sample_path': "./samples/",                # Path to the directory containing the audio samples
    'sample_rate': 48000,                       # Sample rate of your audio files (Hz) - crucial for ms conversions
    'release_time': 1.2,                        # Default release time for all notes in seconds
    'min_cutoff': 100,                          # Minimum cutoff frequency for the low-velocity layer in Hz
    'max_cutoff': 22000,                        # Maximum cutoff frequency for the high-velocity layer in Hz
    'sample_format': "KEPSREC{note:03d}.wav",   # Format string for sample filenames, use '{note}' to insert MIDI note number. Example: "piano_{note:03d}.wav" for "piano_021.wav", "piano_108.wav"
    'sample_range': (21, 108),                  # MIDI note number range of the available samples (lowest, highest)
    'key_range': (0, 127),                      # MIDI key number range to map the samples to (lowest, highest)
    'global_sample_offset': 0,                  # NEW: Offset for sample filenames. If samples are named 1,2,3 but correspond to MIDI 21,22,23, set to 20.

    'enable_dynamics_curve': True,      # Enable dynamics curve (volume shaping across velocity layers)
    'dynamics_curve': "exponential",    # Curve for dynamics (volume) across velocity layers: "linear", "logarithmic", "exponential"
    'dynamics_curve_intensity': 0.65,   # Intensity of the dynamics curve (higher values mean more pronounced dynamic range)

    'enable_cutoff_velocity_layers': False, # Enables or disables velocity layers
    'layer_count': 26,                      # Number of velocity layers to create (1-128)
    'velocity_curve': "exponential",        # Curve for velocity layers: "linear", "logarithmic", "exponential"
    'curve_intensity': 0.70,                # Intensity of the velocity curve (higher values mean more pronounced velocity response)
    'overlap_percent': 100,                 # Percentage of overlap between velocity layers (0-100)
        
    'random_offset': False,           # Enable random sample start offset
    'offset_range': (0, 100),         # Range for random offset (min, max). Unit defined by random_offset_unit
    'random_offset_unit': "ms",       # Unit for random offset: "samples" or "ms"
    'random_offset_mode': "global",   # "per_layer" (offset varies by layer) or "global" (same max offset for all layers)
    'enable_offset_curve': False,     # Enable a curve for the random offset amount across layers (only applies if random_offset_mode is "per_layer")
    'offset_curve': "linear",         # Curve type for offset (if enabled): "linear", "logarithmic", "exponential"
    'offset_curve_intensity': 0.5,    # Intensity of the offset curve

    'enable_resonance': False,   # Enable filter resonance adjustment across layers
    'resonance_range': (1, 10),  # Range for resonance (min, max)

    'enable_reverb': False,   # Enable Dattorro's Progenitor Reverb
    'reverb_send': 60,        # Reverb send amount (0-100)
    'reverb_roomsize': 50,    # Reverb room size (0-100)
    'reverb_damp': 50,        # Reverb damping (0-100)
    'reverb_width': 100,      # Reverb stereo width (0-100)

    'enable_hammers': True,         # Enable separate hammer/mechanical noises
    'hammers_format': "hammer.wav", # Filename for hammer noises (e.g., "hammer.wav")
    'hammer_volume': 16,            # Volume for hammer noises (dB)

    'enable_sample_panning': True,  # Enable sample panning based on key position
    'panning_aggression': 90,       # How aggressive the panning is (0-100). 0 means no panning.

    'enable_round_robin': False,         # Enable random sample selection (round-robin)
    'round_robin_count': 4,              # Number of round-robin variations per note/layer
    'round_robin_offset_variance': 42,   # Max random offset (ms or samples) added to each RR sample
    'round_robin_volume_variance': 1.5,  # Max random volume variance (dB) added to each RR sample
    'round_robin_pan_variance': 8.0,     # Max random pan variance (pan units) added to each RR sample
    'round_robin_cutoff_variance': 33,   # Max random cutoff variance (Hz) added to each RR sample
    'round_robin_offset_unit': 'ms',     # Unit for round robin offset variance: "samples" or "ms"

    'enable_crossfade': False,    # Enable crossfading between velocity layers
    'crossfade_overlap_vel': 6,   # Velocity range (e.g., 8 units) over which layers crossfade

    'enable_fil_veltrack': False, # Enable Filter Envelope Velocity Tracking
    'fil_veltrack_amount': 100,   # Amount of filter velocity tracking (0-200)

    'enable_ampeg_decay_veltrack': False, # Enable Amplitude Envelope Velocity Tracking - Granular (Decay)
    'ampeg_decay_veltrack_amount': -100,  # Amount of amplitude decay velocity tracking (-100 to 100)

    'enable_ampeg_attack_veltrack': False, # Enable Amplitude Envelope Attack Velocity Tracking
    'ampeg_attack_veltrack_amount': -50,   # Amount of amplitude attack velocity tracking (-100 to 100)

    'enable_ampeg_sustain_veltrack': False, # Enable Amplitude Envelope Sustain Velocity Tracking
    'ampeg_sustain_veltrack_amount': 50,    # Amount of amplitude sustain velocity tracking (-100 to 100)

    'enable_ampeg_hold_veltrack': False,   # Enable Amplitude Envelope Hold Velocity Tracking
    'ampeg_hold_veltrack_amount': 100,     # Amount of amplitude hold velocity tracking (-100 to 100)

    'enable_ampeg_release_veltrack': False, # Enable Amplitude Envelope Release Velocity Tracking
    'ampeg_release_veltrack_amount': -100,  # Amount of amplitude release velocity tracking (-100 to 100)

    'enable_gain_veltrack': False, # NEW: Enable Gain Velocity Tracking
    'gain_veltrack_amount': 0,     # NEW: Amount of gain velocity tracking (-100 to 100, typically for fine-tuning)
    
    'enable_keyboard_zones': False, # Enable splitting the keyboard into separate zones
    'keyboard_zone_count': 1,       # Number of keyboard zones to create (1-128)
    
    # List of polyphony values for each zone. Must have `keyboard_zone_count` elements if `enable_keyboard_zones` is True.
    'zone_polyphony_values': [4],   # Example: [1, 2, 4] for 3 zones with different polyphony

    'note_selfmask_enabled': False,         # Whether to enable voice self-masking (applied per layer)
    'conditional_selfmask_enabled': False,  # Enable conditional note_selfmask based on lo_vel (applied per layer)
    'selfmask_min_lovel': 62,               # Minimum lo_vel for note_selfmask=1 to be applied

    'global_polyphony': None, # New: Sets a global polyphony limit for the entire instrument. Set to None to disable.
    
    'additional_region_options': {}, # Dictionary for additional opcodes for each region (e.g., {"tune": 0, "bend_up": 1200}) # THIS MUST BE THE LAST SETTING
}

def generate_sfz(sample_path, release_time,
                  min_cutoff, max_cutoff,
                  layer_count, sample_format,
                  sample_range, key_range,
                  velocity_curve="logarithmic",
                  curve_intensity=1.0,
                  overlap_percent=5,
                  random_offset=False,
                  offset_range=(0, 0),
                  random_offset_unit="samples",
                  sample_rate=44100,
                  random_offset_mode="per_layer",
                  enable_offset_curve=False,
                  offset_curve="linear",
                  offset_curve_intensity=1.0,
                  resonance_range=(1, 10),
                  enable_resonance=True,
                  enable_reverb=False,
                  reverb_send=50,
                  reverb_roomsize=50,
                  reverb_damp=50,
                  reverb_width=100,
                  enable_hammers=False,
                  hammers_format="hammer.wav",
                  hammer_volume=8,
                  enable_dynamics_curve=True,
                  dynamics_curve="logarithmic",
                  dynamics_curve_intensity=1.0,
                  additional_region_options=None,
                  enable_cutoff_velocity_layers=True,
                  enable_sample_panning=False,
                  panning_aggression=50,
                  enable_round_robin=False,
                  round_robin_count=1,
                  round_robin_offset_variance=0,
                  round_robin_volume_variance=0,
                  round_robin_pan_variance=0,
                  round_robin_cutoff_variance=0,
                  round_robin_offset_unit="ms",
                  enable_crossfade=False,
                  crossfade_overlap_vel=8,
                  enable_fil_veltrack=False,
                  fil_veltrack_amount=100,
                  enable_ampeg_decay_veltrack=False,
                  ampeg_decay_veltrack_amount=50,
                  enable_ampeg_attack_veltrack=False,
                  ampeg_attack_veltrack_amount=100,
                  enable_ampeg_sustain_veltrack=False,
                  ampeg_sustain_veltrack_amount=100,
                  # New Velocity-to-Envelope Curve Mapping parameters
                  enable_ampeg_hold_veltrack=False,
                  ampeg_hold_veltrack_amount=0,
                  enable_ampeg_release_veltrack=False,
                  ampeg_release_veltrack_amount=0,
                  global_sample_offset=0,
                  # New parameters for keyboard zoning
                  enable_keyboard_zones=False,
                  keyboard_zone_count=1,
                  zone_polyphony_values=[4],
                  # Existing selfmasking parameters
                  note_selfmask_enabled=True,
                  conditional_selfmask_enabled=False,
                  selfmask_min_lovel=100,
                  # New global polyphony parameter (moved)
                  global_polyphony=None,
                  enable_gain_veltrack=False, # NEW PARAMETER
                  gain_veltrack_amount=0):    # NEW PARAMETER


    # Determine the effective number of layers to process
    effective_layer_count = 1 if not enable_cutoff_velocity_layers else layer_count

    if effective_layer_count > 128:
        raise ValueError("Maximum effective layer count is 128.")

    if not os.path.exists(sample_path):
        raise FileNotFoundError(f"Sample path not found: {sample_path}")

    lowest_sample, highest_sample = sample_range
    lowest_key, highest_key = key_range
    center_key = (lowest_key + highest_key) / 2

    existing_sample_formats = {}
    sample_names_with_spaces = set()

    for note in range(lowest_sample, highest_sample + 1):
        file_note = note - global_sample_offset
        formatted_sample_file = os.path.join(sample_path, sample_format.format(note=file_note))
        unformatted_sample_file = os.path.join(sample_path, f"{file_note}.wav")
        unformatted_file_no_ext = os.path.join(sample_path, f"{file_note}")

        potential_files = glob.glob(formatted_sample_file) or glob.glob(unformatted_sample_file) or glob.glob(unformatted_file_no_ext + ".*")

        if potential_files:
            sample_filename = os.path.basename(potential_files[0])
            if ' ' in sample_filename:
                sample_names_with_spaces.add(sample_filename)
            existing_sample_formats[note] = sample_filename

    if sample_names_with_spaces:
        print("Error: The following sample names contain spaces. Please remove spaces from these filenames:")
        for filename in sorted(list(sample_names_with_spaces)):
            print(f"- {filename}")
        raise ValueError("Sample names with spaces found. Please rename your sample files.")

    if not existing_sample_formats:
        raise FileNotFoundError(f"No sample files found matching pattern: {sample_format} or without leading zeros.")

    if min_cutoff >= max_cutoff:
        raise ValueError("min_cutoff must be less than max_cutoff")

    if effective_layer_count < 1:
        raise ValueError("effective_layer_count must be at least 1") # Changed from layer_count

    if not 0 <= overlap_percent <= 100:
        raise ValueError("overlap_percent must be between 0 and 100")

    if velocity_curve not in ["linear", "logarithmic", "exponential"]:
        raise ValueError("velocity_curve must be one of: linear, logarithmic, exponential")

    if curve_intensity <= 0:
        raise ValueError("curve_intensity must be greater than 0")

    if lowest_key < 0 or highest_key > 127:
        raise ValueError("key_range must be within MIDI range 0-127")

    if lowest_sample < 0 or highest_sample > 127:
        raise ValueError("sample_range must be within MIDI range 0-127")

    if random_offset and offset_range[0] < 0:
        raise ValueError("minimum offset must be >= 0")

    if random_offset and offset_range[0] >= offset_range[1]:
        raise ValueError("max_offset must be greater than min_offset for random offsets")

    if random_offset_unit not in ["samples", "ms"]:
        raise ValueError("random_offset_unit must be 'samples' or 'ms'.")

    if random_offset_unit == "ms" and not (isinstance(sample_rate, (int, float)) and sample_rate > 0):
        raise ValueError("sample_rate must be a positive number if random_offset_unit is 'ms'.")

    if random_offset_mode not in ["per_layer", "global"]:
        raise ValueError("random_offset_mode must be 'per_layer' or 'global'.")

    if offset_curve not in ["linear", "logarithmic", "exponential"]:
        raise ValueError("offset_curve must be one of: linear, logarithmic, exponential")

    if offset_curve_intensity <= 0:
        raise ValueError("offset_curve_intensity must be greater than 0")

    if not (isinstance(resonance_range, tuple) and len(resonance_range) == 2 and
             isinstance(resonance_range[0], (int, float)) and isinstance(resonance_range[1], (int, float)) and
             resonance_range[0] >= 0 and resonance_range[1] >= resonance_range[0]):
        raise ValueError("resonance_range must be a tuple (min_resonance, max_resonance) with non-negative values.")

    if not isinstance(enable_resonance, bool):
        raise ValueError("enable_resonance must be a boolean value (True or False).")

    if not isinstance(enable_reverb, bool):
        raise ValueError("enable_reverb must be a boolean value (True or False).")

    if not (0 <= reverb_send <= 100):
        raise ValueError("reverb_send must be between 0 and 100.")
    if not (0 <= reverb_roomsize <= 100):
        raise ValueError("reverb_roomsize must be between 0 and 100.")
    if not (0 <= reverb_damp <= 100):
        raise ValueError("reverb_damp must be between 0 and 100.")
    if not (0 <= reverb_width <= 100):
        raise ValueError("reverb_width must be between 0 and 100.")

    if not isinstance(enable_hammers, bool):
        raise ValueError("enable_hammers must be a boolean value (True or False).")

    if not isinstance(enable_dynamics_curve, bool):
        raise ValueError("enable_dynamics_curve must be a boolean value (True or False).")

    if dynamics_curve not in ["linear", "logarithmic", "exponential"]:
        raise ValueError("dynamics_curve must be one of: linear, logarithmic, exponential")

    if dynamics_curve_intensity <= 0:
        raise ValueError("dynamics_curve_intensity must be greater than 0")

    if not isinstance(enable_sample_panning, bool):
        raise ValueError("enable_sample_panning must be a boolean value (True or False).")

    if not (0 <= panning_aggression <= 100):
        raise ValueError("panning_aggression must be between 0 and 100.")

    if not isinstance(enable_round_robin, bool):
        raise ValueError("enable_round_robin must be a boolean value (True or False).")

    if enable_round_robin and not (1 <= round_robin_count <= 128):
        raise ValueError("round_robin_count must be between 1 and 128 if enabled.")

    if round_robin_offset_variance < 0 or round_robin_volume_variance < 0 or \
       round_robin_pan_variance < 0 or round_robin_cutoff_variance < 0:
        raise ValueError("Round robin variances must be non-negative.")

    if round_robin_offset_unit not in ["samples", "ms"]:
        raise ValueError("round_robin_offset_unit must be 'samples' or 'ms'.")

    if not isinstance(crossfade_overlap_vel, int) or not (0 <= crossfade_overlap_vel <= 127):
        raise ValueError("crossfade_overlap_vel must be an integer between 0 and 127.")

    if not isinstance(fil_veltrack_amount, (int, float)) or not (0 <= fil_veltrack_amount <= 200):
        raise ValueError("fil_veltrack_amount must be a number between 0 and 200.")

    if not isinstance(ampeg_decay_veltrack_amount, (int, float)) or not (-100 <= ampeg_decay_veltrack_amount <= 100):
        raise ValueError("ampeg_decay_veltrack_amount must be a number between -100 and 100.")

    if not isinstance(ampeg_attack_veltrack_amount, (int, float)) or not (-100 <= ampeg_attack_veltrack_amount <= 100):
        raise ValueError("ampeg_attack_veltrack_amount must be a number between -100 and 100.")

    if not isinstance(ampeg_sustain_veltrack_amount, (int, float)) or not (-100 <= ampeg_sustain_veltrack_amount <= 100):
        raise ValueError("ampeg_sustain_veltrack_amount must be a number between -100 and 100.")

    # Validation for new envelope velocity tracking options
    if not isinstance(enable_ampeg_hold_veltrack, bool):
        raise ValueError("enable_ampeg_hold_veltrack must be a boolean value (True or False).")
    if not isinstance(ampeg_hold_veltrack_amount, (int, float)) or not (-100 <= ampeg_hold_veltrack_amount <= 100):
        raise ValueError("ampeg_hold_veltrack_amount must be a number between -100 and 100.")

    if not isinstance(enable_ampeg_release_veltrack, bool):
        raise ValueError("enable_ampeg_release_veltrack must be a boolean value (True or False).")
    if not isinstance(ampeg_release_veltrack_amount, (int, float)) or not (-100 <= ampeg_release_veltrack_amount <= 100):
        raise ValueError("ampeg_release_veltrack_amount must be a number between -100 and 100.")

    # Validation for gain_veltrack
    if not isinstance(enable_gain_veltrack, bool):
        raise ValueError("enable_gain_veltrack must be a boolean value (True or False).")
    if not isinstance(gain_veltrack_amount, (int, float)) or not (-100 <= gain_veltrack_amount <= 100):
        raise ValueError("gain_veltrack_amount must be a number between -100 and 100.")

    # Validation for new keyboard zoning options
    if enable_keyboard_zones:
        if not (1 <= keyboard_zone_count <= 128):
            raise ValueError("keyboard_zone_count must be between 1 and 128 if keyboard zones are enabled.")
        if not isinstance(zone_polyphony_values, list) or len(zone_polyphony_values) != keyboard_zone_count:
            raise ValueError(f"zone_polyphony_values must be a list with {keyboard_zone_count} elements when keyboard_zones are enabled.")
        if any(not (1 <= val <= 128) for val in zone_polyphony_values):
            raise ValueError("Each polyphony value in zone_polyphony_values must be between 1 and 128.")

    # Validation for new global_polyphony
    if global_polyphony is not None and (not isinstance(global_polyphony, int) or not (1 <= global_polyphony <= 128)):
        raise ValueError("global_polyphony must be an integer between 1 and 128, or None.")

    min_resonance, max_resonance = resonance_range

    cutoffs = []
    if enable_cutoff_velocity_layers:
        for i in range(effective_layer_count): # Changed to effective_layer_count
            pos = i / (effective_layer_count - 1) if effective_layer_count > 1 else 0 # Changed to effective_layer_count
            if velocity_curve == "linear":
                factor = pos ** curve_intensity if curve_intensity != 1.0 else pos
            elif velocity_curve == "logarithmic":
                factor = pos ** (0.85 * curve_intensity)
            else:
                factor = pos ** (1.25 * curve_intensity)
            cutoff = int(min_cutoff * (max_cutoff / min_cutoff) ** factor)
            cutoffs.append(cutoff)
    else:
        default_cutoff = int(min_cutoff * (max_cutoff / min_cutoff) ** 0.5)
        cutoffs = [default_cutoff] * effective_layer_count # Changed to effective_layer_count

    velocity_ranges = []
    velocity_span = 127
    base_increment = velocity_span / effective_layer_count # Changed to effective_layer_count
    overlap_amount = (overlap_percent / 100) * base_increment

    for i in range(effective_layer_count): # Changed to effective_layer_count
        lo_vel = int(max(1, (i * base_increment) - overlap_amount))
        hi_vel = int(min(127, ((i + 1) * base_increment) + overlap_amount))
        if hi_vel == lo_vel:
            hi_vel += 1
        if hi_vel > 127:
            hi_vel = 127
        if lo_vel >= hi_vel:
            lo_vel = int(max(1, hi_vel -1))
            if lo_vel < 1:
              lo_vel = 1
            if hi_vel == 127 and lo_vel == 127:
              lo_vel = 126
        velocity_ranges.append((lo_vel, hi_vel))

    quoted_sample_path = f'"{sample_path}"' if ' ' in sample_path else sample_path

    sfz_content = f"""// Dynamic SFZ with {effective_layer_count} customizable layers
// Script created by AG89 and a bunch of GPTs
<control>
default_path={quoted_sample_path}

<global>
ampeg_release={release_time}
volume=0
pan=0
"""
    # Add global polyphony if specified
    if global_polyphony is not None:
        sfz_content += f"polyphony={global_polyphony}\n"

    sfz_content += "// Velocity curve: {velocity_curve} (intensity: {curve_intensity})\n"


    if enable_dynamics_curve:
        sfz_content += f"// Dynamics curve: {dynamics_curve} (intensity: {dynamics_curve_intensity})\n"

    if enable_reverb:
        sfz_content += f"send_effect=101 reverb send={reverb_send} reverb_roomsize={reverb_roomsize} reverb_damp={reverb_damp} reverb_width={reverb_width}\n"

    if enable_resonance:
        sfz_content += f"// Resonance control enabled: range {min_resonance}-{max_resonance}\n"
    else:
        sfz_content += "// Resonance control disabled (using default behavior)\n"

    if random_offset:
        min_offset, max_offset = offset_range
        sfz_content += f"// Random sample start offsets enabled: {min_offset}-{max_offset} {random_offset_unit} (Mode: {random_offset_mode})\n"
        if enable_offset_curve:
            sfz_content += f"// Offset curve: {offset_curve} (intensity: {offset_curve_intensity})\n"

    if enable_round_robin:
        sfz_content += f"// Random sample/region selection enabled: {round_robin_count} variations per note/layer\n"

    if enable_crossfade:
        sfz_content += f"// Velocity Crossfading enabled with {crossfade_overlap_vel} velocity units overlap.\n"

    if enable_fil_veltrack:
        sfz_content += f"// Filter Envelope Velocity Tracking enabled: fil_veltrack={fil_veltrack_amount}\n"

    if enable_ampeg_decay_veltrack:
        sfz_content += f"// Amplitude Envelope Velocity Tracking - Granular (Decay) enabled: ampeg_decay_veltrack={ampeg_decay_veltrack_amount}\n"

    if enable_ampeg_attack_veltrack:
        sfz_content += f"// Amplitude Envelope Attack Velocity Tracking enabled: ampeg_attack_veltrack={ampeg_attack_veltrack_amount}\n"

    if enable_ampeg_sustain_veltrack:
        sfz_content += f"// Amplitude Envelope Sustain Velocity Tracking enabled: ampeg_sustain_veltrack={ampeg_sustain_veltrack_amount}\n"
    
    # New: Add comments for Ampeg Hold/Release Veltrack
    if enable_ampeg_hold_veltrack:
        sfz_content += f"// Amplitude Envelope Hold Velocity Tracking enabled: ampeg_hold_veltrack={ampeg_hold_veltrack_amount}\n"

    if enable_ampeg_release_veltrack:
        sfz_content += f"// Amplitude Envelope Release Velocity Tracking enabled: ampeg_release_veltrack={ampeg_release_veltrack_amount}\n"

    # NEW: Add comment for gain_veltrack
    if enable_gain_veltrack:
        sfz_content += f"// Gain Velocity Tracking enabled: gain_veltrack={gain_veltrack_amount}\n"

    if conditional_selfmask_enabled:
        sfz_content += f"// Conditional selfmasking enabled: note_selfmask=1 applied if lovel >= {selfmask_min_lovel}\n"
    elif note_selfmask_enabled:
        sfz_content += f"// Note selfmask enabled globally.\n"

    if enable_keyboard_zones:
        sfz_content += f"// Keyboard zoning enabled: {keyboard_zone_count} zones with custom polyphony.\n"


    sfz_content += "\n"

    existing_samples_list = sorted(existing_sample_formats.keys())
    key_to_sample_map = {}

    for key in range(lowest_key, highest_key + 1):
        if lowest_sample <= key <= highest_sample and key in existing_sample_formats:
            key_to_sample_map[key] = key
        else:
            valid_nearest_sample = None
            min_distance = float('inf')

            for sample_note in existing_samples_list:
                distance = abs(key - sample_note)
                is_adjacent_with_own_sample = (abs(key - sample_note) == 1) and (sample_note in existing_sample_formats)

                if not is_adjacent_with_own_sample:
                    if distance < min_distance:
                        min_distance = distance
                        valid_nearest_sample = sample_note

            if valid_nearest_sample is not None:
                key_to_sample_map[key] = valid_nearest_sample
            else:
                nearest_sample = None
                min_distance_fallback = float('inf')
                for sample_note in existing_samples_list:
                    distance = abs(key - sample_note)
                    if distance < min_distance_fallback:
                        min_distance_fallback = distance
                        nearest_sample = sample_note
                key_to_sample_map[key] = nearest_sample if nearest_sample is not None else lowest_sample

    # Calculate key ranges for keyboard zones
    key_zones = []
    if enable_keyboard_zones:
        keys_per_zone = (highest_key - lowest_key + 1) / keyboard_zone_count
        for z in range(keyboard_zone_count):
            zone_low_key = lowest_key + round(z * keys_per_zone)
            zone_high_key = lowest_key + round((z + 1) * keys_per_zone) - 1
            if z == keyboard_zone_count - 1: # Ensure the last zone covers the highest key
                zone_high_key = highest_key
            key_zones.append((zone_low_key, zone_high_key))
    else:
        key_zones.append((lowest_key, highest_key)) # Single zone for the entire keyboard

    for z_idx, (zone_low_key, zone_high_key) in enumerate(key_zones):
        if enable_keyboard_zones:
            current_zone_polyphony = zone_polyphony_values[z_idx]
            # Add a comment for the zone
            sfz_content += f"// Zone {z_idx + 1}: Keys {zone_low_key}-{zone_high_key}, Polyphony: {current_zone_polyphony}\n"

        for i in range(effective_layer_count): # Changed to effective_layer_count
            lo_vel, hi_vel = velocity_ranges[i]
            current_cutoff = cutoffs[i]

            sfz_content += f"""<group>
lokey={zone_low_key} hikey={zone_high_key}
lovel={lo_vel} hivel={hi_vel}
"""
            # Conditional filter application: Only add filter if velocity layers are enabled AND there's more than 1 effective layer
            if enable_cutoff_velocity_layers and effective_layer_count > 1:
                sfz_content += f"""cutoff={current_cutoff}
fil_type=lpf_2p
"""
            # Apply polyphony based on zoning. If not zoned, no polyphony limit is applied.
            if enable_keyboard_zones:
                sfz_content += f"note_polyphony={current_zone_polyphony}\n"
            
            if conditional_selfmask_enabled:
                if lo_vel >= selfmask_min_lovel:
                    sfz_content += f"note_selfmask=1\n"
            elif note_selfmask_enabled:
                sfz_content += f"note_selfmask=1\n"


            if enable_fil_veltrack:
                sfz_content += f"fil_veltrack={fil_veltrack_amount}\n"

            if enable_resonance:
                resonance = min_resonance + (max_resonance - min_resonance) * (i / (effective_layer_count - 1) if effective_layer_count > 1 else 0) # Changed to effective_layer_count
                sfz_content += f"resonance={resonance:.2f}\n"

            if enable_dynamics_curve:
                dynamics_factor = i / (effective_layer_count - 1) if effective_layer_count > 1 else 0 # Changed to effective_layer_count
                if dynamics_curve == "linear":
                    dynamics_factor = dynamics_factor ** dynamics_curve_intensity if dynamics_curve_intensity != 1.0 else dynamics_factor
                elif dynamics_curve == "logarithmic":
                    dynamics_factor = dynamics_factor ** (0.85 * dynamics_curve_intensity)
                else:
                    dynamics_factor = dynamics_factor ** (1.25 * dynamics_curve_intensity)
                volume_adjustment = round(-6 * dynamics_factor * dynamics_curve_intensity, 1)
            else:
                volume_adjustment = round(-6 * (i / (effective_layer_count - 1) if effective_layer_count > 1 else 0), 1) # Changed to effective_layer_count

            sfz_content += f"""volume={volume_adjustment}
ampeg_veltrack=100
"""
            if enable_ampeg_decay_veltrack:
                sfz_content += f"ampeg_decay_veltrack={ampeg_decay_veltrack_amount}\n"

            if enable_ampeg_attack_veltrack:
                sfz_content += f"ampeg_attack_veltrack={ampeg_attack_veltrack_amount}\n"

            if enable_ampeg_sustain_veltrack:
                sfz_content += f"ampeg_sustain_veltrack={ampeg_sustain_veltrack_amount}\n"
            
            # New: Add ampeg_hold_veltrack
            if enable_ampeg_hold_veltrack:
                sfz_content += f"ampeg_hold_veltrack={ampeg_hold_veltrack_amount}\n"

            # New: Add ampeg_release_veltrack
            if enable_ampeg_release_veltrack:
                sfz_content += f"ampeg_release_veltrack={ampeg_release_veltrack_amount}\n"

            # NEW: Add gain_veltrack
            if enable_gain_veltrack:
                sfz_content += f"gain_veltrack={gain_veltrack_amount}\n"


            if enable_crossfade:
                if i > 0:
                    xfin_lovel = lo_vel
                    xfin_hivel = min(lo_vel + crossfade_overlap_vel, hi_vel)
                    sfz_content += f"xfin_lovel={xfin_lovel} xfin_hivel={xfin_hivel}\n"

                if i < effective_layer_count - 1: # Changed to effective_layer_count
                    xfout_hivel = hi_vel
                    xfout_lovel = max(hi_vel - crossfade_overlap_vel, lo_vel)
                    sfz_content += f"xfout_hivel={xfout_hivel} xfout_lovel={xfout_lovel}\n"

            sfz_content += "\n"

            for key in range(zone_low_key, zone_high_key + 1): # Iterate only over keys within the current zone
                sample_note = key_to_sample_map[key]
                sample_filename = existing_sample_formats.get(sample_note)

                if not sample_filename:
                    file_note_for_filename_reconstruction = sample_note - global_sample_offset
                    sample_filename = sample_format.format(note=file_note_for_filename_reconstruction)

                pitch_adjustment = ""
                if key != sample_note:
                    cents = (key - sample_note) * 100
                    pitch_adjustment = f" tune={cents}"

                base_offset_random_param = ""
                if random_offset:
                    min_offset, max_offset = offset_range
                    if random_offset_mode == "per_layer" and enable_offset_curve:
                        offset_curve_factor = i / (effective_layer_count - 1) if effective_layer_count > 1 else 0 # Changed to effective_layer_count
                        if offset_curve == "linear":
                            offset_amount_raw = min_offset + (max_offset - min_offset) * offset_curve_factor
                        elif offset_curve == "logarithmic":
                            log_arg = 1 + offset_curve_factor * (math.exp(offset_curve_intensity) - 1)
                            if log_arg <= 0:
                                log_arg = 1e-9
                            offset_amount_raw = min_offset + (max_offset - min_offset) * math.log(log_arg) / offset_curve_intensity
                        else:
                            exp_factor = (math.exp(offset_curve_factor * offset_curve_intensity) - 1) / (math.exp(offset_curve_intensity) - 1)
                            offset_amount_raw = min_offset + (max_offset - min_offset) * exp_factor
                    else:
                        offset_amount_raw = max_offset

                    offset_amount_samples = int(round(offset_amount_raw * (sample_rate / 1000.0))) if random_offset_unit == "ms" else int(round(offset_amount_raw))
                    base_offset_random_param = f" offset_random={offset_amount_samples}"

                base_pan_param = ""
                if enable_sample_panning:
                    pan_value = (key - center_key) / (highest_key - lowest_key) * (panning_aggression / 100) * 100
                    pan_value = max(-100, min(100, pan_value))
                    base_pan_param = f" pan={pan_value:.2f}"

                region_line = (
                    f"<region> key={key} sample={sample_filename}{pitch_adjustment}"
                    f"{base_offset_random_param}{base_pan_param} loop_mode=off" 
                )

                if additional_region_options:
                    for option, value in additional_region_options.items():
                        if isinstance(value, str):
                            if "{note}" in value:
                                value = value.format(note=sample_note)
                            if "{key}" in value:
                                value = value.format(key=key)
                        region_line += f" {option}={value}"

                sfz_content += region_line + "\n"

    if enable_hammers:
        sfz_content += """
// Hammer Noises
"""
        # Hammer noises are typically global, not per-zone, so iterate over velocity layers once
        for i, (lo_vel, hi_vel) in enumerate(zip(velocity_ranges, cutoffs)):
            sfz_content += f"""<group>
lovel={lo_vel} hivel={hi_vel}
"""
            _dynamics_curve_intensity = dynamics_curve_intensity
            _dynamics_curve = dynamics_curve
            _hammer_volume = hammer_volume
            _enable_dynamics_curve = enable_dynamics_curve
            _effective_layer_count = effective_layer_count # Changed to effective_layer_count

            if _enable_dynamics_curve:
                dynamics_factor = i / (_effective_layer_count - 1 if _effective_layer_count > 1 else 1) # Changed to effective_layer_count
                if _dynamics_curve == "linear":
                    dynamics_factor = dynamics_factor ** _dynamics_curve_intensity if _dynamics_curve_intensity != 1.0 else dynamics_factor
                elif _dynamics_curve == "logarithmic":
                    dynamics_factor = dynamics_factor ** (0.85 * _dynamics_curve_intensity)
                else:
                    dynamics_factor = dynamics_factor ** (1.25 * _dynamics_curve_intensity)
                hammer_volume_adjustment = _hammer_volume + round(-6 * dynamics_factor * _dynamics_curve_intensity, 1)
            else:
                hammer_volume_adjustment = _hammer_volume + round(-6 * (i / (_effective_layer_count - 1) if _effective_layer_count > 1 else 0), 1) # Changed to effective_layer_count

            sfz_content += f"volume={hammer_volume_adjustment}\n"
            sfz_content += f"""<region> key={key_range[0]}-{key_range[1]} sample="{hammers_format}" loop_mode=off
"""
            sfz_content += "</group>\n"

    generate_sfz.existing_sample_formats = existing_sample_formats
    generate_sfz.key_to_sample_map = key_to_sample_map

    return sfz_content


def analyze_key_mapping(key_to_sample_map, existing_sample_formats, lowest_key, highest_key, lowest_sample, highest_sample):
    """
    Analyzes the key to sample mapping for potential issues like
    skipped notes, samples mapped to unexpected keys, or keys mapped
    to themselves when no sample exists.
    """
    issues = []

    # Identify existing sample notes for easier checking
    existing_sample_notes = set(existing_sample_formats.keys())

    for key in range(lowest_key, highest_key + 1):
        mapped_sample = key_to_sample_map.get(key)

        # Check for direct mapping to a non-existent sample
        if mapped_sample is None:
            issues.append(f"Key {key}: Not mapped to any sample.")
        elif mapped_sample not in existing_sample_notes:
            issues.append(f"Key {key}: Mapped to non-existent sample {mapped_sample}.")

        # Check for "stretching" - a key being mapped to a sample far away
        if key in existing_sample_notes:
            if mapped_sample != key and abs(key - mapped_sample) > 2 and mapped_sample in existing_sample_notes:
                issues.append(f"Key {key} (has own sample): Mapped to distant sample {mapped_sample} (Distance: {abs(key - mapped_sample)}). Consider if this is intended.")
        else:
            if mapped_sample is not None and abs(key - mapped_sample) > 5:
                issues.append(f"Key {key} (no own sample): Mapped to distant sample {mapped_sample} (Distance: {abs(key - mapped_sample)}).")

        # Check if an adjacent key is mapped to this key's sample when it has its own
        for adj_offset in [-1, 1]:
            adj_key = key + adj_offset
            if lowest_key <= adj_key <= highest_key:
                if adj_key in existing_sample_notes and key_to_sample_map.get(adj_key) == key and adj_key != key:
                    issues.append(f"Key {adj_key}: Mapped to adjacent key {key} which has its own sample (Key {adj_key} also has a sample).")
                if key in existing_sample_notes and key_to_sample_map.get(adj_key) == key and adj_key not in existing_sample_notes:
                    issues.append(f"Key {adj_key}: Mapped to adjacent key {key} (Key {key} has its own sample, Key {adj_key} does not).")

        if key not in existing_sample_formats and key_to_sample_map.get(key) == lowest_sample and any(n in existing_sample_formats for n in [key - 1, key + 1] if lowest_key <= n <= highest_key):
            issues.append(f"""Key {key}: Skipped - no specific mapping, and neighbors have samples.""")

        if key not in existing_sample_formats and mapped_sample == key:
            issues.append(f"Key {key}: Mapped to itself despite no sample existing.")

    if issues:
        print("\nPotential Key Mapping Issues:")
        for issue in issues:
            print(f"- {issue}")
    else:
        print("\nKey Mapping Analysis: No obvious issues found.")

if __name__ == "__main__":
    sfz_content = generate_sfz(**config)

    with open("Piano.sfz", "w") as sfz_file:
        sfz_file.write(sfz_content)

    print("SFZ file 'Piano.sfz' generated successfully.")
    print("Script created by AG89 and a bunch of GPTs")

    analyze_key_mapping(generate_sfz.key_to_sample_map, generate_sfz.existing_sample_formats, config['key_range'][0], config['key_range'][1], config['sample_range'][0], config['sample_range'][1])
