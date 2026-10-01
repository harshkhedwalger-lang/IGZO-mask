import matplotlib.pyplot as plt
import matplotlib.patches as patches

# ==============================
# CONFIGURATION (EDIT HERE)
# ==============================
FIG_WIDTH = 10
FIG_HEIGHT = 4

COLORS = {
    "substrate": "#7FA6A6",
    "metal": "#666666",
    "oxide": "#3F5FBF",
    "igzo": "#F2B632"
}

FONT_SIZE = 11


# ==============================
# DRAWING FUNCTION
# ==============================
def draw_layer(ax, x, y, width, height, color, label,
               text_color="white", fontsize=FONT_SIZE):
    """Draws a rectangular layer with centered label"""
    rect = patches.Rectangle(
        (x, y), width, height,
        linewidth=1.2,
        edgecolor='black',
        facecolor=color
    )
    ax.add_patch(rect)

    ax.text(
        x + width / 2,
        y + height / 2,
        label,
        ha='center',
        va='center',
        fontsize=fontsize,
        color=text_color,
        weight='bold'
    )


# ==============================
# DEVICE GENERATOR
# ==============================
def generate_igzo_device(filename="IGZO_device"):
    fig, ax = plt.subplots(figsize=(FIG_WIDTH, FIG_HEIGHT))

    # --------------------------
    # LAYER POSITIONS
    # --------------------------
    y = 0

    # Substrate
    draw_layer(ax, 0, y, 10, 1.0, COLORS["substrate"],
               "Si / SiO$_2$ substrate")
    y += 1.0

    # Bottom Gate (Pt)
    draw_layer(ax, 3, y, 4, 0.6, COLORS["metal"], "Pt")
    y += 0.6

    # Al2O3 dielectric
    draw_layer(ax, 1, y, 8, 1.0, COLORS["oxide"], "Al$_2$O$_3$")
    y += 1.0

    # IGZO layer
    draw_layer(ax, 2, y, 6, 0.8, COLORS["igzo"], "IGZO")
    y += 0.8

    # Source / Drain contacts
    draw_layer(ax, 2, y, 1.5, 1.0, COLORS["metal"], "Pt")
    draw_layer(ax, 6.5, y, 1.5, 1.0, COLORS["metal"], "Pt")

    # --------------------------
    # FORMATTING
    # --------------------------
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis('off')

    # --------------------------
    # EXPORT (HIGH QUALITY)
    # --------------------------
    plt.savefig(f"{filename}.svg", bbox_inches='tight')
    plt.savefig(f"{filename}.pdf", bbox_inches='tight')
    plt.savefig(f"{filename}.png", dpi=600, bbox_inches='tight')

    plt.close()
    print(f"Saved: {filename}.svg / .pdf / .png")


# ==============================
# RUN
# ==============================
if __name__ == "__main__":
    generate_igzo_device("IGZO_cross_section")