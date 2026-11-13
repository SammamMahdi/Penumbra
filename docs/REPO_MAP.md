# Repository map

```text
Penumbra/
├── backend/app/          FastAPI app; science/ (tested modules) and services/ (cache, bundles, analyses)
├── src/                  React + TypeScript frontend (features/, api/client.ts, hooks/, state/, utils/)
├── tests/
│   ├── scientific/       S1-S12 + V4 (pytest)
│   ├── api/              endpoints and every error path (pytest + FastAPI TestClient)
│   ├── frontend/         Vitest + Testing Library
│   └── e2e/              Playwright journeys A-C, responsive and offline checks
├── scripts/              download_data (+ build_download_manifest), link_data, build_datasets, precompute, benchmark,
│                         gen_docs; imagery builders (polarlib,
│                         prepare_trek, prepare_site_images, prepare_tiles, prepare_globe, prepare_polar)
├── data/
│   ├── raw/              NASA/JPL files from scripts/download_data.py or tasks.py link (not committed)
│   ├── cache/            computed products (not committed)
│   └── metadata/         files.json (SHA-256), datasets.json (sources, frames, versions), downloads.json (download list)
├── tiles/                globe imagery tiles from tasks.py imagery (not committed)
├── docs/                 ASSISTANT.md (Armstrong), method, validation, provenance, performance, test report, UI references
├── screenshots/          QA and e2e screenshots (only the two images used in PENUMBRA.md are committed)
├── serve.py              tile builders (imported by the backend for /tiles)
├── tasks.py              doctor · data · imagery · link · precompute · build · dev · test
└── README.md (user guide), PENUMBRA.md (features, science, validation), DATA_DOWNLOAD_MANUAL.md, ARCHITECTURE.md, .env.example
```

## Data

The data is not stored in the repository. `python tasks.py data` downloads it and `python tasks.py imagery` builds the
globe tiles; see [DATA_DOWNLOAD_MANUAL.md](../DATA_DOWNLOAD_MANUAL.md). On the original development machine,
`python tasks.py link` hard-links the same files from the first download folders instead.
