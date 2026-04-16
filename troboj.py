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

# --- 2. POMOŽNE FUNKCIJE (Z VAROVALKO) ---
def formatiraj_v_minute(sekunde):
    # Varovalka za neveljavne vnose (None, nan, besedilo)
    try:
        sek_float = float(sekunde)
        if sek_float <= 0: return "0:00,00"
        minute = int(sek_float // 60)
        preostale_sekunde = sek_float % 60
        return f"{minute}:{preostale_sekunde:05.2f}".replace(".", ",")
    except (ValueError, TypeError):
        return "0:00,00"

def calc_pts(row, razred_ime):
    try:
        s60 = float(row['60m [s]']) if pd.notnull(row['60m [s]']) else 0
        dalj = float(row['Daljina [m]']) if pd.notnull(row['Daljina [m]']) else 0
        s600 = float(row['600m [s]']) if pd.notnull(row['600m [s]']) else 0
        r_num = int(razred_ime.split('.')[0])
    except: return pd.Series([0, 0, 0, 0])

    t6, td, t60 = 0, 0, 0
    if r_num <= 5:
        if s60 > 0 and (17.78 - s60) > 0: t6 = int(8 * (17.78 - s60)**2.1)
        if dalj > 0: td = int(2.2062 * ((dalj * 100) - 130))
        if s600 > 0 and (240 - s600) > 0: t60 = int(0.625 * (240 - s600)**1.51)
    else:
        if s60 > 0 and (14.6 - s60) > 0: t6 = int(7.48676 * (14.6 - s60)**2.5)
        if dalj > 0 and (dalj - 1.25) > 0: td = int(171.91361 * (dalj - 1.25)**1.1)
        if s600 > 0 and (175.43 - s600) > 0: t60 = int(0.089752 * (175.43 - s600)**2.1)
    return pd.Series([t6, td, t60, t6+td+t60])

def to_excel(df_in):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as wr:
        df_in.to_excel(wr, index=False, sheet_name="Rezultati")
    return out.getvalue()

# --- 3. SIDEBAR ---
st.sidebar.title("🏃‍♂️ TROBOJ")
leto = st.sidebar.selectbox("Leto:", leta_vsa, index=len(leta_vsa)-1)
izbira_spola = st.sidebar.radio("Spol:", ["Fantje", "Punce"])
spol = "Fanti" if izbira_spola == "Fantje" else "Punce"

razredi = [f"{i}. razred" for i in range(1, 10)]
razred = st.sidebar.selectbox("Razred:", razredi)

# --- 4. NALAGANJE PODATKOV ---
pot_l = os.path.join("Podatki", leto.replace("/","_"))
if not os.path.exists(pot_l): os.makedirs(pot_l)
fn = os.path.join(pot_l, f"baza_{spol}_{razred.replace(' ', '_')}.csv")

cols = ["#", "Ime in Priimek", "60m [s]", "Točke (60m)", "Daljina [m]", "Točke (Daljina)", "600m [s]", "Točke (600m)", "SKUPAJ"]

if os.path.exists(fn): 
    df = pd.read_csv(fn)
    # Odpravimo morebitne None vrednosti takoj ob nalaganju
    df = df.fillna(0)
    for c in cols:
        if c not in df.columns: df[c] = 0.0
    df = df[cols]
else: 
    df = pd.DataFrame(columns=cols)

if df.empty: 
    df = pd.DataFrame([[1, ""] + [0.0]*7], columns=cols)

# --- 5. UI ZA VNOS ---
st.title(f"🏆 {leto} | {razred}: {izbira_spola}")

config = {
    "#": st.column_config.NumberColumn("št.", disabled=True, width="small"),
    "60m [s]": st.column_config.NumberColumn("60m [s]", step=0.01, format="%.2f", default=0.0),
    "600m [s]": st.column_config.NumberColumn("600m [sek]", step=0.01, format="%.2f", default=0.0),
    "Daljina [m]": st.column_config.NumberColumn("Daljina [m]", step=0.01, format="%.2f", default=0.0),
    "Točke (60m)": st.column_config.NumberColumn("🔒 T_60", disabled=True),
    "Točke (Daljina)": st.column_config.NumberColumn("🔒 T_Dalj", disabled=True),
    "Točke (600m)": st.column_config.NumberColumn("🔒 T_600", disabled=True),
    "SKUPAJ": st.column_config.NumberColumn("🔒 SKUPAJ", disabled=True)
}

ed = st.data_editor(df, num_rows="dynamic", use_container_width=True, key=f"ed_{fn}", column_config=config)

if st.button("🚀 SHRANI", use_container_width=True):
    kon = ed[ed["Ime in Priimek"].fillna("").str.strip() != ""].copy()
    if not kon.empty:
        kon["#"] = range(1, len(kon) + 1)
        kon[["Točke (60m)","Točke (Daljina)","Točke (600m)","SKUPAJ"]] = kon.apply(lambda r: calc_pts(r, razred), axis=1)
        kon = kon[cols].fillna(0)
        kon.to_csv(fn, index=False)
        st.success("Shranjeno!")
        st.rerun()

# --- 6. REZULTATI ---
dejanski = ed[ed["Ime in Priimek"].fillna("").str.strip() != ""].copy()
if not dejanski.empty:
    st.divider()
    dejanski[["Točke (60m)","Točke (Daljina)","Točke (600m)","SKUPAJ"]] = dejanski.apply(lambda r: calc_pts(r, razred), axis=1)
    
    # Zdaj funkcija formatiraj_v_minute ne bo več "pokala", če dobi None
    dejanski["600m [min:sek]"] = dejanski["600m [s]"].apply(formatiraj_v_minute)
    
    res = dejanski.sort_values("SKUPAJ", ascending=False).reset_index(drop=True)
    res.index += 1
    res["Mesto"] = res.index
    
    prikaz_cols = ["Mesto", "#", "Ime in Priimek", "60m [s]", "Daljina [m]", "600m [s]", "600m [min:sek]", "SKUPAJ"]
    st.subheader("📊 Trenutni vrstni red")
    st.dataframe(res[prikaz_cols], use_container_width=True)
    
    st.write("📥 **Izvoz:**")
    st.download_button("📊 Izvozi Excel", to_excel(res), f"Troboj_{razred}.xlsx")

st.markdown("<br><hr><center><small>Izdelal: Anej Nagode, 2026</small></center>", unsafe_allow_html=True)
