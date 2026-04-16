import streamlit as st
import pandas as pd
import os, io

# --- 1. OSNOVA ---
st.set_page_config(page_title="Atletski Troboj PRO", layout="wide", page_icon="🏃‍♂️")

def dobi_leta():
    if not os.path.exists("Podatki"): 
        os.makedirs("Podatki")
    dirs = [d for d in os.listdir("Podatki") if os.path.isdir(os.path.join("Podatki", d))]
    yrs = sorted([d.replace("_", "/") for d in dirs])
    return yrs if yrs else ["2025/26"]

leta_vsa = dobi_leta()

# --- 2. STOPNIČKE IN REKORDI ---
@st.dialog("🏆 Najboljši & stopničke")
def prikazi_stopnicke(leto_pot):
    # Ustvarimo zavihke za Spol
    t_fanti, t_punce = st.tabs(["👦 Fanti", "👧 Punce"])
    
    # Razdelitev razredov
    razredna_stopnja = [f"{i}. razred" for i in range(1, 6)]
    predmetna_stopnja = [f"{i}. razred" for i in range(6, 10)]
    
    for idx, s_ime in enumerate(["Fanti", "Punce"]):
        with [t_fanti, t_punce][idx]:
            # Znotraj spola ustvarimo pod-zavihke za stopnje
            sub1, sub2 = st.tabs(["🏫 Razredna (1-5)", "🎓 Predmetna (6-9)"])
            
            for sub_tab, stopnja_list, naslov in [(sub1, razredna_stopnja, "Razredna"), (sub2, predmetna_stopnja, "Predmetna")]:
                with sub_tab:
                    st.subheader(f"🥇 Skupne stopničke ({naslov})")
                    v_sez = []
                    for r in stopnja_list:
                        # Uporabimo tvoj format s podčrtaji: baza_Spol_X._razred.csv
                        p = os.path.join(leto_pot, f"baza_{s_ime}_{r.replace(' ', '_')}.csv")
                        if os.path.exists(p):
                            tdf = pd.read_csv(p)
                            if not tdf.empty:
                                tdf["R"] = r
                                v_sez.append(tdf)
                    
                    if v_sez:
                        df_stopnja = pd.concat(v_sez)
                        if "SKUPAJ" in df_stopnja.columns:
                            top3 = df_stopnja[df_stopnja["SKUPAJ"] > 0].sort_values("SKUPAJ", ascending=False).head(3)
                            cols = st.columns(3)
                            for i, (_, row) in enumerate(top3.iterrows()):
                                with cols[i]:
                                    st.metric(label=f"{i+1}. mesto ({row['R']})", value=f"{int(row['SKUPAJ'])} točk", delta=row['Ime in Priimek'], delta_color="off")
                    else:
                        st.info("Ni podatkov za to stopnjo.")

# --- 3. FUNKCIJE ZA IZRAČUN (DVOJNA LOGIKA) ---
def calc_pts(row, razred_ime):
    try:
        s60 = float(row['60m [s]']) if pd.notnull(row['60m [s]']) else 0
        dalj = float(row['Daljina [m]']) if pd.notnull(row['Daljina [m]']) else 0
        s600 = float(row['600m [s]']) if pd.notnull(row['600m [s]']) else 0
        r_num = int(razred_ime.split('.')[0])
    except:
        return pd.Series([0, 0, 0, 0])

    t6, td, t60 = 0, 0, 0
    
    if r_num <= 5:
        # --- RAZREDNA STOPNJA (Tvoja stara logika) ---
        if s60 > 0 and (17.78 - s60) > 0: 
            t6 = int(8 * (17.78 - s60)**2.1)
        if dalj > 0: 
            td = int(2.2062 * ((dalj * 100) - 130))
        if s600 > 0 and (240 - s600) > 0: 
            t60 = int(0.625 * (240 - s600)**1.51)
    else:
        # --- PREDMETNA STOPNJA (Nove formule) ---
        if s60 > 0 and (14.6 - s60) > 0:
            t6 = int(7.48676 * (14.6 - s60)**2.5)
        if dalj > 0 and (dalj - 1.25) > 0:
            td = int(171.91361 * (dalj - 1.25)**1.1)
        if s600 > 0 and (175.43 - s600) > 0:
            t60 = int(0.089752 * (175.43 - s600)**2.1)
            
    return pd.Series([t6, td, t60, t6+td+t60])

def to_excel(df_in):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as wr:
        df_in.to_excel(wr, index=False, sheet_name="Rezultati")
    return out.getvalue()

# --- 4. SIDEBAR ---
st.sidebar.title("🏃‍♂️ TROBOJ")
leto = st.sidebar.selectbox("Leto:", leta_vsa, index=len(leta_vsa)-1)
# ... (koda za novo leto ostane ista) ...

st.sidebar.divider()
spol = st.sidebar.radio("Spol:", ["Fanti", "Punce"])
razredi = [f"{i}. razred" for i in range(1, 10)]
razred = st.sidebar.selectbox("Razred:", razredi)

if st.sidebar.button("🏆 NAJBOLJŠI & STOPNIČKE", use_container_width=True):
    prikazi_stopnicke(os.path.join("Podatki", leto.replace("/","_")))

# --- 5. PODATKI (Pot do datotek) ---
pot_l = os.path.join("Podatki", leto.replace("/","_"))
# Pazimo na format: baza_Fanti_1._razred.csv (zamenjamo presledek s podčrtajem)
fn = os.path.join(pot_l, f"baza_{spol}_{razred.replace(' ', '_')}.csv")
cols = ["#", "Ime in Priimek", "60m [s]", "Točke (60m)", "Daljina [m]", "Točke (Daljina)", "600m [s]", "Točke (600m)", "SKUPAJ"]

# ... (nalaganje df ostane isto) ...
if os.path.exists(fn): 
    df = pd.read_csv(fn)
else:
    df = pd.DataFrame(columns=cols)

if df.empty: 
    df = pd.DataFrame([[1, ""] + [0.0]*7], columns=cols)

# --- 6. UI ---
st.title(f"🏆 {leto} | {razred}: {spol}")

# ... (config editorja ostane isti) ...
ed = st.data_editor(df, num_rows="dynamic", use_container_width=True, key=fn)

if st.button("🚀 SHRANI", use_container_width=True):
    kon = ed[ed["Ime in Priimek"].fillna("").str.strip() != ""].copy()
    if not kon.empty:
        kon["#"] = range(1, len(kon) + 1)
        # TUKAJ PODAMO RAZRED V FUNKCIJO
        kon[["Točke (60m)","Točke (Daljina)","Točke (600m)","SKUPAJ"]] = kon.apply(lambda r: calc_pts(r, razred), axis=1)
        kon.to_csv(fn, index=False)
        st.success(f"Shranjeno z uporabo točkovnika za {razred}!")
        st.rerun()

# ... (prikaz rezultatov spodaj ostane isti) ...
