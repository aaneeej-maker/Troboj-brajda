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
    t_fanti, t_punce = st.tabs(["👦 Fanti", "👧 Punce"])
    
    razredna_stopnja = [f"{i}. razred" for i in range(1, 6)]
    predmetna_stopnja = [f"{i}. razred" for i in range(6, 10)]
    
    for idx, s_ime in enumerate(["Fanti", "Punce"]):
        with [t_fanti, t_punce][idx]:
            sub1, sub2 = st.tabs(["🏫 Razredna (1-5)", "🎓 Predmetna (6-9)"])
            
            for sub_tab, stopnja_list, naslov in [(sub1, razredna_stopnja, "Razredna"), (sub2, predmetna_stopnja, "Predmetna")]:
                with sub_tab:
                    st.subheader(f"🥇 Skupne stopničke ({naslov})")
                    v_sez = []
                    for r in stopnja_list:
                        # Uskladitev s tvojimi datotekami (podčrtaji namesto presledkov)
                        r_fix = r.replace(' ', '_')
                        p = os.path.join(leto_pot, f"baza_{s_ime}_{r_fix}.csv")
                        if os.path.exists(p):
                            tdf = pd.read_csv(p)
                            if not tdf.empty and "SKUPAJ" in tdf.columns:
                                tdf["R"] = r
                                v_sez.append(tdf)
                    
                    if v_sez:
                        df_stopnja = pd.concat(v_sez)
                        # Prikažemo top 3 tiste, ki imajo vsaj nekaj točk
                        top3 = df_stopnja[df_stopnja["SKUPAJ"] > 0].sort_values("SKUPAJ", ascending=False).head(3)
                        if not top3.empty:
                            cols = st.columns(3)
                            for i, (_, row) in enumerate(top3.iterrows()):
                                with cols[i]:
                                    st.metric(label=f"{i+1}. mesto ({row['R']})", value=f"{int(row['SKUPAJ'])} točk", delta=row['Ime in Priimek'], delta_color="off")
                    else:
                        st.info("Ni podatkov za to stopnjo.")

# --- 3. FUNKCIJE ZA IZRAČUN (DVOJNA LOGIKA) ---
def calc_pts(row, razred_ime):
    try:
        s60 = float(row['60m [s]']) if pd.notnull(row['60m [s]']) and row['60m [s]'] != "" else 0
        dalj = float(row['Daljina [m]']) if pd.notnull(row['Daljina [m]']) and row['Daljina [m]'] != "" else 0
        s600 = float(row['600m [s]']) if pd.notnull(row['600m [s]']) and row['600m [s]'] != "" else 0
        r_num = int(razred_ime.split('.')[0])
    except:
        return pd.Series([0, 0, 0, 0])

    t6, td, t60 = 0, 0, 0
    
    if r_num <= 5:
        # --- RAZREDNA STOPNJA (1-5) ---
        if s60 > 0 and (17.78 - s60) > 0: 
            t6 = int(8 * (17.78 - s60)**2.1)
        if dalj > 0: 
            td = int(2.2062 * ((dalj * 100) - 130))
        if s600 > 0 and (240 - s600) > 0: 
            t60 = int(0.625 * (240 - s600)**1.51)
    else:
        # --- PREDMETNA STOPNJA (6-9) ---
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
leto = st.sidebar.
