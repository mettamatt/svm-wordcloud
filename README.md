# Spanish Word Cloud Generator

This repository contains a **Streamlit** application that generates Spanish word clouds with custom colors, frequencies, and dimensions. Users can:

- Customize word lists (CSV, semicolon, or newline separated).
- Select a color gradient by choosing one final color, with the initial color automatically derived by darkening the final color.
- Adjust the number of gradient stops and the WordCloud dimensions.
- Preview **five random variations** of the WordCloud.
- **Download** each variation at **full resolution**.
- **Store** and **manage** named runs (configurations) for easy reuse.

## Features

- **Live Preview of 5 Variations**: Each run randomizes word frequencies so you can see different possible layouts.
- **Color Gradient**: Automatically derives a darker shade from your chosen final color to create a smooth gradient.
- **Flexible Word List**: Paste words separated by commas, semicolons, or line breaks.
- **WordCloud Dimensions**: Control the pixel size (width x height) of the generated images.
- **Stored Runs**: Save custom runs with a chosen name, load them later, or delete them when no longer needed.
- **Export Config**: Download a JSON config of your current settings.

---

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/mettamatt/svm-wordcloud.git
   cd your-repo-name
   ```
2. **Install dependencies** (Python 3.8+ recommended):
   ```bash
   pip install streamlit wordcloud matplotlib
   ```
   *Alternatively, create a virtual environment and install inside it*:
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Linux/Mac
   # or venv\Scripts\activate on Windows

   pip install streamlit wordcloud matplotlib
   ```

---

## Usage

1. **Run the Streamlit app**:
   ```bash
   streamlit run app.py
   ```
2. **Open your browser** to the URL provided (usually [http://localhost:8501](http://localhost:8501)).

---

## Configuration & Runs

1. **Customize Current Run** (sidebar, top):
   - Pick a **final color**.
   - Select the **number of color stops** to create a gradient.
   - Paste your **words** (separated by commas, semicolons, or line breaks).
   - Set **WordCloud width and height**.

2. **Manage Stored Runs** (sidebar, below customization):
   - **Run Name**: Enter a name for your current configuration.
   - **Save Current as Run**: Stores the current settings under that name.
   - **Select a run** from the dropdown to **load** or **delete**.

3. **Export Current Config**: Download your current config as `config.json`.

---

## Preview & Download

1. On the main page, you’ll see **five random variations** of your WordCloud.
2. Each variation can be **downloaded** as a **PNG** with full resolution (the width and height you selected in the sidebar).
