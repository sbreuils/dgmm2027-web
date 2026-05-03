#!/usr/bin/env python3
"""
dgmm2027_logo_3d.py  —  3-D logo render for DGMM 2027
=====================================================
Requires:
    pip install pyvista[all]

DG  → extruded 3-D letters whose surface triangulation is visible
      (discrete geometry theme: flat-shaded faces + mesh edges)
MM  → overlapping blue spheres (mathematical morphology structuring elements)

Usage
-----
    python dgmm2027_logo_3d.py            # surface triangles (default)
    python dgmm2027_logo_3d.py --tet      # filled tetrahedra (interior visible)
    python dgmm2027_logo_3d.py --save     # save dgmm2027_3d.png (off-screen)
"""

import sys
import numpy as np
import pyvista as pv

# ── Palette ──────────────────────────────────────────────────────────────────
# NOTE: do not merge/normalise these — each serves a distinct visual role.
DG_FACE   = "#4b4b4b7d"   # DG letter faces  (steel-blue grey)
DG_EDGE   = "#eceff1"   # DG mesh edges    (near-white, high contrast on dark face)
MM_SPHERE = DG_FACE#"#546e7a"   # MM structuring-element spheres (DGMM blue)
BG_COLOR  = "#eef2ff"   # scene background (soft blue-white)

# ── M-letter geometry ────────────────────────────────────────────────────────
# Bars are placed on an integer grid; diagonals are sampled continuously
# along the actual line so the resolution matches the sphere spacing.
#
# Layout (unit = sphere spacing SP):
#
#   col:  0  1  2  3  4  5  6
#   row 0: ██  ·  ·  ·  ·  ██
#   row 1: ██  ○  ·  ·  ○  ██   ← diagonal starts here (continuous)
#   row 2: ██  ·  ○  ·  ○  ██
#   row 3: ██  ·  ·  ●  ·  ██   ← V-point (diagonals meet at col 3.5)
#   row 4: ██  ·  ·  ·  ·  ██
#   row 5: ██  ·  ·  ·  ·  ██
#   row 6: ██  ·  ·  ·  ·  ██


# ── Letter helpers ────────────────────────────────────────────────────────────

def make_letter_surface(char: str, target_height: float,
                        depth: float = 0.45) -> pv.PolyData:
    """
    Extruded 3-D text mesh scaled so its cap height == *target_height*.
    A slightly larger depth (0.45) gives the front face more room and produces
    larger, more readable triangles on the extruded sides.
    """
    mesh = pv.Text3D(char, depth=depth)
    h = mesh.bounds[3] - mesh.bounds[2]
    if h > 1e-6:
        s = target_height / h
        mesh.scale([s, s, 1.0], inplace=True)
    # Centre the letter vertically at y = 0
    cy = (mesh.bounds[2] + mesh.bounds[3]) / 2.0
    mesh.translate([0.0, -cy, 0.0], inplace=True)
    return mesh


def make_letter_tet(char: str, target_height: float,
                    depth: float = 0.45,
                    shrink: float = 0.78) -> pv.UnstructuredGrid:
    """
    Fill the letter interior with tetrahedra, then shrink each cell so the
    gaps between tetrahedra are visible (discrete-geometry cross-section look).
    Use this with --tet; note the letter outline is less distinct.
    """
    surf = make_letter_surface(char, target_height, depth)
    tet  = surf.delaunay_3d(offset=2.5)
    return tet.shrink(shrink)


# ── M-letter spheres ──────────────────────────────────────────────────────────

def _sample_line(x0, y0, x1, y1, sp, include_start=True):
    """Sample sphere centres every *sp* along the segment (x0,y0)→(x1,y1).

    include_start=True  → includes the start point (i=0), so the diagonal
                          sphere sits directly adjacent to the bar sphere and
                          the two look visually connected.
    include_start=False → excludes i=0 (legacy; leaves a gap at the bar edge).
    """
    dx, dy = x1 - x0, y1 - y0
    n = max(1, round(np.hypot(dx, dy) / sp))
    start = 0 if include_start else 1
    return [(x0 + i / n * dx, y0 + i / n * dy) for i in range(start, n + 1)]


