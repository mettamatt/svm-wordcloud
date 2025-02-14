import streamlit as st
import json
import random
import re
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from io import BytesIO
from PIL import Image

# ---------------------------------------------------------------------
#                           HELPER FUNCTIONS
# ---------------------------------------------------------------------

def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """
    Convert a hex color string (e.g., '#ff00d3') to an RGB tuple.
    """
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    """
    Convert an (R, G, B) tuple to a hex color string '#RRGGBB'.
    """
    return '#{:02x}{:02x}{:02x}'.format(*rgb)

def derive_start_color(final_color: str, factor: float = 0.57) -> tuple[int, int, int]:
    """
    Derive a starting color by darkening the user-chosen final color.
    Factor < 1.0 yields a darker version of final_color.
    """
    final_rgb = hex_to_rgb(final_color)
    start_rgb = tuple(max(0, int(c * factor)) for c in final_rgb)
    return start_rgb

def generate_color_stops(final_color: str, n_stops: int = 5) -> list[tuple[int, int, int]]:
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
    """
    Return one of the gradient color stops at random.
    """
    color_stops = st.session_state.get("color_stops", [])
    if not color_stops:
        return "rgb(0, 0, 0)"  # fallback if something goes wrong
    c = random.choice(color_stops)
    return f"rgb({c[0]}, {c[1]}, {c[2]})"

def assign_varied_frequencies(words: list[str]) -> dict[str, int]:
    """
    Mimics original logic:
      - 1 or 2 words get freq ~10,
      - 1 word gets freq ~5,
      - the rest get freq 1-2.
    """
    if not words:
        return {}

    shuffled = words[:]
    random.shuffle(shuffled)
    num_big = random.choice([1, 2])  # choose 1 or 2 big words
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
    """
    Return a list of 5 random frequencies dicts for the given words_list.
    """
    variations = []
    for _ in range(5):
        frequencies = assign_varied_frequencies(words_list)
        variations.append(frequencies)
    return variations

