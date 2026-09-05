"""OVITO helper functions shared by the screening scripts."""

from pathlib import Path
import math
import numpy as np

from p7b_ovito_config import (
    PALETTE_BASE, PALETTE_SOFT, PALETTE_METAL_HIGH,
    BASE_RADII, IMAGE_SIZE, DPI, PAIR_MARGIN
)

def require_ovito():
    try:
        import ovito
        return ovito
    except Exception as exc:
        raise SystemExit(
            "Cannot import OVITO in this Python environment.\n"
            "Activate your OVITO conda environment first.\n"
            f"Original error: {exc}"
        )

def normalized(v):
    v = np.asarray(v, dtype=float)
    n = np.linalg.norm(v)
    if n == 0:
        raise ValueError("Zero camera vector")
    return v / n

def lattice_matrix_from_data(data):
    if data.cell is None:
        raise RuntimeError("CIF import produced no simulation cell.")
    H = np.asarray(data.cell)[:3, :3]
    return H

def direction_from_coeffs(data, coeffs):
    H = lattice_matrix_from_data(data)
    a, b, c = H[:,0], H[:,1], H[:,2]
    h, k, l = coeffs
    return normalized(h*a + k*b + l*c)

def cell_metrics(data):
    H = lattice_matrix_from_data(data)
    a, b, c = H[:,0], H[:,1], H[:,2]
    def angle(u,v):
        x = np.dot(u,v) / (np.linalg.norm(u)*np.linalg.norm(v))
        return math.degrees(math.acos(float(np.clip(x,-1,1))))
    return {
        "a": float(np.linalg.norm(a)),
        "b": float(np.linalg.norm(b)),
        "c": float(np.linalg.norm(c)),
        "alpha": angle(b,c),
        "beta": angle(a,c),
        "gamma": angle(a,b),
        "volume": float(abs(np.linalg.det(H))),
    }

def particle_type_counts(data):
    ptype = data.particles["Particle Type"]
    ids = np.asarray(ptype)
    id_to_name = {t.id: t.name for t in ptype.types}
    out = {}
    for tid in ids:
        name = id_to_name.get(int(tid), str(int(tid)))
        out[name] = out.get(name, 0) + 1
    return out

def palette_by_name(name):
    # A recipe may pass a palette dictionary directly.
    if isinstance(name, dict):
        return name
    if name == "base":
        return PALETTE_BASE
    if name == "soft":
        return PALETTE_SOFT
    if name == "metal_high":
        return PALETTE_METAL_HIGH
    raise ValueError(name)

def build_pipeline(cif_path, rep=(1,1,1), recipe=None):
    require_ovito()
    from ovito.io import import_file
    from ovito.modifiers import (
        CreateBondsModifier, ReplicateModifier,
        SelectTypeModifier, DeleteSelectedModifier
    )
    from ovito.vis import BondsVis

    if recipe is None:
        recipe = dict(
            h_mode="show", h_radius=0.12, particle_scale=1.0,
            bond_width=0.13, bond_color=(0.58,0.58,0.58),
            bond_coloring="uniform", palette="base",
            show_cell=False, ao=False, bond_mode="covalent"
        )

    pipeline = import_file(str(cif_path))
    upstream = pipeline.compute()

    # VERSION-COMPATIBLE particle styling.
    # Avoid EditTypesModifier.edit_type(), which is unavailable in some
    # OVITO installations. Modify mutable ParticleType descriptors instead.
    palette = palette_by_name(recipe.get("palette","base"))
    h_radius = float(recipe.get("h_radius", BASE_RADII["H"]))

    def setup_particle_types(frame, data):
        type_property = data.particles_.particle_types_
        for t in type_property.types_:
            name = t.name
            radius = BASE_RADII.get(name, getattr(t, "radius", 0.35))
            if name == "H":
                radius = h_radius
            radius = recipe.get("radii", {}).get(name, radius)
            color = palette.get(name, getattr(t, "color", (0.5,0.5,0.5)))
            t.radius = float(radius)
            t.color = tuple(color)

    pipeline.modifiers.append(setup_particle_types)

    # Optional H removal: use numeric type IDs for broader compatibility.
    if recipe.get("h_mode") == "hide":
        h_ids = [t.id for t in upstream.particles["Particle Type"].types if t.name == "H"]
        if h_ids:
            pipeline.modifiers.append(
                SelectTypeModifier(property="Particle Type", types=set(h_ids))
            )
            pipeline.modifiers.append(DeleteSelectedModifier())

    # Bond generation.
    bond_mode = recipe.get("bond_mode", "covalent")
    bonds = CreateBondsModifier()
    if bond_mode == "covalent":
        bonds.mode = CreateBondsModifier.Mode.CovalentRadius
    elif bond_mode == "vdw":
        bonds.mode = CreateBondsModifier.Mode.VdWRadius
        if hasattr(bonds, "prevent_hh_bonds"):
            bonds.prevent_hh_bonds = True
    elif bond_mode == "pairwise":
        # Explicit chemically controlled bonding. Unspecified type pairs
        # remain at cutoff 0 and therefore receive no bond.
        if not hasattr(CreateBondsModifier.Mode, "Pairwise") or not hasattr(bonds, "set_pairwise_cutoff"):
            raise RuntimeError(
                "This OVITO build does not expose Pairwise bond mode / set_pairwise_cutoff(). "
                "Run 00_probe_ovito_api.py and send the output."
            )
        bonds.mode = CreateBondsModifier.Mode.Pairwise
        if hasattr(bonds, "discard_existing_bonds"):
            bonds.discard_existing_bonds = True

        present = {t.name for t in upstream.particles["Particle Type"].types}
        pair_cutoffs = recipe.get("pair_cutoffs", {})
        for (a, b), cutoff in pair_cutoffs.items():
            if a in present and b in present:
                bonds.set_pairwise_cutoff(a, b, float(cutoff))
    else:
        raise ValueError(f"Unsupported bond_mode: {bond_mode}")

    bonds.vis.width = float(recipe.get("bond_width", 0.13))
    if recipe.get("bond_coloring") == "particle":
        try:
            bonds.vis.coloring_mode = BondsVis.ColoringMode.ByParticle
        except Exception:
            try:
                bonds.vis.coloring_mode = BondsVis.ColoringMode.ByParticleType
            except Exception:
                print("[compat] Per-particle bond coloring unsupported; using uniform color.")
                try:
                    bonds.vis.coloring_mode = BondsVis.ColoringMode.Uniform
                except Exception:
                    pass
                bonds.vis.color = tuple(recipe.get("bond_color", (0.58,0.58,0.58)))
    else:
        try:
            bonds.vis.coloring_mode = BondsVis.ColoringMode.Uniform
        except Exception:
            pass
        bonds.vis.color = tuple(recipe.get("bond_color", (0.58,0.58,0.58)))
    pipeline.modifiers.append(bonds)

    # Replicate particles and bonds.
    rx, ry, rz = rep
    pipeline.modifiers.append(
        ReplicateModifier(num_x=rx, num_y=ry, num_z=rz, adjust_box=True)
    )

    # Visualization settings.
    src = pipeline.source.data
    if src.particles is not None:
        src.particles.vis.scaling = float(recipe.get("particle_scale", 1.0))
    if src.cell is not None:
        src.cell.vis.render_cell = bool(recipe.get("show_cell", False))
        if hasattr(src.cell.vis, "rendering_color"):
            src.cell.vis.rendering_color = (0.50,0.50,0.50)

    return pipeline, upstream

