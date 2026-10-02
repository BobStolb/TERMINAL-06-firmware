# KiCad 3D library models used by the TS06 boards

These 29 STEP files are copies of models from KiCad's official 3D library (kicad-packages3D), kept here
because **the `kicad/kicad:10.0` Docker image ships no 3D library at all** (no `*.3dshapes` directory, and
`KICAD10_3DMODEL_DIR` is unset in it), so every `${KICAD10_3DMODEL_DIR}/...` model path in the boards points
at nothing unless a library is mounted. `tools/render_populated.py` mounts this folder as
`KICAD10_3DMODEL_DIR`; the layout (`<Library>.3dshapes/<file>.step`) is the library's own.

Only the files the three boards actually use are kept (see `python3 tools/model_coverage.py -v`). Two models
the boards name are NOT here, because they were not in the library copy found on this machine:

| Model the board names | Part | What the renders use instead |
|---|---|---|
| `Module.3dshapes/Arduino_Nano_WithMountingHoles.step` | U1, Arduino Nano | `3d/populated/models/nano_on_pbs.scad` |
| `Fuse.3dshapes/Fuse_Bourns_MF-RG1100.step` | F1, PTC fuse | `3d/populated/models/fuse_ptc.scad` |

That is why the Nano drew as an outline only: its model file did not exist.

**Licence.** KiCad's libraries are CC-BY-SA 4.0 with KiCad's exception for designs that use them (the STEP
headers say so). Redistributed here unmodified; the CC-BY-SA terms stay with these files, not with the rest
of the repository.
