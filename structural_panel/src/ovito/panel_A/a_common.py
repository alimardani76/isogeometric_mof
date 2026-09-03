"""Shared OVITO helpers for Panel A Round 1."""

from pathlib import Path
import numpy as np

from a_config import (
    A_PAIRWISE_CUTOFFS, PALETTE, RADII, BOND_WIDTH,
    BOND_COLOR, IMAGE_SIZE, DPI, PAIR_MARGIN
)

def require_ovito():
    try:
        import ovito
        return ovito
    except Exception as exc:
        raise SystemExit(
            "Cannot import OVITO. Activate your ovito_render environment first.\n"
            f"Original error: {exc}"
        )

def normalized(v):
    v = np.asarray(v, dtype=float)
    n = np.linalg.norm(v)
    if n == 0:
        raise ValueError("zero direction")
    return v/n

def lattice_matrix(data):
    return np.asarray(data.cell)[:3,:3]

def direction_from_coeffs(data, coeffs):
    H = lattice_matrix(data)
    a,b,c = H[:,0],H[:,1],H[:,2]
    h,k,l = coeffs
    return normalized(h*a + k*b + l*c)

def make_renderer():
    require_ovito()
    from ovito.vis import TachyonRenderer
    r = TachyonRenderer()
    r.ambient_occlusion = False
    r.shadows = False
    r.antialiasing = True
    r.antialiasing_samples = 4
    return r

def build_pipeline(cif_path, hide_h=True):
    require_ovito()
    from ovito.io import import_file
    from ovito.modifiers import (
        CreateBondsModifier, SelectTypeModifier, DeleteSelectedModifier
    )
    from ovito.vis import BondsVis

    pipe = import_file(str(cif_path))
    upstream = pipe.compute()

    def setup_types(frame, data):
        prop = data.particles_.particle_types_
        for t in prop.types_:
            if t.name in RADII:
                t.radius = float(RADII[t.name])
            if t.name in PALETTE:
                t.color = tuple(PALETTE[t.name])
    pipe.modifiers.append(setup_types)

    if hide_h:
        h_ids = [t.id for t in upstream.particles["Particle Type"].types if t.name == "H"]
        if h_ids:
            pipe.modifiers.append(
                SelectTypeModifier(property="Particle Type", types=set(h_ids))
            )
            pipe.modifiers.append(DeleteSelectedModifier())

    bonds = CreateBondsModifier()
    if not hasattr(CreateBondsModifier.Mode, "Pairwise") or not hasattr(bonds, "set_pairwise_cutoff"):
        raise RuntimeError(
            "Your OVITO build does not expose Pairwise bonding. "
            "Use the same OVITO environment that successfully ran the Panel-B/Panel-D scripts."
        )
    bonds.mode = CreateBondsModifier.Mode.Pairwise
    if hasattr(bonds, "discard_existing_bonds"):
        bonds.discard_existing_bonds = True

    present = {t.name for t in upstream.particles["Particle Type"].types}
    for (a,b), cut in A_PAIRWISE_CUTOFFS.items():
        if a in present and b in present:
            bonds.set_pairwise_cutoff(a,b,float(cut))

    bonds.vis.width = float(BOND_WIDTH)
    try:
        bonds.vis.coloring_mode = BondsVis.ColoringMode.Uniform
    except Exception:
        pass
    bonds.vis.color = tuple(BOND_COLOR)
    pipe.modifiers.append(bonds)

    src = pipe.source.data
    if src.cell is not None:
        src.cell.vis.render_cell = False
    return pipe, upstream

def auto_fov(pipe, direction):
    from ovito.vis import Viewport
    pipe.add_to_scene()
    try:
        vp = Viewport(type=Viewport.Type.Ortho, camera_dir=tuple(direction))
        vp.zoom_all()
        return float(vp.fov)
    finally:
        pipe.remove_from_scene()

def render(pipe, direction, fov, outpath):
    from ovito.vis import Viewport
    outpath = Path(outpath)
    outpath.parent.mkdir(parents=True, exist_ok=True)

    pipe.add_to_scene()
    try:
        vp = Viewport(type=Viewport.Type.Ortho, camera_dir=tuple(direction))
        vp.zoom_all()
        vp.fov = float(fov)
        vp.render_image(
            filename=str(outpath),
            size=IMAGE_SIZE,
            background=(1.0,1.0,1.0),
            renderer=make_renderer()
        )
    finally:
        pipe.remove_from_scene()

    try:
        from PIL import Image
        with Image.open(outpath) as im:
            im.save(outpath, dpi=(DPI, DPI))
    except Exception:
        pass

def render_pair(pipe_i, dir_i, pipe_ii, dir_ii, out_i, out_ii):
    shared = max(auto_fov(pipe_i, dir_i), auto_fov(pipe_ii, dir_ii)) * PAIR_MARGIN
    render(pipe_i, dir_i, shared, out_i)
    render(pipe_ii, dir_ii, shared, out_ii)
    return shared
