import plotly.io as pio

pio.templates["skolverket"] = {
    "layout": {
        "colorway": [
            "#91AFF0",  # Blue
            "#F1C0E1",  # Red
            "#10B981",  # Green
            "#F59E0B",  # Amber
            "#8B5CF6",  # Purple
        ],
        "paper_bgcolor": "white",
        "plot_bgcolor": "white",
        "font": {
            "family": "Inter, Arial, sans-serif",
            "size": 14,
            "color": "#111827",
        },
        "xaxis": {"gridcolor": "#E5E7EB"},
        "yaxis": {"gridcolor": "#E5E7EB"},
    }
}

pio.templates.default = "skolverket"
