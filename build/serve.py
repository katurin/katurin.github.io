#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build/serve.py
Livereload server that calls build.generate_index.build() when source files change.
Run from repository root: python build/serve.py
"""
import sys
from pathlib import Path
import html as _html

# ensure repo root on sys.path so build.generate_index can be imported
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    from build.generate_index import build as generate_index_build
except Exception as e:
    print("Error importing build.generate_index:", e, file=sys.stderr)
    sys.exit(1)

from livereload import Server

def noop():
    # placeholder for simple watches that don't need a python rebuild
    pass

def main(host="127.0.0.1", port=5500, watch_patterns=None):
    if watch_patterns is None:
        watch_patterns = [
            "posts/*.html",
            "style.css",
            "build/index_template.html",
            "build/generate_index.py"
        ]

    # initial build
    print("Running initial build...")
    generate_index_build()

    server = Server()
    # Watch patterns: when changed, call generate_index_build (or noop for lightweight files)
    for pattern in watch_patterns:
        # For posts and templates, run full build
        if pattern.startswith("posts") or "index_template" in pattern or "generate_index" in pattern:
            server.watch(pattern, generate_index_build)
        else:
            server.watch(pattern, noop)

    # Serve repository root so index.html and posts/ and images/ are accessible
    print(f"Starting livereload server at http://{host}:{port} (root: {ROOT})")
    server.serve(root=str(ROOT), host=host, port=port, open_url_delay=1)

if __name__ == "__main__":
    main(host="127.0.0.1", port=5510)