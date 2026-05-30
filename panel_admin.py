import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os

# --- 1. CONFIGURACIÓN DE PÁGINA (DEBE SER EL PRIMER COMANDO) ---
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
    # --- MENÚ LATERAL DE NAVEGACIÓN ---
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/854/854878.png", width=100)
    st.sidebar.title("Menú OKS")
    modo = st.sidebar.radio("Navegación:", ["Panel Principal (Ver Rutas)", "Panel Gestión (Actualizar Clientes)"])
    st.sidebar.markdown("---")

    if st.sidebar.button("Cerrar Sesión"):
        st.session_state['logueado'] = False
        st.rerun()

    # ==========================================
    # OPCIÓN 1: PANEL PRINCIPAL (Solo Visualización)
    # ==========================================
    if modo == "Panel Principal (Ver Rutas)":
        archivo_rutas = 'rutas_optimizadas.xlsx' 

        if os.path.exists(archivo_rutas):
            df = pd.read_excel(archivo_rutas)
            df.columns = df.columns.str.strip()
            # Limpiar códigos de cliente
            df['Codigo_Cliente'] = df['Codigo_Cliente'].astype(str).str.replace('.0', '', regex=False).str.strip()

            st.title("🗺️ Visor de Rutas Geográficas OKS")
            st.info("Este panel es de solo lectura. Selecciona los filtros para visualizar los clientes en el mapa.")
            
            st.sidebar.header("Filtros de Mapa")
            vendedores_sel = st.sidebar.multiselect("Vendedores:", sorted(df['Vendedor'].unique().tolist()))
            dias_sel = st.sidebar.multiselect("Días:", ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado'])

            if vendedores_sel and dias_sel:
                df_f = df[(df['Vendedor'].isin(vendedores_sel)) & (df['Dia'].isin(dias_sel))].copy()
                
                if not df_f.empty:
                    centro = [df_f['Latitud'].mean(), df_f['Longitud'].mean()]
                    m = folium.Map(location=centro, zoom_start=14, tiles='cartodbpositron')

                    for _, row in df_f.iterrows():
                        coord = [row['Latitud'], row['Longitud']]
                        
                        # Lógica de colores de pines según el día
                        color_map = {
                            'Lunes': 'red', 'Martes': 'blue', 'Miercoles': 'green',
                            'Jueves': 'orange', 'Viernes': 'purple', 'Sabado': 'black'
                        }
                        color_pin = color_map.get(row['Dia'], 'gray')

                        html_popup = f"""
                        <div style="font-family: Arial; min-width: 200px;">
                            <h4 style="color: #1565c0;">{row['Cliente']}</h4>
                            <b>Código:</b> {row['Codigo_Cliente']}<br>
                            <b>Vendedor:</b> {row['Vendedor']}<br>
                            <b>Día:</b> {row['Dia']}<br>
                            <hr>
                            <b>Dirección:</b><br>{row['Direccion_Completa']}
                        </div>
                        """
                        
                        folium.Marker(
                            location=coord,
                            popup=folium.Popup(html_popup, max_width=300),
                            tooltip=row['Codigo_Cliente'],
                            icon=folium.Icon(color=color_pin, icon='info-sign')
                        ).add_to(m)

                    st_folium(m, width=1200, height=750, key="mapa_visor")
                else:
                    st.warning("No hay datos para esta selección.")
            else:
                st.info("👈 Selecciona Vendedor y Día en el menú lateral.")
        else:
            st.error(f"No se encuentra el archivo '{archivo_rutas}'.")

    # ==========================================
    # OPCIÓN 2: PANEL DE GESTIÓN (Actualización de Clientes)
    # ==========================================
    elif modo == "Panel Gestión (Actualizar Clientes)":
        st.title("🔄 Actualización de Base de Datos Maestra")
        
        archivo_maestro = 'rutas_optimizadas.xlsx'
        archivo_nuevo = 'nuevos_clientes.xlsx'

        st.markdown("""
        ### Instrucciones:
        1. Asegúrate de que el archivo **`nuevos_clientes.xlsx`** esté en la carpeta.
        2. El sistema comparará los códigos de cliente.
        3. Si el cliente ya existe, se actualizará su información con la del nuevo archivo.
        4. Si el cliente no existe, se agregará como nuevo registro.
        """)

        if st.button("🚀 Ejecutar Sincronización de Excel"):
            if os.path.exists(archivo_maestro) and os.path.exists(archivo_nuevo):
                with st.spinner("Procesando archivos..."):
                    # Cargar archivos
                    df_m = pd.read_excel(archivo_maestro)
                    df_n = pd.read_excel(archivo_nuevo)

                    # Limpieza básica
                    df_m['Codigo_Cliente'] = df_m['Codigo_Cliente'].astype(str).str.strip()
                    df_n['Codigo_Cliente'] = df_n['Codigo_Cliente'].astype(str).str.strip()

                    # Fusión: Concatenamos y quitamos duplicados quedándonos con el último (el nuevo)
                    # Esto actualiza datos existentes y añade los nuevos
                    df_final = pd.concat([df_m, df_n], ignore_index=True)
                    df_final = df_final.drop_duplicates(subset=['Codigo_Cliente'], keep='last')

                    # Guardar
                    df_final.to_excel(archivo_maestro, index=False)
                    
                    st.success(f"✅ ¡Actualización completada! Base maestra guardada con {len(df_final)} registros.")
                    st.balloons()
            else:
                st.error("Error: Asegúrate de que ambos archivos Excel existan en la carpeta del programa.")


¡Tu panel OKS ya está listo! He preparado una guía visual para explicarte los cambios y el código completo corregido para que lo pongas a funcionar de inmediato.
