First run case prepared from `tutorials/Linear_stability`.

Included:
- `C1input`
- `profile_ne`, `profile_te`, `profile_omega`
- `coil.dat`, `current.dat`
- `rmp_coil.dat`, `rmp_current.dat`
- `run.sh`

Still required before launching:
- Executable (`../../_localgnu-opt-25/m3dc1_2d` by default, or set `M3DC1_BIN`)
- Mesh files referenced by `C1input`:
  - `part.smb`
  - `diiid.txt`

Run command:
```bash
cd /root/M3DC1/unstructured/runs/first_linear
./run.sh
```

Optional env vars:
- `NPROC` (default `1`)
- `M3DC1_BIN` (path to executable)
- `INPUT` (default `C1input`)
- `LOG` (default `run.log`)