def create_wordcloud_image(frequencies: dict[str, int],
                          width: int,
                          height: int) -> Image.Image:
    """
    Create a WordCloud (using the color_func from session_state),
    convert it to a Pillow Image at full resolution, and return it.
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
    wc_image = wc.to_image()
    return wc_image

# ---------------------------------------------------------------------
#                          STREAMLIT APP
# ---------------------------------------------------------------------

# --- 1. Default configuration ---
default_config = {
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

# --- 2. Initialize session state ---
if "config" not in st.session_state:
    st.session_state["config"] = default_config.copy()

# We track stored runs as a list of dicts: {"name": str, "config": {...}}
if "runs" not in st.session_state:
    st.session_state["runs"] = []

# We keep five random variations in session_state
if "variations" not in st.session_state:
    st.session_state["variations"] = generate_5_variations(
        st.session_state["config"]["words"]
    )

# -----------------------------------------------
# SIDEBAR - Customize Current Run
# -----------------------------------------------
st.sidebar.header("Customize Current Run")

# 1) Final color + color stops
final_color = st.sidebar.color_picker(
    "Pick the final color",
    value=st.session_state["config"].get("final_color", "#ff00d3")
)

n_stops = st.sidebar.slider(
    "Number of Color Stops",
    min_value=3,
    max_value=10,
    value=st.session_state["config"].get("n_stops", 5)
)

# 2) Words - CSV, semicolon, or newline
words_input = st.sidebar.text_area(
    label="Words (comma, semicolon, or newline separated)",
    value="\n".join(st.session_state["config"].get("words", default_config["words"])),
    height=300
)
temp_words = re.split(r"[,\n;]+", words_input)
words_list = [w.strip() for w in temp_words if w.strip()]

# 3) Dimensions
cloud_width = st.sidebar.number_input(
    "WordCloud Width",
    min_value=200,
    max_value=6000,
    value=st.session_state["config"].get("width", 2000)
)

cloud_height = st.sidebar.number_input(
    "WordCloud Height",
    min_value=200,
    max_value=6000,
    value=st.session_state["config"].get("height", 1600)
)

# --- Update session config ---
st.session_state["config"]["final_color"] = final_color
st.session_state["config"]["n_stops"] = n_stops
st.session_state["config"]["words"] = words_list
st.session_state["config"]["width"] = cloud_width
st.session_state["config"]["height"] = cloud_height

# --- Generate color stops and store them ---
st.session_state["color_stops"] = generate_color_stops(final_color, n_stops)

# --- Show a gradient preview in the sidebar ---
st.sidebar.subheader("Gradient Preview")
col_preview = st.sidebar.columns(n_stops)
for idx, rgb_color in enumerate(st.session_state["color_stops"]):
    # Each color gets a small colored square
    hex_color = rgb_to_hex(rgb_color)
    with col_preview[idx]:
        st.markdown(
            f"""
            <div style="width:60px; height:30px; background-color:{hex_color}; 
                        border:1px solid #000; border-radius:5px">
            </div>
            """,
            unsafe_allow_html=True
        )

# -----------------------------------------------
# SIDEBAR - Manage Stored Runs
# -----------------------------------------------
st.sidebar.header("Manage Stored Runs")
run_name = st.sidebar.text_input("Run Name")

# Button to save current config as a run
if st.sidebar.button("Save Current as Run"):
    if run_name.strip():
        new_run = {
            "name": run_name.strip(),
            "config": st.session_state["config"].copy()
        }
        st.session_state["runs"].append(new_run)
        st.success(f"Run '{run_name}' saved!")
    else:
        st.error("Please enter a valid run name.")

# If runs exist, allow loading/deleting them
if st.session_state["runs"]:
    run_names = [r["name"] for r in st.session_state["runs"]]
    selected_run_name = st.sidebar.selectbox("Select a run to load or delete:", run_names)
    selected_run = next((r for r in st.session_state["runs"] if r["name"] == selected_run_name), None)

    if selected_run:
        # Button to load selected run
        if st.sidebar.button("Load Run"):
            st.session_state["config"] = selected_run["config"].copy()
            st.session_state["color_stops"] = generate_color_stops(
                st.session_state["config"]["final_color"],
                st.session_state["config"]["n_stops"]
            )
            st.session_state["variations"] = generate_5_variations(
                st.session_state["config"]["words"]
            )
            st.success(f"Run '{selected_run_name}' loaded!")

        # Button to delete selected run
        if st.sidebar.button("Delete Run"):
            st.session_state["runs"] = [
                r for r in st.session_state["runs"]
                if r["name"] != selected_run_name
            ]
            st.success(f"Run '{selected_run_name}' deleted!")
else:
    st.sidebar.info("No runs saved yet.")

# -----------------------------------------------
# SIDEBAR - Export/Import Current Config
# -----------------------------------------------
st.sidebar.subheader("Export/Import Config")
config_json = json.dumps(st.session_state["config"], indent=4)
st.sidebar.download_button(
    "Export Current Config (JSON)",
    config_json,
    file_name="config.json",
    mime="application/json"
)

uploaded_file = st.sidebar.file_uploader("Import Config (JSON)")
if uploaded_file is not None:
    try:
        imported_config = json.load(uploaded_file)
        # Overwrite the current config with the imported config
        st.session_state["config"] = imported_config
        # Re-generate color stops & variations
        st.session_state["color_stops"] = generate_color_stops(
            st.session_state["config"]["final_color"],
            st.session_state["config"]["n_stops"]
        )
        st.session_state["variations"] = generate_5_variations(
            st.session_state["config"]["words"]
        )
        st.success("Config imported successfully!")
    except Exception as e:
        st.error(f"Error importing config: {e}")

# -----------------------------------------------
# MAIN CONTENT
# -----------------------------------------------
st.title("Spanish Word Cloud (5 Variations)")

if not words_list:
    st.error("You have no words. Please add at least one word.")
else:
    # Button to regenerate the 5 random variations
    if st.button("Regenerate 5 Variations"):
        st.session_state["variations"] = generate_5_variations(words_list)
        st.success("Five new frequency sets generated!")

    st.write("Below are 5 random frequency variations using the current configuration.")

    # Use columns to display the 5 variations
    cols = st.columns(3)  # We'll use 3 columns and wrap the 5 items

    for i, frequencies in enumerate(st.session_state["variations"]):
        col = cols[i % 3]  # pick which column to place the variation in
        with col:
            variation_num = i + 1
            st.subheader(f"Variation #{variation_num}")

            # Create the high-res wordcloud image only once
            wc_image_fullres = create_wordcloud_image(
                frequencies=frequencies,
                width=st.session_state["config"]["width"],
                height=st.session_state["config"]["height"]
            )

            # Make a smaller preview copy
            preview_image = wc_image_fullres.copy()
            preview_width = 400  # pick a smaller size for on-screen display
            aspect_ratio = st.session_state["config"]["height"] / st.session_state["config"]["width"]
            preview_height = int(preview_width * aspect_ratio)
            preview_image.thumbnail((preview_width, preview_height))

            # Show the preview
            st.image(preview_image)

            # Allow download of the full-res image
            fullres_buffer = BytesIO()
            wc_image_fullres.save(fullres_buffer, format="PNG")
            st.download_button(
                label=f"Download Variation #{variation_num} (Full Resolution)",
                data=fullres_buffer.getvalue(),
                file_name=f"wordcloud_variation_{variation_num}.png",
                mime="image/png"
            )
