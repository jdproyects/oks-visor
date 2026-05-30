import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Distribuidora OKS - Panel Central", layout="wide")

# --- CONFIGURACIÓN DE SEGURIDAD ---
USUARIO_VALIDO = "admin"
CLAVE_VALIDA = "oks2026" 

def login():
    st.title("🔐 Acceso Privado OKS")
    col1, col2 = st.columns(2)
    with col1:
        usuario = st.text_input("Usuario")
        clave = st.text_input("Contraseña", type="password")
        if st.button("Entrar"):
            if usuario == USUARIO_VALIDO and clave == CLAVE_VALIDA:
                st.session_state['logueado'] = True
                st.rerun()
            else:
                st.error("Usuario o clave incorrectos")

if 'logueado' not in st.session_state:
    st.session_state['logueado'] = False

if not st.session_state['logueado']:
    login()
else:
    # --- MENÚ LATERAL ---
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/854/854878.png", width=100)
    st.sidebar.title("Menú OKS")
    modo = st.sidebar.radio("Navegación:", ["Panel Principal (Ver Rutas)", "Panel Gestión (Actualizar Clientes)"])
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state['logueado'] = False
        st.rerun()

    # --- PANEL PRINCIPAL ---
    if modo == "Panel Principal (Ver Rutas)":
        archivo_rutas = 'rutas_optimizadas.xlsx' 
        if os.path.exists(archivo_rutas):
            df = pd.read_excel(archivo_rutas)
            df.columns = df.columns.str.strip()
            df['Codigo_Cliente'] = df['Codigo_Cliente'].astype(str).str.replace('.0', '', regex=False).str.strip()

            st.title("🗺️ Visor de Rutas Geográficas")
            vendedores_sel = st.sidebar.multiselect("Vendedores:", sorted(df['Vendedor'].unique().tolist()))
            dias_sel = st.sidebar.multiselect("Días:", ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado'])

            if vendedores_sel and dias_sel:
                df_f = df[(df['Vendedor'].isin(vendedores_sel)) & (df['Dia'].isin(dias_sel))].copy()
                if not df_f.empty:
                    centro = [df_f['Latitud'].mean(), df_f['Longitud'].mean()]
                    m = folium.Map(location=centro, zoom_start=14, tiles='cartodbpositron')
                    for _, row in df_f.iterrows():
                        folium.Marker(
                            location=[row['Latitud'], row['Longitud']],
                            popup=row['Cliente'],
                            tooltip=row['Codigo_Cliente']
                        ).add_to(m)
                    st_folium(m, width=1200, height=750)
            else:
                st.info("Selecciona filtros en el menú lateral.")
        else:
            st.error("No se encuentra el archivo 'rutas_optimizadas.xlsx'.")

    # --- PANEL GESTIÓN ---
    elif modo == "Panel Gestión (Actualizar Clientes)":
        st.title("🔄 Actualización de Base de Datos")
        if st.button("🚀 Ejecutar Sincronización"):
            if os.path.exists('rutas_optimizadas.xlsx') and os.path.exists('nuevos_clientes.xlsx'):
                df_m = pd.read_excel('rutas_optimizadas.xlsx')
                df_n = pd.read_excel('nuevos_clientes.xlsx')
                df_m['Codigo_Cliente'] = df_m['Codigo_Cliente'].astype(str).str.strip()
                df_n['Codigo_Cliente'] = df_n['Codigo_Cliente'].astype(str).str.strip()
                df_final = pd.concat([df_m, df_n]).drop_duplicates(subset=['Codigo_Cliente'], keep='last')
                df_final.to_excel('rutas_optimizadas.xlsx', index=False)
                st.success("¡Base actualizada correctamente!")
            else:
                st.error("Archivos no encontrados.")
