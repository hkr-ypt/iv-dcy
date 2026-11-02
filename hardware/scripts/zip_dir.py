#!/usr/bin/env python3
# SPDX-License-Identifier: CERN-OHL-S-2.0
# Copyright (c) 2026 Lucas Wu
"""Zip a directory's files (flat, sorted, fixed timestamps): zip_dir.py DIR OUT.zip"""
import sys
import zipfile
from pathlib import Path

src, out = Path(sys.argv[1]), Path(sys.argv[2])
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for f in sorted(p for p in src.iterdir() if p.is_file()):
        info = zipfile.ZipInfo(f.name, date_time=(2026, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        z.writestr(info, f.read_bytes())
print(f"   {out} ({len(z.namelist())} files)")