def make_M_spheres(x0: float, y0: float,
                   radius: float = 0.20) -> list[pv.PolyData]:
    """
    Sphere centres for one M letter.

    Layout — 4 gaps wide (cols 0-4, single-width bars):

      col:  0    1    2    3    4
      row 0:  ●    ●              ●    ●      ← two peaks (gap at centre)
      row 1:  ●         ●    ●         ●      ← diagonals step inward
      row 2:  ●              ●              ●      ← diagonals close in
      row 3:  ●         V-point        ●      ← V-point
      row 4+: ●                        ●      ← bars only

    Single-width bars leave the diagonal clearly visible.
    Diagonal start points (col=1 / col=3 at row 0) are adjacent to the bars
    so the joint looks solid; include_start=True ensures those spheres exist.
    The gap between col 1 and col 3 at row 0 creates the two M peaks.
    """
    sp     = radius * 1.72
    n_rows = 7
    v_col  = 2.0   # V-point at exact centre of a 4-gap letter (cols 0-4)
    v_row  = 3

    centers: list[tuple[float, float]] = []

    # ── Single-width vertical bars ───────────────────────────────────────────
    for r in range(n_rows):
        centers.append((x0,          y0 - r * sp))   # left  bar, col 0
        centers.append((x0 + 4 * sp, y0 - r * sp))   # right bar, col 4

    # ── Diagonals (continuous, start point included) ─────────────────────────
    vx = x0 + v_col * sp
    vy = y0 - v_row * sp

    # Left diagonal:  (col=1, row=0)  →  V-point (col=2, row=3)
    centers += _sample_line(x0 + 1 * sp, y0, vx, vy, sp, include_start=True)

    # Right diagonal: (col=3, row=0)  →  V-point (col=2, row=3)
    centers += _sample_line(x0 + 3 * sp, y0, vx, vy, sp, include_start=True)

    # ── Deduplicate nearby centres ───────────────────────────────────────────
    seen:   set[tuple[int, int]]      = set()
    unique: list[tuple[float, float]] = []
    tol = sp * 0.5
    for cx, cy in centers:
        key = (round(cx / tol), round(cy / tol))
        if key not in seen:
            seen.add(key)
            unique.append((cx, cy))

    return [
        pv.Sphere(radius=radius, center=(cx, cy, 0.0),
                  theta_resolution=32, phi_resolution=32)
        for cx, cy in unique
    ]


# ── Scene ─────────────────────────────────────────────────────────────────────

