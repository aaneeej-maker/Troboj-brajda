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
    t1, t2 = st.tabs(["👦 Fanti", "👧 Punce"])
    razredi = [f"{i}. razred" for i in range(1, 10)]
    for idx, s_ime in enumerate(["Fanti", "Punce"]):
        with [t1, t2][idx]:
            v_sez = []
            st.subheader("🥇 Stopničke po razredih")
            for r in razredi:
                p = os.path.join(leto_pot, f"baza_{s_ime}_{r.replace(' ', '_')}.csv")
                if os.path.exists(p):
                    tdf = pd.read_csv(p)
                    if not tdf.empty and "Ime in Priimek" in tdf.columns:
                        tdf["R"] = r
                        v_sez.append(tdf)
                        if "SKUPAJ" in tdf.columns:
                            top3 = tdf[tdf["SKUPAJ"] > 0].nlargest(3, "SKUPAJ")
                            if not top3.empty:
                                with st.expander(f"📍 {r}"):
                                    for j, (_, row) in enumerate(top3.iterrows()):
                                        st.write(f"{['🥇','🥈','🥉'][j]} {row['Ime in Priimek']}: **{row['SKUPAJ']}**")
            
            if v_sez:
                st.divider()
                st.subheader("⭐ Rekordi sezone")
                df_all = pd.concat(v_sez)
                for l, c, m in [("⚡ 60m","60m [s]","min"),("🚀 Daljina","Daljina [m]","max"),("🏃 600m","600m [s]","min")]:
                    if c in df_all.columns:
                        st.write(f"**{l}**")
                        sub = df_all[df_all[c] > 0]
                        if not sub.empty:
                            best = sub.nsmallest(3, c) if m=="min" else sub.nlargest(3, c)
                            for k, (_, rb) in enumerate(best.iterrows()):
                                st.write(f"{['🥇','🥈','🥉'][k]} {rb['Ime in Priimek']} ({rb['R']}): **{rb[c]}**")

# --- 3. FUNKCIJE ---
def calc_pts(r):
    try:
        s60 = float(r['60m [s]']) if pd.notnull(r['60m [s]']) else 0
        dalj = float(r['Daljina [m]']) if pd.notnull(r['Daljina [m]']) else 0
        s600 = float(r['600m [s]']) if pd.notnull(r['600m [s]']) else 0
    except:
        s60, dalj, s600 = 0, 0, 0

    t6, td, t60 = 0, 0, 0
    if s60 > 0 and (17.78 - s60) > 0: 
        t6 = int(8 * (17.78 - s60)**2.1)
    if dalj > 0: 
        td = int(2.2062 * ((dalj * 100) - 130))
    if s600 > 0 and (240 - s600) > 0: 
        t60 = int(0.625 * (240 - s600)**1.51)
    return pd.Series([t6, td, t60, t6+td+t60])

def to_excel(df_in):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as wr:
        df_in.to_excel(wr, index=False, sheet_name="Rezultati")
    return out.getvalue()

# --- 4. SIDEBAR ---
st.sidebar.title("🏃‍♂️ TROBOJ")
leto = st.sidebar.selectbox("Leto:", leta_vsa, index=len(leta_vsa)-1)
with st.sidebar.expander("➕ Novo leto"):
    try:
        zad = leta_vsa[-1].split('/')[0]
        n_l = f"{int(zad)+1}/{int(zad)+2}"
        st.write(f"Naslednje: **{n_l}**")
        if st.button("USTVARI"): 
            os.makedirs(os.path.join("Podatki", n_l.replace("/","_")), exist_ok=True)
            st.rerun()
    except: pass

st.sidebar.divider()
spol = st.sidebar.radio("Spol:", ["Fanti", "Punce"])
razredi = [f"{i}. razred" for i in range(1, 10)]
razred = st.sidebar.selectbox("Razred:", razredi)

if st.sidebar.button("🏆 NAJBOLJŠI & STOPNIČKE", use_container_width=True):
    prikazi_stopnicke(os.path.join("Podatki", leto.replace("/","_")))

