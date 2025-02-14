import streamlit as st
import json
import random
import re
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from io import BytesIO

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
    Factor < 1.0 yields a darker version of the final_color.
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

# ---------------------------------------------------------------------
#                    WORD CLOUD GENERATION FUNCTIONS
# ---------------------------------------------------------------------

def multi_stop_gradient_color_func(word=None, font_size=None, position=None,
                                   orientation=None, font_path=None, random_state=None) -> str:
    """
    Returns one of the generated color stops at random, stored in session_state.
    """
    color_stops = st.session_state.get("color_stops", [])
    if not color_stops:
        return "rgb(0, 0, 0)"  # fallback if something goes wrong
    c = random.choice(color_stops)
    return f"rgb({c[0]}, {c[1]}, {c[2]})"

def assign_varied_frequencies(words: list[str]) -> dict[str, int]:
    """
    Mimics your original logic:
      - 1 or 2 words get freq ~10
      - 1 word gets freq ~5
      - the rest get freq 1-2
    """
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

def create_wordcloud(
    frequencies: dict[str, int],
    width: int = 2000,
    height: int = 1600
) -> WordCloud:
    """
    Creates a WordCloud using multi_stop_gradient_color_func for coloring,
    with user-defined width and height.
    """
    wc = WordCloud(
        width=width,
        height=height,
        background_color="white",
        color_func=multi_stop_gradient_color_func,
        prefer_horizontal=0.3,
        margin=10
    ).generate_from_frequencies(frequencies)
    return wc

# ---------------------------------------------------------------------
#                          STREAMLIT APP
# ---------------------------------------------------------------------

# 1. Default configuration
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

# 2. Initialize session state
if "config" not in st.session_state:
    st.session_state["config"] = default_config.copy()

# We also track stored runs as a list of dicts: {"name": str, "config": {...}}
if "runs" not in st.session_state:
    st.session_state["runs"] = []

# -----------------------------------------------
# SIDEBAR - Customize Current Run (TOP PRIORITY)
# -----------------------------------------------
st.sidebar.header("Customize Current Run")

# 1) Final color + color stops
final_color = st.sidebar.color_picker(
    "Pick the final color",
    value=st.session_state["config"].get("final_color", "#ff00d3")
)

n_stops = st.sidebar.slider(
    "Number of Color Stops", min_value=3, max_value=10,
    value=st.session_state["config"].get("n_stops", 5)
)

# 2) Words - CSV, semicolon, or newline
words_input = st.sidebar.text_area(
    label="Words (comma, semicolon, or newline separated)",
    value="\n".join(st.session_state["config"].get("words", default_config["words"])),
    height=300
)
# Split on commas, semicolons, or newlines
temp_words = re.split(r"[,\n;]+", words_input)
words_list = [w.strip() for w in temp_words if w.strip()]

# 3) Dimensions
cloud_width = st.sidebar.number_input(
    "WordCloud Width",
    min_value=200, max_value=6000,
    value=st.session_state["config"].get("width", 2000)
)

cloud_height = st.sidebar.number_input(
    "WordCloud Height",
    min_value=200, max_value=6000,
    value=st.session_state["config"].get("height", 1600)
)

# Update session config
st.session_state["config"]["final_color"] = final_color
st.session_state["config"]["n_stops"] = n_stops
st.session_state["config"]["words"] = words_list
st.session_state["config"]["width"] = cloud_width
st.session_state["config"]["height"] = cloud_height

# Generate the color stops from final_color
st.session_state["color_stops"] = generate_color_stops(final_color, n_stops)

# -----------------------------------------------
# SIDEBAR - Manage Stored Runs (Below)
# -----------------------------------------------
st.sidebar.header("Manage Stored Runs")

# Provide a text input for run name
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
            st.success(f"Run '{selected_run_name}' loaded!")

        # Button to delete selected run
        if st.sidebar.button("Delete Run"):
            st.session_state["runs"] = [r for r in st.session_state["runs"] if r["name"] != selected_run_name]
            st.success(f"Run '{selected_run_name}' deleted!")
else:
    st.sidebar.info("No runs saved yet.")

# -----------------------------------------------
# SIDEBAR - Export Current Config
# -----------------------------------------------
config_json = json.dumps(st.session_state["config"], indent=4)
st.sidebar.download_button(
    "Export Current Config (JSON)",
    config_json,
    file_name="config.json",
    mime="application/json"
)

# -----------------------------------------------
# MAIN CONTENT: Display 5 Variations + Download
# -----------------------------------------------
st.title("Spanish Word Cloud - 5 Variations")
st.write("Below are 5 random frequency variations using the current configuration.")

if not words_list:
    st.error("You have no words. Please add at least one word.")
else:
    # Generate and display 5 variations in a vertical layout
    for i in range(1, 6):
        frequencies = assign_varied_frequencies(words_list)
        wc = create_wordcloud(
            frequencies,
            width=st.session_state["config"]["width"],
            height=st.session_state["config"]["height"]
        )
        
        # Convert WordCloud to a BytesIO for on-screen preview
        preview_buffer = BytesIO()
        fig, ax = plt.subplots(figsize=(8, 6))  # Display size in the UI
        ax.imshow(wc, interpolation='bilinear')
        ax.axis("off")
        fig.savefig(preview_buffer, format="png", dpi=100, bbox_inches="tight")
        plt.close(fig)

        st.subheader(f"Variation #{i}")
        st.image(preview_buffer.getvalue(), use_container_width=True)

        # Full-resolution output
        fullres_buffer = BytesIO()
        wc_fig, wc_ax = plt.subplots(
            figsize=(st.session_state["config"]["width"] / 100,
                     st.session_state["config"]["height"] / 100)
        )
        wc_ax.imshow(wc, interpolation='bilinear')
        wc_ax.axis("off")
        wc_fig.savefig(fullres_buffer, format="png", dpi=100, bbox_inches='tight')
        plt.close(wc_fig)

        st.download_button(
            label=f"Download Variation #{i} (Full Resolution)",
            data=fullres_buffer.getvalue(),
            file_name=f"wordcloud_variation_{i}.png",
            mime="image/png"
        )

# For debugging/curiosity: show color stops in RGB/Hex
# st.write("**Color Stops (RGB)**:", st.session_state["color_stops"])
# st.write("**Color Stops (Hex)**:", [rgb_to_hex(c) for c in st.session_state["color_stops"]])
