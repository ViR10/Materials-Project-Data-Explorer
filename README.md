# Materials Data Explorer

A Streamlit web application that connects to the [Materials Project](https://materialsproject.org)
API to fetch, filter, and explore computed materials data in real time. Built as part of a
self-directed Materials Informatics learning path, combining API integration, scientific
data validation, and interactive filtering.

## Overview

Given a chemical formula (e.g. `Fe2O3`), the app queries the Materials Project database,
which typically returns multiple candidate crystal structures (polymorphs) for that
composition — not all of them physically realistic or stable. The app helps identify the
thermodynamically most stable structure and lets the user filter results by crystal
system, band gap, and stability, rather than blindly trusting the first result returned.

## Features

- **Runtime API key entry** — the Materials Project API key is entered by the user at
  runtime through a password-masked input field. It is never hardcoded or written to
  disk; it exists only for the duration of the browser session.
- **Key validation** — before any search is allowed, the app runs a lightweight test
  query (fetching a single field for Silicon, `mp-149`, which always exists in the
  database) to confirm the key is valid. Invalid keys or connection failures produce a
  clear error message instead of a silent crash.
- **Formula-based search** — enter any chemical formula and retrieve all matching
  structures from the database, including material ID, crystal system, density, band
  gap, formation energy, energy above hull, and number of atomic sites.
- **Interactive filters**:
  - **Crystal System** — multi-select filter (e.g. Trigonal, Cubic, Orthorhombic)
  - **Band Gap range** — slider bounded by the actual min/max of the fetched results
  - **Stability threshold (Energy Above Hull)** — filters out structures that are too
    thermodynamically unstable to be realistically synthesizable (default threshold:
    0.05 eV/atom, a commonly cited cutoff in materials screening literature)
- **Automatic identification of the most stable structure** among the filtered results,
  displayed with key metrics.
- **Built-in scientific warning** — if the most stable structure's band gap is 0.0 eV,
  the app flags this as a possible artifact of standard DFT (GGA) calculations rather
  than evidence the material is truly metallic, since GGA is known to underestimate band
  gaps in transition metal oxides.
- **CSV export** of the filtered dataset for further analysis outside the app.

## Tech Stack

- [Streamlit](https://streamlit.io) — web UI framework
- [mp-api](https://github.com/materialsproject/api) — official Materials Project API client
- [pandas](https://pandas.pydata.org) — data handling and filtering

## Setup

```bash
pip install -r requirements.txt
streamlit run app.py
```

You will need a free Materials Project API key, available at:
https://materialsproject.org/api

Paste the key into the sidebar field when the app launches, then click **Validate Key**
before running a search.

## Scientific Notes

These notes exist because it's easy to treat database output as ground truth. It isn't:

- All property values in this app are **DFT-calculated** (computed via Density
  Functional Theory), not experimentally measured. Treat them as approximations, not
  verified physical measurements.
- `Energy Above Hull = 0.0 eV/atom` indicates a thermodynamic ground state — the most
  stable known structure for that composition. Higher values indicate metastable
  structures that are progressively less likely to be experimentally realizable.
- Standard DFT with the GGA (Generalized Gradient Approximation) functional is known to
  **underestimate band gaps**, sometimes reporting 0 eV (implying metallic behavior) for
  materials that are experimentally known to be insulators or semiconductors. This is
  especially common for transition metal oxides (Fe, Co, Ni, etc.) due to how GGA
  handles strongly correlated d-electrons. More accurate (but more computationally
  expensive) methods like GGA+U or HSE06 are typically needed to correct this.
- A formula search returning multiple structures is normal — it reflects the existence
  of multiple known or hypothetical polymorphs for that composition, not a data error.

## Known Limitations

- Exception handling around the API client currently catches broad `Exception` types
  rather than specific ones, since the exact exception classes exposed by `mp-api`
  change between versions. A more robust implementation would catch specific network/auth
  exceptions separately.
- The app currently supports single-formula lookups only; no side-by-side comparison
  between multiple formulas yet.
- No crystal structure visualization (2D/3D) is included yet.

## Roadmap

- [ ] Add crystal structure visualization using `pymatgen`
- [ ] Support comparing multiple formulas side by side
- [ ] Integrate `matminer` composition-based descriptors directly into the app
- [ ] Replace broad exception handling with specific exception types

---

Part of an ongoing Materials Informatics learning project — Week 2 integration of
materials database access, API validation, and interactive data exploration.