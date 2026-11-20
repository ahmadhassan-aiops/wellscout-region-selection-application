"""WellScout palette and type: an engineering drawing sheet (drafting grid, navy ink, title blocks)."""

PAPER = "#f3f6f9"
GRID = "#dbe5ef"
GRID_MAJOR = "#c4d3e2"
PANEL = "#ffffff"
INK = "#13294b"        # drawing ink (navy)
MUTED = "#4a5a70"
FAINT = "#7a889b"
LINE = "#b7c4d3"
ACCENT = "#b45309"     # crude amber, for the chosen option and highlights
ACCENT_SOFT = "#fdf3e7"
GAIN = "#25734a"       # profit (always with a + sign or an icon)
LOSS = "#b42318"       # loss (always with a sign or an icon)
REGION = {0: "#2f6db5", 1: "#0f766e", 2: "#6d3fc0"}
REGION_SOFT = {0: "#e8f0fa", 1: "#e3f3f1", 2: "#f0eafb"}
MODEL_NOTE = {"Linear": "straight-line linear regression (the brief)",
              "Linear + squares": "linear regression with squared and cross terms",
              "LightGBM": "gradient-boosted trees (beyond the brief)"}

HEAD = "'IBM Plex Sans Condensed', 'Arial Narrow', sans-serif"
BODY = "'IBM Plex Sans', 'Segoe UI', sans-serif"
MONO = "'IBM Plex Mono', Consolas, monospace"
CHART_FONT = "Segoe UI, Arial, sans-serif"
