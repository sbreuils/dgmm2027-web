import sys
import numpy as np
import pyvista as pv
 
# ── Palette ──────────────────────────────────────────────────────────────────
GRAY_COLOR  = "#757575"   # DG letters
BLUE_COLOR  = "#1565c0"   # MM spheres
BG_COLOR    = "#f0f4ff"   # background
 
# ── M-letter voxel map ───────────────────────────────────────────────────────
# Grid: 7 rows × 7 cols  (row 0 = top)
# Two-wide vertical bars on left (cols 0-1) and right (cols 5-6),
# with converging diagonals meeting at centre (row 3, col 3).
#
#   0 1 2 3 4 5 6
#   X X . . . X X   row 0
#   X X X . X X X   row 1
#   X X . X . X X   row 2
#   X X . . . X X   row 3
#   X X . . . X X   row 4
#   X X . . . X X   row 5
#   X X . . . X X   row 6
#
M_CELLS = set(
    [(r, 0) for r in range(7)] +       # left bar col 0
    [(r, 1) for r in range(7)] +       # left bar col 1
    [(r, 5) for r in range(7)] +       # right bar col 5
    [(r, 6) for r in range(7)] +       # right bar col 6
    [(1, 2), (2, 3)] +                 # left diagonal inner
    [(1, 4), (2, 3)]                   # right diagonal inner
)
 
 
# ── Helpers ───────────────────────────────────────────────────────────────────
 
def make_letter(char: str, target_height: float, depth: float = 0.35) -> pv.PolyData:
    """Extruded 3-D text mesh scaled to *target_height*."""
    mesh = pv.Text3D(char, depth=depth)
    h = mesh.bounds[3] - mesh.bounds[2]
    if h > 1e-6:
        s = target_height / h
        mesh.scale([s, s, 1.0], inplace=True)
    # Centre vertically at y = 0
    cy = (mesh.bounds[2] + mesh.bounds[3]) / 2.0
    mesh.translate([0.0, -cy, 0.0], inplace=True)
    return mesh
 
 
def make_M(x0: float, y0: float,
           radius: float = 0.40) -> list[pv.PolyData]:
    """Return list of sphere meshes forming one M letter.
 
    Parameters
    ----------
    x0, y0 : float
        Position of the top-left sphere centre.
    radius : float
        Sphere radius; neighbouring spheres slightly overlap.
    """
    spacing = radius * 1.72   # ~14 % overlap between adjacent spheres
    spheres = []
    for (row, col) in M_CELLS:
        cx = x0 + col * spacing
        cy = y0 - row * spacing   # rows grow downward
        cz = 0.0
        spheres.append(
            pv.Sphere(radius=radius, center=(cx, cy, cz),
                      theta_resolution=32, phi_resolution=32)
        )
    return spheres
 
 
# ── Scene builder ─────────────────────────────────────────────────────────────
 
def build_scene(off_screen: bool = False) -> pv.Plotter:
    SPHERE_R = 0.40
    SPACING  = SPHERE_R * 1.72
    M_H      = 6 * SPACING    # height of M (rows 0-6 → 6 gaps)
    M_W      = 6 * SPACING    # width  of M (cols 0-6 → 6 gaps)
    GAP      = SPACING * 1.4  # gap between letters
 
    pl = pv.Plotter(off_screen=off_screen, window_size=(1800, 700))
    pl.set_background(BG_COLOR)
 
    # ── D ────────────────────────────────────────────────────────────────────
    D = make_letter("D", target_height=M_H)
    D_w = D.bounds[1] - D.bounds[0]
    pl.add_mesh(D, color=GRAY_COLOR, smooth_shading=True,
                specular=0.5, specular_power=25)
 
    # ── G  (right of D) ──────────────────────────────────────────────────────
    G = make_letter("G", target_height=M_H)
    G.translate([D_w + GAP, 0.0, 0.0], inplace=True)
    G_w = G.bounds[1] - G.bounds[0]
    pl.add_mesh(G, color=GRAY_COLOR, smooth_shading=True,
                specular=0.5, specular_power=25)
 
    # ── M1 ───────────────────────────────────────────────────────────────────
    m1_x0 = D_w + GAP + G_w + GAP * 1.8
    m1_y0 = M_H / 2.0            # top-row y so letter is centred at y=0
 
    for s in make_M(m1_x0, m1_y0, radius=SPHERE_R):
        pl.add_mesh(s, color=BLUE_COLOR, smooth_shading=True,
                    specular=1.0, specular_power=60)
 
    # ── M2  (right of M1) ────────────────────────────────────────────────────
    m2_x0 = m1_x0 + M_W + GAP
 
    for s in make_M(m2_x0, m1_y0, radius=SPHERE_R):
        pl.add_mesh(s, color=BLUE_COLOR, smooth_shading=True,
                    specular=1.0, specular_power=60)
 
    # ── Lighting ──────────────────────────────────────────────────────────────
    total_w = m2_x0 + M_W
    cx = total_w / 2.0
 
    pl.enable_shadows()
    pl.add_light(pv.Light(
        position=(cx + total_w * 0.4, M_H, 20),
        focal_point=(cx, 0, 0),
        intensity=1.1,
        light_type="scene light"
    ))
    pl.add_light(pv.Light(
        position=(cx - total_w * 0.5, M_H * 0.3, 12),
        focal_point=(cx, 0, 0),
        intensity=0.45,
        light_type="scene light"
    ))
    pl.add_light(pv.Light(
        position=(cx, -M_H, 8),
        focal_point=(cx, 0, 0),
        intensity=0.20,
        light_type="scene light"
    ))
 
    # ── Camera: slightly elevated front view ──────────────────────────────────
    dist = max(total_w, M_H) * 1.45
    pl.camera_position = [
        (cx, 0.0, dist),
        (cx, 0.0, 0.0),
        (0.0, 1.0, 0.0),
    ]
 
    return pl
 
 
# ── Entry point ───────────────────────────────────────────────────────────────
 
if __name__ == "__main__":
    save_mode = "--save" in sys.argv
 
    pl = build_scene(off_screen=save_mode)
 
    if save_mode:
        outfile = "dgmm2027_3d.png"
        pl.screenshot(outfile, transparent_background=True)
        print(f"Saved → {outfile}")
    else:
        print("Controls: left-drag = rotate  |  right-drag = zoom  |  Q = quit")
        pl.show(title="DGMM 2027 — 3-D Logo")