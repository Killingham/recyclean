import os
import pandas as pd
import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Recyclean", page_icon="♻️", layout="wide")
st.title("♻️ Recyclean: residuos introducidos")


def secreto(nombre):
    try:
        return st.secrets[nombre]
    except Exception:
        return os.environ[nombre]


supabase = create_client(secreto("SUPABASE_URL"), secreto("SUPABASE_KEY"))

NOMBRES = {"papel_carton": "Papel / cartón", "plastico": "Plástico", "vidrio": "Vidrio"}
ICONOS = {"papel_carton": "📦", "plastico": "🧴", "vidrio": "🍾"}


@st.fragment(run_every=3)
def panel():
    r = (supabase.table("detecciones").select("*")
         .eq("origen", "basurero").order("hora", desc=True).limit(500).execute())
    df = pd.DataFrame(r.data)

    if df.empty:
        st.info("Aún no se ha introducido ningún residuo al basurero.")
        return

    df["hora"] = pd.to_datetime(df["hora"], utc=True).dt.tz_convert("America/Bogota")
    ultimo = df.iloc[0]
    clase = ultimo["clase"]

    st.subheader("Último residuo introducido")
    st.markdown(f"# {ICONOS.get(clase, '♻️')} {NOMBRES.get(clase, clase)}")
    st.caption(f"Confianza {ultimo['confianza']:.0%} · {ultimo['hora']:%d/%m/%Y %H:%M:%S}")

    conteo = df["clase"].value_counts()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total introducidos", len(df))
    c2.metric("📦 Papel / cartón", int(conteo.get("papel_carton", 0)))
    c3.metric("🧴 Plástico", int(conteo.get("plastico", 0)))
    c4.metric("🍾 Vidrio", int(conteo.get("vidrio", 0)))

    izq, der = st.columns(2)
    with izq:
        st.subheader("Residuos por material")
        st.bar_chart(conteo)
    with der:
        st.subheader("Residuos por hora")
        st.line_chart(df.set_index("hora").resample("h").size())

    st.subheader("Últimos residuos")
    tabla = df.head(10).copy()
    tabla["material"] = tabla["clase"].map(lambda c: NOMBRES.get(c, c))
    tabla["confianza"] = (tabla["confianza"] * 100).round().astype(int).astype(str) + "%"
    tabla["hora"] = tabla["hora"].dt.strftime("%d/%m %H:%M:%S")
    st.dataframe(tabla[["hora", "material", "confianza"]], width="stretch", hide_index=True)


panel()