def make_renderer(ao=False):
    require_ovito()
    from ovito.vis import TachyonRenderer
    r = TachyonRenderer()
    r.ambient_occlusion = bool(ao)
    if ao:
        r.ambient_occlusion_samples = 8
        r.ambient_occlusion_brightness = 0.85
    r.shadows = False
    r.antialiasing = True
    r.antialiasing_samples = 4
    return r

def auto_fov(pipeline, direction):
    from ovito.vis import Viewport
    pipeline.add_to_scene()
    try:
        vp = Viewport(type=Viewport.Type.Ortho, camera_dir=tuple(direction))
        vp.zoom_all()
        return float(vp.fov)
    finally:
        pipeline.remove_from_scene()

def render_with_fov(pipeline, direction, fov, output_path, ao=False):
    from ovito.vis import Viewport
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    pipeline.add_to_scene()
    try:
        vp = Viewport(type=Viewport.Type.Ortho, camera_dir=tuple(direction))
        # Let OVITO center the structure, then enforce pair-matched orthographic scale.
        vp.zoom_all()
        vp.fov = float(fov)
        vp.render_image(
            filename=str(output_path),
            size=IMAGE_SIZE,
            background=(1.0,1.0,1.0),
            renderer=make_renderer(ao=ao)
        )
    finally:
        pipeline.remove_from_scene()

    stamp_dpi(output_path)

def stamp_dpi(path):
    try:
        from PIL import Image
        p = Path(path)
        with Image.open(p) as im:
            im.save(p, dpi=(DPI,DPI))
    except Exception:
        # Rendering remains valid even if Pillow is absent.
        pass

def render_pair_matched_scale(pipe_i, dir_i, pipe_ii, dir_ii, out_i, out_ii, ao=False):
    fov_i = auto_fov(pipe_i, dir_i)
    fov_ii = auto_fov(pipe_ii, dir_ii)
    shared = max(fov_i, fov_ii) * PAIR_MARGIN
    render_with_fov(pipe_i, dir_i, shared, out_i, ao=ao)
    render_with_fov(pipe_ii, dir_ii, shared, out_ii, ao=ao)
    return shared

def bond_length_rows(data):
    """Returns rows (elementA, elementB, length) for computed bonds."""
    if data.particles is None or data.particles.bonds is None:
        return []

    pos = np.asarray(data.particles.positions)
    ptype = data.particles["Particle Type"]
    type_ids = np.asarray(ptype)
    names = {t.id:t.name for t in ptype.types}
    H = lattice_matrix_from_data(data)

    topology = np.asarray(data.particles.bonds.topology)
    pbc = np.asarray(data.particles.bonds.pbc_vectors)

    rows = []
    for (a,b), shift in zip(topology, pbc):
        v = pos[b] - pos[a] + H @ shift
        length = float(np.linalg.norm(v))
        ea = names.get(int(type_ids[a]), str(int(type_ids[a])))
        eb = names.get(int(type_ids[b]), str(int(type_ids[b])))
        x,y = sorted((ea,eb))
        rows.append((x,y,length))
    return rows
