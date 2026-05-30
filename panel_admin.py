import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Distribuidora OKS - Panel", layout="wide")

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
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/854/854878.png", width=100)
    st.sidebar.title("Menú OKS")
    modo = st.sidebar.radio("Navegación:", ["Panel Principal (Rutas)", "Panel Gestión (Actualizar Clientes)"])
    st.sidebar.markdown("---")

    if st.sidebar.button("Cerrar Sesión"):
        st.session_state['logueado'] = False
        st.rerun()

    # ==========================================
    # PANEL PRINCIPAL (Restaurado con tu estética)
    # ==========================================
    if modo == "Panel Principal (Rutas)":
        archivo_rutas = 'rutas_optimizadas.xlsx' 

        if os.path.exists(archivo_rutas):
            df = pd.read_excel(archivo_rutas)
            df.columns = df.columns.str.strip()
            df['Codigo_Cliente'] = df['Codigo_Cliente'].astype(str).str.replace('.0', '', regex=False).str.strip()
            
            st.title("🗺️ Panel de Enrutamiento Interactivo OKS")
            st.sidebar.header("Filtros")
            vendedores_sel = st.sidebar.multiselect("Seleccionar Vendedores:", sorted(df['Vendedor'].unique().tolist()))
            dias_sel = st.sidebar.multiselect("Seleccionar Días:", ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado'], default=[])

            if vendedores_sel and dias_sel:
                df_f = df[(df['Vendedor'].isin(vendedores_sel)) & (df['Dia'].isin(dias_sel))].copy()
                
                if not df_f.empty:
                    centro = [df_f['Latitud'].mean(), df_f['Longitud'].mean()]
                    m = folium.Map(location=centro, zoom_start=14, tiles='cartodbpositron')

                    for _, row in df_f.iterrows():
                        coord = [row['Latitud'], row['Longitud']]
                        cod_cliente = row['Codigo_Cliente']
                        
                        promedio = row.get('Promedio_3Meses', 'NA')
                        tiene_compra = not (pd.isna(promedio) or str(promedio).strip().upper() in ['NA', 'N/A', '', 'NAN'])

                        # Restauración de tu lógica de colores original
                        color_map = {
                            'Lunes': 'darkred' if tiene_compra else 'red',
                            'Martes': 'darkblue' if tiene_compra else 'lightblue',
                            'Miercoles': 'darkgreen' if tiene_compra else 'lightgreen',
                            'Jueves': 'brown' if tiene_compra else 'orange',
                            'Viernes': 'darkpurple' if tiene_compra else 'purple'
                        }
                        color_pin = color_map.get(row['Dia'], 'black')
                            
                        html_popup = f"""
                        <div style="font-family: Arial, sans-serif; min-width: 250px; font-size: 12px;">
                            <h4 style="margin: 0 0 5px 0; color: #d32f2f;">{row['Cliente']}</h4>
                            <table style="width: 100%; border-collapse: collapse;">
                                <tr><td><b>Código:</b></td><td>{row['Codigo_Cliente']}</td></tr>
                                <tr><td><b>Vendedor:</b></td><td>{row['Vendedor']}</td></tr>
                                <tr><td><b>Día:</b></td><td>{row['Dia']}</td></tr>
                                <tr><td colspan="2"><hr style="margin: 5px 0;"></td></tr>
                                <tr><td><b>Canal:</b></td><td>{row.get('Canal', 'N/A')}</td></tr>
                                <tr><td><b>Prom. 3 Meses:</b></td><td>{row.get('Promedio_3Meses', 'N/A')}</td></tr>
                                <tr><td colspan="2"><b>Dirección:</b><br>{row['Direccion_Completa']}</td></tr>
                            </table>
                        </div>
                        """
                        
                        folium.Marker(
                            location=coord,
                            popup=folium.Popup(html_popup, max_width=350), 
                            tooltip=cod_cliente,
                            icon=folium.Icon(color=color_pin, icon='info-sign')
                        ).add_to(m)

                        # Restauración del texto fijo sobre el mapa
                        folium.Marker(
                            location=coord,
                            icon=folium.DivIcon(
                                icon_size=(150,36), icon_anchor=(7, 18),
                                html=f"""<div style="font-family: 'Arial Black'; color: #000; font-size: 10pt; font-weight: 900; text-shadow: 1px 1px 0 #FFF, -1px -1px 0 #FFF;">{cod_cliente}</div>"""
                            )
                        ).add_to(m)
                    
                    st_folium(m, width=1200, height=750)
                else:
                    st.warning("No se encontraron registros.")
            else:
                st.info("👈 Selecciona Vendedor y Día en el menú lateral.")

    # ==========================================
    # PANEL GESTIÓN (Funcionalidad de actualización)
    # ==========================================
    elif modo == "Panel Gestión (Actualizar Clientes)":
        st.title("🔄 Actualización de Clientes")
        if st.button("🚀 Ejecutar Sincronización"):
            if os.path.exists('rutas_optimizadas.xlsx') and os.path.exists('nuevos_clientes.xlsx'):
                df_m = pd.read_excel('rutas_optimizadas.xlsx')
                df_n = pd.read_excel('nuevos_clientes.xlsx')
                df_m['Codigo_Cliente'] = df_m['Codigo_Cliente'].astype(str).str.strip()
                df_n['Codigo_Cliente'] = df_n['Codigo_Cliente'].astype(str).str.strip()
                
                df_final = pd.concat([df_m, df_n]).drop_duplicates(subset=['Codigo_Cliente'], keep='last')
                df_final.to_excel('rutas_optimizadas.xlsx', index=False)
                st.success("¡Base de datos maestra actualizada!")
            else:
                st.error("Archivos necesarios no encontrados.")
