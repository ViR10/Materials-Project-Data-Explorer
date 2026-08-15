"""
Materials Data Explorer
------------------------
Streamlit app jo Materials Project API se live data fetch karta hai,
filter karta hai, aur nicely display karta hai.

Run karne ke liye:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
from mp_api.client import MPRester

st.set_page_config(page_title="Materials Data Explorer", page_icon="🔬", layout="wide")

st.title("🔬 Materials Data Explorer")
st.caption("Materials Project API se live materials data fetch, filter aur explore karo.")

# ============================================================
# SESSION STATE — yeh app ke "memory" ki tarah kaam karta hai.
# Streamlit har interaction pe pura script re-run karta hai,
# isliye API key aur fetched data ko yaad rakhne ke liye
# session_state zaroori hai, warna har click pe sab reset ho jayega.
# ============================================================
if "api_key_valid" not in st.session_state:
    st.session_state.api_key_valid = False
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "df" not in st.session_state:
    st.session_state.df = None

# ============================================================
# STEP 1 — API KEY INPUT + VALIDATION
# ============================================================
st.sidebar.header("🔑 Materials Project API Key")

api_key_input = st.sidebar.text_input(
    "Apni API key yahan paste karo",
    type="password",   # screen pe dots dikhenge, plain text nahi
    value=st.session_state.api_key,
)

if st.sidebar.button("Validate Key"):
    if not api_key_input.strip():
        st.sidebar.error("API key khaali hai. Pehle key enter karo.")
    else:
        with st.sidebar:
            with st.spinner("Key check ho rahi hai..."):
                try:
                    # Lightweight test query — Silicon (mp-149) hamesha
                    # database mein exist karta hai, isliye ismein sirf
                    # ek field maang ke fast check karte hain.
                    with MPRester(api_key_input) as mpr:
                        _ = mpr.materials.summary.search(
                            material_ids=["mp-149"],
                            fields=["material_id"],
                        )
                    st.session_state.api_key_valid = True
                    st.session_state.api_key = api_key_input
                    st.success("✅ API key valid hai.")
                except Exception as e:
                    # Broad except istemal kiya kyunki mp-api ke exact
                    # exception classes API version ke sath change hote
                    # rehte hain. Production code mein specific exception
                    # (jaise requests.exceptions.HTTPError) catch karna
                    # behtar practice hai.
                    st.session_state.api_key_valid = False
                    st.error(f"❌ Key invalid ya connection error:\n{e}")

if not st.session_state.api_key_valid:
    st.info("👈 Pehle sidebar mein apni Materials Project API key enter karke 'Validate Key' dabao.")
    st.caption("API key yahan se milti hai: https://materialsproject.org/api")
    st.stop()   # jab tak key valid nahi, aage ka code chalega hi nahi

# ============================================================
# STEP 2 — FORMULA SEARCH
# ============================================================
st.header("🔍 Material Search")

formula = st.text_input("Chemical formula enter karo (e.g. Fe2O3, TiO2, Al2O3)")
search_btn = st.button("Fetch Data")

if search_btn:
    if not formula.strip():
        st.warning("Pehle koi formula likho.")
    else:
        try:
            with st.spinner(f"'{formula}' ka data fetch ho raha hai..."):
                with MPRester(st.session_state.api_key) as mpr:
                    docs = mpr.materials.summary.search(
                        formula=formula,
                        fields=[
                            "material_id", "formula_pretty", "symmetry",
                            "density", "band_gap", "formation_energy_per_atom",
                            "energy_above_hull", "nsites",
                        ],
                    )
        except Exception as e:
            st.error(f"Data fetch karte waqt error aaya:\n{e}")
            docs = None

        if docs is not None:
            if not docs:
                st.warning(f"'{formula}' ke liye koi result nahi mila. Formula check karo.")
                st.session_state.df = None
            else:
                # Raw API objects ko clean dictionary rows mein convert
                # karte hain taake pandas DataFrame bana sakein.
                rows = []
                for d in docs:
                    rows.append({
                        "Material ID": d.material_id,
                        "Formula": d.formula_pretty,
                        # symmetry.crystal_system Enum object hai, string nahi —
                        # str() se convert karna zaroori hai, warna sorted()
                        # aage Enum objects compare nahi kar payega (TypeError).
                        "Crystal System": str(d.symmetry.crystal_system) if d.symmetry else None,
                        "Density (g/cm³)": round(d.density, 3) if d.density is not None else None,
                        "Band Gap (eV)": round(d.band_gap, 3) if d.band_gap is not None else None,
                        "Formation Energy (eV/atom)": round(d.formation_energy_per_atom, 4) if d.formation_energy_per_atom is not None else None,
                        "Energy Above Hull (eV/atom)": round(d.energy_above_hull, 4) if d.energy_above_hull is not None else None,
                        "Num Sites": d.nsites,
                    })
                st.session_state.df = pd.DataFrame(rows)

# ============================================================
# STEP 3 — FILTERS + DISPLAY
# ============================================================
if st.session_state.df is not None:
    df = st.session_state.df
    st.header("📊 Results")

    st.subheader("Filters")
    col1, col2, col3 = st.columns(3)

    with col1:
        crystal_systems = sorted(df["Crystal System"].dropna().unique().tolist())
        selected_systems = st.multiselect(
            "Crystal System", crystal_systems, default=crystal_systems
        )

    with col2:
        min_bg = float(df["Band Gap (eV)"].min())
        max_bg = float(df["Band Gap (eV)"].max())
        if min_bg == max_bg:
            max_bg += 0.01  # slider ko crash hone se bachane ke liye
        band_gap_range = st.slider("Band Gap (eV)", min_bg, max_bg, (min_bg, max_bg))

    with col3:
        stability_threshold = st.slider(
            "Max Energy Above Hull (eV/atom)",
            0.0, 0.5, 0.05, step=0.01,
            help=(
                "0.0 = sirf ground-state (sabse stable) structure. "
                "Literature mein ~0.05 eV/atom se zyada par material "
                "usually experimentally synthesize karna mushkil hota hai."
            ),
        )

    filtered_df = df[
        (df["Crystal System"].isin(selected_systems))
        & (df["Band Gap (eV)"].between(band_gap_range[0], band_gap_range[1]))
        & (df["Energy Above Hull (eV/atom)"] <= stability_threshold)
    ]

    st.write(f"**{len(filtered_df)} / {len(df)} structures filters ke baad match hui**")
    st.dataframe(filtered_df, use_container_width=True)

    if not filtered_df.empty:
        most_stable = filtered_df.loc[filtered_df["Energy Above Hull (eV/atom)"].idxmin()]

        st.subheader("🏆 Most Stable Matching Structure")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Material ID", most_stable["Material ID"])
        m2.metric("Crystal System", most_stable["Crystal System"])
        m3.metric("Band Gap", f"{most_stable['Band Gap (eV)']} eV")
        m4.metric("Density", f"{most_stable['Density (g/cm³)']} g/cm³")

        if most_stable["Band Gap (eV)"] == 0.0:
            st.warning(
                "⚠️ Band Gap = 0.0 eV standard DFT (GGA) ka known limitation ho "
                "sakta hai, khaas kar transition metal oxides (Fe, Co, Ni waghera) "
                "ke liye — material actually metallic nahi bhi ho sakta. GGA+U ya "
                "HSE06 calculation check karna zaroori hai confirm karne ke liye."
            )
    else:
        st.info("Koi structure in filters ko match nahi karti. Thresholds relax karo.")

    csv = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Filtered data CSV download karo",
        csv,
        f"{formula or 'materials'}_filtered.csv",
        "text/csv",
    )
else:
    st.info("Upar formula likho aur 'Fetch Data' dabao.")