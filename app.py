import streamlit as st
import json
import os
import random
import re
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from io import BytesIO
from PIL import Image

# ---------------------------------------------------------------------
#                           PERSISTENCE HELPERS
# ---------------------------------------------------------------------
SAVE_FILE = "saved_configs.json"

def load_saved_configs() -> list[dict]:
    """
    Load previously saved configs from a local JSON file.
    If the file doesn't exist, return an empty list.
    """
    if not os.path.exists(SAVE_FILE):
        return []
    with open(SAVE_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            if isinstance(data, list):
                return data
            else:
                return []
        except json.JSONDecodeError:
            return []

def save_saved_configs(configs: list[dict]):
    """
    Write the list of saved configs to the local JSON file,
    ensuring a lightweight persistence approach.
    """
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(configs, f, indent=4)

# ---------------------------------------------------------------------
#                           HELPER FUNCTIONS
# ---------------------------------------------------------------------

def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert a hex color string (e.g., '#ff00d3') to an RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    """Convert an (R, G, B) tuple to a hex color string '#RRGGBB'."""
    return '#{:02x}{:02x}{:02x}'.format(*rgb)

def derive_start_color(final_color: str, factor: float = 0.57) -> tuple[int, int, int]:
    """
    Darken the user-chosen final color by a factor (<1 => darker).
    """
    final_rgb = hex_to_rgb(final_color)
    start_rgb = tuple(max(0, int(c * factor)) for c in final_rgb)
    return start_rgb

def generate_color_stops(final_color: str, n_stops: int) -> list[tuple[int, int, int]]:
    """
    Generate a list of 'n_stops' colors interpolating between a derived
    darker color (start) and the final color (end).
    """
    start_rgb = derive_start_color(final_color)
    end_rgb = hex_to_rgb(final_color)
    gradient = []
    for i in range(n_stops):
        t = i / (n_stops - 1)
        r = round(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * t)
        g = round(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * t)
        b = round(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * t)
        gradient.append((r, g, b))
    return gradient

def multi_stop_gradient_color_func(word=None, font_size=None,
                                   position=None, orientation=None,
                                   font_path=None, random_state=None) -> str:
    """Return one of the gradient color stops at random."""
    color_stops = st.session_state.get("color_stops", [])
    if not color_stops:
        return "rgb(0, 0, 0)"  # fallback if something goes wrong
    c = random.choice(color_stops)
    return f"rgb({c[0]}, {c[1]}, {c[2]})"

def assign_varied_frequencies(words: list[str]) -> dict[str, int]:
    """
    Mimics original logic:
      - 1 or 2 words get freq ~10
      - 1 word gets freq ~5
      - the rest get freq 1-2
    """
    if not words:
        return {}
    shuffled = words[:]
    random.shuffle(shuffled)
    num_big = random.choice([1, 2])
    big_words = shuffled[:num_big]
    medium_words = shuffled[num_big:num_big+1]
    small_words = shuffled[num_big+1:]

    freqs = {}
    for w in big_words:
        freqs[w] = random.randint(9, 10)
    for w in medium_words:
        freqs[w] = random.randint(5, 6)
    for w in small_words:
        freqs[w] = random.randint(1, 2)
    return freqs

def generate_5_variations(words_list: list[str]) -> list[dict[str, int]]:
    """Return exactly 5 random frequencies dicts for the given words_list."""
    variations = []
    for _ in range(5):
        frequencies = assign_varied_frequencies(words_list)
        variations.append(frequencies)
    return variations

def create_wordcloud_image(frequencies: dict[str, int],
                          width: int,
                          height: int) -> Image.Image:
    """
    Create a WordCloud using the multi_stop_gradient_color_func,
    convert to a Pillow Image at full resolution, and return it.
    """
    wc = WordCloud(
        width=width,
        height=height,
        background_color="white",
        color_func=multi_stop_gradient_color_func,
        prefer_horizontal=0.3,
        margin=10
    ).generate_from_frequencies(frequencies)
    # Convert to PIL Image
    return wc.to_image()

# ---------------------------------------------------------------------
#                          STREAMLIT APP
# ---------------------------------------------------------------------

# 1. Load or Init Session State
#    - Active config, saved configs, and variations
if "active_config" not in st.session_state:
    st.session_state["active_config"] = {
        "final_color": "#ff00d3",
        "n_stops": 5,
        "words": [
            "algún", "ningún", "otro", "todo", "cualquier",
            "cualquiera", "poco", "mucho", "varios", "demasiado",
            "bastante", "cada", "cierto", "ninguno", "alguno",
            "mismo", "semejante", "tantos", "diverso", "suficiente"
        ],
        "width": 2000,
        "height": 1600
    }

if "saved_configs" not in st.session_state:
    st.session_state["saved_configs"] = load_saved_configs()

if "variations" not in st.session_state:
    st.session_state["variations"] = generate_5_variations(
        st.session_state["active_config"]["words"]
    )

# ---------------------------------------------------------------------
# SIDEBAR - Config / Gradient / Saved Configs
# ---------------------------------------------------------------------

st.sidebar.title("Configuration")

# --- Color & Gradient Controls ---
final_color = st.sidebar.color_picker(
    "Pick the final color",
    value=st.session_state["active_config"].get("final_color", "#ff00d3")
)

n_stops = st.sidebar.slider(
    "Number of Color Stops",
    min_value=3,
    max_value=10,
    value=st.session_state["active_config"].get("n_stops", 5)
)

# Immediately generate color stops so we can show the preview
color_stops = generate_color_stops(final_color, n_stops)
st.session_state["color_stops"] = color_stops

# --- Gradient Preview (move it up near color picker) ---
st.sidebar.subheader("Gradient Preview")
gradient_cols = st.sidebar.columns(n_stops)
for idx, rgb_color in enumerate(color_stops):
    hex_color = rgb_to_hex(rgb_color)
    with gradient_cols[idx]:
        st.markdown(
            f"""
            <div style="width:40px; height:20px; background-color:{hex_color}; 
                        border:1px solid #000; border-radius:3px">
            </div>
            """,
            unsafe_allow_html=True
        )

# --- Words ---
words_input = st.sidebar.text_area(
    label="Words (comma, semicolon, or newline separated)",
    value="\n".join(st.session_state["active_config"]["words"]),
    height=200
)

temp_words = re.split(r"[,\n;]+", words_input)
words_list = [w.strip() for w in temp_words if w.strip()]

# --- Dimensions ---
cloud_width = st.sidebar.number_input(
    "WordCloud Width",
    min_value=200,
    max_value=6000,
    value=st.session_state["active_config"].get("width", 2000)
)
cloud_height = st.sidebar.number_input(
    "WordCloud Height",
    min_value=200,
    max_value=6000,
    value=st.session_state["active_config"].get("height", 1600)
)

# Update active config in session
st.session_state["active_config"] = {
    "final_color": final_color,
    "n_stops": n_stops,
    "words": words_list,
    "width": cloud_width,
    "height": cloud_height
}

# --------------------------------
# Manage Saved Configs (Persistence)
# --------------------------------
st.sidebar.header("Saved Configs")

config_name = st.sidebar.text_input("Config Name")

if st.sidebar.button("Save Current Config"):
    if config_name.strip():
        new_saved = {
            "name": config_name.strip(),
            "config": st.session_state["active_config"].copy()
        }
        st.session_state["saved_configs"].append(new_saved)
        save_saved_configs(st.session_state["saved_configs"])
        st.success(f"Config '{config_name}' saved!")
    else:
        st.error("Please enter a valid name.")

if st.session_state["saved_configs"]:
    all_names = [item["name"] for item in st.session_state["saved_configs"]]
    selected_name = st.sidebar.selectbox("Select a saved config to load/delete:", all_names)
    chosen_item = next((it for it in st.session_state["saved_configs"] if it["name"] == selected_name), None)

    if chosen_item:
        if st.sidebar.button("Load Config"):
            st.session_state["active_config"] = chosen_item["config"].copy()
            # Recompute color stops & variations
            st.session_state["color_stops"] = generate_color_stops(
                st.session_state["active_config"]["final_color"],
                st.session_state["active_config"]["n_stops"]
            )
            st.session_state["variations"] = generate_5_variations(
                st.session_state["active_config"]["words"]
            )
            st.success(f"Loaded saved config: '{selected_name}'")

        if st.sidebar.button("Delete Config"):
            st.session_state["saved_configs"] = [
                it for it in st.session_state["saved_configs"] if it["name"] != selected_name
            ]
            save_saved_configs(st.session_state["saved_configs"])
            st.success(f"Deleted saved config: '{selected_name}'")
else:
    st.sidebar.info("No saved configs yet.")

# --------------------------------
# Export/Import the Active Config
# --------------------------------
st.sidebar.subheader("Export/Import Active Config")
config_json = json.dumps(st.session_state["active_config"], indent=4)
st.sidebar.download_button(
    "Export Active Config (JSON)",
    config_json,
    file_name="active_config.json",
    mime="application/json"
)
uploaded_file = st.sidebar.file_uploader("Import Config (JSON)")
if uploaded_file is not None:
    try:
        imported_config = json.load(uploaded_file)
        # Overwrite the active config
        st.session_state["active_config"] = imported_config
        # Update color stops & variations
        st.session_state["color_stops"] = generate_color_stops(
            imported_config["final_color"],
            imported_config["n_stops"]
        )
        st.session_state["variations"] = generate_5_variations(
            imported_config["words"]
        )
        st.success("Config imported successfully!")
    except Exception as e:
        st.error(f"Error importing config: {e}")

# ---------------------------------------------------------------------
# MAIN CONTENT
# ---------------------------------------------------------------------
st.title("Spanish Word Cloud (5 Variations)")

# Check for words
if not words_list:
    st.error("No words provided. Please add at least one word in the sidebar.")
else:
    # Let user regenerate the 5 random variations with a button
    if st.button("Regenerate 5 Variations"):
        st.session_state["variations"] = generate_5_variations(words_list)
        st.success("Five new frequency sets generated!")

    st.write("Below are 5 random frequency variations using the current configuration.")

    # Use columns to display the 5 variations in rows (3 columns wide, so row wrap)
    cols = st.columns(3)
    for i, freqs in enumerate(st.session_state["variations"]):
        col = cols[i % 3]  # pick which column to place it in
        with col:
            variation_num = i + 1
            st.subheader(f"Variation #{variation_num}")

            # Create the high-res wordcloud image only once
            wc_image_fullres = create_wordcloud_image(
                frequencies=freqs,
                width=st.session_state["active_config"]["width"],
                height=st.session_state["active_config"]["height"]
            )

            # Make a smaller preview copy
            preview_image = wc_image_fullres.copy()
            preview_width = 300  # pick a smaller size for on-screen display
            aspect_ratio = (
                st.session_state["active_config"]["height"] /
                st.session_state["active_config"]["width"]
            )
            preview_height = int(preview_width * aspect_ratio)
            preview_image.thumbnail((preview_width, preview_height))

            # Show the preview
            st.image(preview_image)

            # Allow download of the full-res image
            fullres_buffer = BytesIO()
            wc_image_fullres.save(fullres_buffer, format="PNG")
            st.download_button(
                label=f"Download Variation #{variation_num}",
                data=fullres_buffer.getvalue(),
                file_name=f"wordcloud_variation_{variation_num}.png",
                mime="image/png"
            )

# End of script