# --- 5. PODATKI ---
pot_l = os.path.join("Podatki", leto.replace("/","_"))
if not os.path.exists(pot_l): os.makedirs(pot_l)
fn = os.path.join(pot_l, f"baza_{spol}_{razred.replace(' ', '_')}.csv")
cols = ["#", "Ime in Priimek", "60m [s]", "Točke (60m)", "Daljina [m]", "Točke (Daljina)", "600m [s]", "Točke (600m)", "SKUPAJ"]

if os.path.exists(fn): 
    df = pd.read_csv(fn)
    if "Letnik rojstva" in df.columns: df = df.drop(columns=["Letnik rojstva"])
else:
    l_i, r_i = leta_vsa.index(leto), razredi.index(razred)
    if l_i > 0 and r_i > 0:
        p_fn = os.path.join("Podatki", leta_vsa[l_i-1].replace("/","_"), f"baza_{spol}_{razredi[r_i-1].replace(' ','_')}.csv")
        if os.path.exists(p_fn):
            stari_df = pd.read_csv(p_fn)
            # Uvozimo brez sortiranja po abecedi
            df = stari_df[["Ime in Priimek"]].copy()
            df.insert(0, "#", range(1, len(df) + 1)) 
            for c in cols[2:]: df[c] = 0.0
        else: df = pd.DataFrame(columns=cols)
    else: df = pd.DataFrame(columns=cols)

if df.empty: 
    df = pd.DataFrame([[1, ""] + [0.0]*7], columns=cols)

# --- 6. UI ---
st.title(f"🏆 {leto} | {razred}: {spol}")

config = {
    "#": st.column_config.NumberColumn("št.", disabled=True, width="small"),
    "Ime in Priimek": st.column_config.TextColumn("Ime in Priimek", width="large"),
    "Točke (60m)": st.column_config.NumberColumn("🔒", disabled=True),
    "Točke (Daljina)": st.column_config.NumberColumn("🔒", disabled=True),
    "Točke (600m)": st.column_config.NumberColumn("🔒", disabled=True),
    "SKUPAJ": st.column_config.NumberColumn("🔒", disabled=True)
}

ed = st.data_editor(df, num_rows="dynamic", use_container_width=True, key=fn, column_config=config)

if st.button("🚀 SHRANI", use_container_width=True):
    # Odstranimo vrstice, kjer ni vpisanega imena
    kon = ed[ed["Ime in Priimek"].fillna("").str.strip() != ""].copy()
    
    if not kon.empty:
        # Številke dodelimo glede na ROČNI vrstni red v tabeli
        kon["#"] = range(1, len(kon) + 1)
        
        # Izračun točk
        kon[["Točke (60m)","Točke (Daljina)","Točke (600m)","SKUPAJ"]] = kon.apply(calc_pts, axis=1)
        
        # Prisili vrstni red stolpcev
        kon = kon[cols]
        kon.to_csv(fn, index=False)
        st.success("Shranjeno po vašem vrstnem redu!")
        st.rerun()
    else:
        pd.DataFrame(columns=cols).to_csv(fn, index=False)
        st.warning("Tabela je prazna.")
        st.rerun()

# Prikaz rezultatov pod urejevalnikom
if not df.empty and str(df.iloc[0,1]).strip():
    st.divider()
    res = df.sort_values("SKUPAJ", ascending=False).reset_index(drop=True)
    res.index += 1
    st.subheader("📊 Trenutni vrstni red (po točkah)")
    st.dataframe(res, use_container_width=True)
    
    st.write("📥 **Izvoz podatkov:**")
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("📊 VSI PODATKI (Excel)", to_excel(res), f"Rezultati_{leto.replace('/','_')}_{razred}.xlsx", use_container_width=True)
    with c2:
        meritve = res[["#", "Ime in Priimek", "60m [s]", "Daljina [m]", "600m [s]"]]
        st.download_button("⏱️ SAMO MERITVE (Excel)", to_excel(meritve), f"Meritve_{leto.replace('/','_')}_{razred}.xlsx", use_container_width=True)

st.markdown("<br><hr><center><small>Izdelal: Anej Nagode, Rezultatski izračun: Luka Mrakič, 2026</small></center>", unsafe_allow_html=True)