def build_scene(off_screen: bool = False,
                tet_mode:   bool = False) -> pv.Plotter:
    SPHERE_R = 0.20
    SP       = SPHERE_R * 1.72   # sphere grid spacing
    M_H      = 8 * SP            # letter height (used to scale DG)
    M_W      = 4 * SP            # letter width: single-width bars at col 0 and col 4
    GAP      = SP * 1.0          # inter-letter gap

    pl = pv.Plotter(off_screen=off_screen, window_size=(1800, 700))
    pl.set_background(BG_COLOR)

    # ── helper: add one DG letter ─────────────────────────────────────────────
    def add_letter(char, x_shift):
        if tet_mode:
            mesh = make_letter_tet(char, target_height=M_H)
        else:
            mesh = make_letter_surface(char, target_height=M_H)
        mesh.translate([x_shift, 0.0, 0.0], inplace=True)
        pl.add_mesh(mesh,
                    color         = DG_FACE,
                    edge_color    = DG_EDGE,
                    show_edges    = True,
                    smooth_shading= False,   # flat shading: each face distinct shade
                    ambient       = 0.40,
                    diffuse       = 0.70,
                    specular      = 0.25,
                    specular_power= 15)
        return mesh

    # ── D ─────────────────────────────────────────────────────────────────────
    D   = add_letter("D", 0.0)
    D_w = D.bounds[1] - D.bounds[0]

    # ── G  (right of D) ───────────────────────────────────────────────────────
    G   = add_letter("G", D_w + GAP)
    G_w = G.bounds[1] - G.bounds[0]


    M   = add_letter("M", D_w + GAP + G_w+ GAP)
    M1_w = M.bounds[1] - M.bounds[0]

    M2   = add_letter("M", D_w + GAP + G_w + GAP + M1_w + GAP)
    M2_w  = M2.bounds[1] - M2.bounds[0]
    right = M2.bounds[1]           # right edge of last M

    # ── 2027  (same baseline as DGMM, slightly smaller) ──────────────────────
    Y2027 = make_letter_surface("2027", target_height=M_H, depth=0.38)
    # Zero the x origin first (Text3D may have internal leading offset)
    Y2027.translate([-Y2027.bounds[0], 0.0, 0.0], inplace=True)
    Y2027.translate([right + GAP * 2.0, 0.0, 0.0], inplace=True)
    pl.add_mesh(Y2027, color=DG_FACE, edge_color=DG_EDGE,
                show_edges=False, smooth_shading=False,
                ambient=0.40, diffuse=0.70, specular=0.25, specular_power=15)

    # ── GRENOBLE subtitle (centred below full DGMM2027 row) ───────────────────
    sub_h   = M_H * 0.30            # subtitle letter height
    grn = make_letter_surface("GRENOBLE", target_height=sub_h, depth=0.34)
    grn_w   = grn.bounds[1] - grn.bounds[0]
    title_cx = (D.bounds[0] + Y2027.bounds[1]) / 2   # centre of full top row
    grn_cx   = grn_w / 2
    gap_y    = GAP * 0.6
    grn.translate([title_cx - grn_cx + 12*GAP,
                   -M_H / 2 - gap_y - sub_h / 2,
                   0.0], inplace=True)
    pl.add_mesh(grn, color=DG_FACE, edge_color=DG_EDGE,
                show_edges=False, smooth_shading=False,
                ambient=0.45, diffuse=0.65, specular=0.20, specular_power=12)

    # ── MM spheres (currently disabled) ──────────────────────────────────────
    # Small separator between G and M1
    # m1_x = D_w + GAP + G_w + SP * 0.4
    # m1_y = (M_H / 2.0) -0.1          # y of top row so letter is centred at y=0

    # for s in make_M_spheres(m1_x, m1_y, radius=SPHERE_R):
    #     pl.add_mesh(s, color=MM_SPHERE, smooth_shading=True,
    #                 ambient=0.35, diffuse=0.65, specular=0.90, specular_power=55)

    # m2_x = m1_x + M_W + GAP
    # for s in make_M_spheres(m2_x, m1_y, radius=SPHERE_R):
    #     pl.add_mesh(s, color=MM_SPHERE, smooth_shading=True,
    #                 ambient=0.35, diffuse=0.65, specular=0.90, specular_power=55)

    # ── Camera & lighting (computed after all meshes so bounds are known) ──────
    pl.reset_camera()          # sets bounds; camera position will be overridden below
    b  = pl.bounds             # (xmin, xmax, ymin, ymax, zmin, zmax)
    cx = (b[0] + b[1]) / 2
    cy = (b[2] + b[3]) / 2
    sw = b[1] - b[0]           # scene width
    sh = b[3] - b[2]           # scene height

    # Front view: camera on +Z axis, tilted ~20° downward so the extruded
    # top edges and mesh triangles are visible without losing legibility.
    dist = max(sw, sh) * 2.2
    pl.camera_position = [
        (cx,  cy + sh * 0.18,  dist),   # slightly above centre
        (cx,  cy,               0.0),   # look at scene centre
        (0,   1,                0.0),   # up = +Y
    ]

    # Key light from top-front-right; fill from top-front-left
    pl.add_light(pv.Light(
        position=(cx + sw * 0.6,  cy + sh,       dist * 0.7),
        focal_point=(cx, cy, 0),
        intensity=1.1, light_type="scene light"))
    pl.add_light(pv.Light(
        position=(cx - sw * 0.4,  cy + sh * 0.4, dist * 0.5),
        focal_point=(cx, cy, 0),
        intensity=0.50, light_type="scene light"))

    return pl


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    save_mode = "--save" in sys.argv
    tet_mode  = "--tet"  in sys.argv

    print("Mode:", "tetrahedra (--tet)" if tet_mode else
          "surface triangles (default) — add --tet for interior tetrahedra")

    pl = build_scene(off_screen=save_mode, tet_mode=tet_mode)

    if save_mode:
        pl.screenshot("dgmm2027_3d.png", transparent_background=True)
        print("Saved → dgmm2027_3d.png")
    else:
        print("Controls: left-drag = rotate  |  right-drag = zoom  |  Q = quit")
        pl.show(title="DGMM 2027 — 3-D Logo")
