import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os

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
    st.set_page_config(page_title="Distribuidora OKS - Panel", layout="wide")
    
    # --- MENÚ LATERAL DE NAVEGACIÓN ---
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/854/854878.png", width=100)
    st.sidebar.title("Menú OKS")
    modo = st.sidebar.radio("Navegación:", ["Panel Principal (Rutas)", "Panel Secundario (Solo Visor)"])
    st.sidebar.markdown("---")

    if st.sidebar.button("Cerrar Sesión"):
        st.session_state['logueado'] = False
        st.rerun()

    # ==========================================
    # OPCIÓN 1: PANEL PRINCIPAL (Armado de Rutas)
    # ==========================================
    if modo == "Panel Principal (Rutas)":
        archivo_rutas = 'rutas_optimizadas.xlsx' 

        if os.path.exists(archivo_rutas):
            df = pd.read_excel(archivo_rutas)
            df.columns = df.columns.str.strip()
            df['Codigo_Cliente'] = df['Codigo_Cliente'].astype(str).str.replace('.0', '', regex=False).str.strip()
            
            if 'ruta_actual' not in st.session_state:
                st.session_state['ruta_actual'] = [] 
            if 'coordenadas_ruta' not in st.session_state:
                st.session_state['coordenadas_ruta'] = [] 

            st.title("🗺️ Panel de Enrutamiento Interactivo OKS")
            
            st.sidebar.header("Filtros")
            vendedores_sel = st.sidebar.multiselect("Seleccionar Vendedores:", sorted(df['Vendedor'].unique().tolist()))
            dias_sel = st.sidebar.multiselect("Seleccionar Días:", ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado'], default=[])

            if st.sidebar.button("🧹 Limpiar Ruta Actual"):
                st.session_state['ruta_actual'] = []
                st.session_state['coordenadas_ruta'] = []
                st.rerun()

            if vendedores_sel and dias_sel:
                df_f = df[(df['Vendedor'].isin(vendedores_sel)) & (df['Dia'].isin(dias_sel))].copy()
                
                if not df_f.empty:
                    centro = [df_f['Latitud'].mean(), df_f['Longitud'].mean()]
                    m = folium.Map(location=centro, zoom_start=14, tiles='cartodbpositron')

                    if len(st.session_state['coordenadas_ruta']) > 1:
                        folium.PolyLine(
                            st.session_state['coordenadas_ruta'],
                            color="black", 
                            weight=4,
                            opacity=0.8
                        ).add_to(m)

                    for _, row in df_f.iterrows():
                        coord = [row['Latitud'], row['Longitud']]
                        cod_cliente = row['Codigo_Cliente']
                        
                        promedio = row.get('Promedio_3Meses', 'NA')
                        tiene_compra = True
                        if pd.isna(promedio) or str(promedio).strip().upper() in ['NA', 'N/A', '', 'NAN']:
                            tiene_compra = False

                        if row['Dia'] == 'Lunes':
                            color_pin = 'darkred' if tiene_compra else 'red'
                        elif row['Dia'] == 'Martes':
                            color_pin = 'darkblue' if tiene_compra else 'lightblue'
                        elif row['Dia'] == 'Miercoles':
                            color_pin = 'darkgreen' if tiene_compra else 'lightgreen'
                        elif row['Dia'] == 'Jueves':
                            color_pin = 'brown' if tiene_compra else 'orange' 
                        elif row['Dia'] == 'Viernes':
                            color_pin = 'darkpurple' if tiene_compra else 'purple'
                        else:
                            color_pin = 'black'
                        
                        vend_ant = row.get('Vendedor_Anterior', '')
                        if pd.isna(vend_ant) or str(vend_ant).strip().upper() in ['NA', 'N/A', 'NAN']:
                            vend_ant = '' 
                            
                        html_popup = f"""
                        <div style="font-family: Arial, sans-serif; min-width: 250px; font-size: 12px;">
                            <h4 style="margin: 0 0 5px 0; color: #d32f2f;">{row['Cliente']}</h4>
                            <table style="width: 100%; border-collapse: collapse;">
                                <tr><td><b>Código:</b></td><td>{row['Codigo_Cliente']}</td></tr>
                                <tr><td><b>Vendedor:</b></td><td>{row['Vendedor']}</td></tr>
                                <tr><td><b>Día:</b></td><td>{row['Dia']}</td></tr>
                                <tr><td colspan="2"><hr style="margin: 5px 0; border: 0; border-top: 1px solid #ccc;"></td></tr>
                                <tr><td><b>Canal:</b></td><td>{row.get('Canal', 'N/A')}</td></tr>
                                <tr><td><b>Prom. 3 Meses:</b></td><td>{row.get('Promedio_3Meses', 'N/A')}</td></tr>
                                <tr><td colspan="2"><hr style="margin: 5px 0; border: 0; border-top: 1px solid #ccc;"></td></tr>
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

                        color_texto = "#00FF00" if cod_cliente in st.session_state['ruta_actual'] else "#000"
                        
                        folium.Marker(
                            location=coord,
                            icon=folium.DivIcon(
                                icon_size=(150,36),
                                icon_anchor=(7, 18),
                                html=f"""<div style="font-family: 'Arial Black'; color: {color_texto}; font-size: 10pt; font-weight: 900; text-shadow: 1px 1px 0 #FFF, -1px -1px 0 #FFF, 1px -1px 0 #FFF, -1px 1px 0 #FFF;">{cod_cliente}</div>"""
                            )
                        ).add_to(m)
                    
                    col1, col2 = st.columns([3, 1]) 
                    
                    with col1:
                        mapa_data = st_folium(m, width=1000, height=750, returned_objects=["last_object_clicked_tooltip"], key="mapa_principal")

                    if mapa_data and mapa_data.get("last_object_clicked_tooltip"):
                        cod_click = mapa_data["last_object_clicked_tooltip"]
                        
                        if cod_click in df_f['Codigo_Cliente'].values and cod_click not in st.session_state['ruta_actual']:
                            fila = df_f[df_f['Codigo_Cliente'] == cod_click].iloc[0]
                            nueva_coord = (fila['Latitud'], fila['Longitud'])
                            
                            st.session_state['ruta_actual'].append(cod_click)
                            st.session_state['coordenadas_ruta'].append(nueva_coord)
                            st.rerun()

                    with col2:
                        st.markdown("### 📋 Orden de Recorrido")
                        if not st.session_state['ruta_actual']:
                            st.info("Haz clic en los pines del mapa para agregar clientes.")
                        else:
                            for i, cod in enumerate(st.session_state['ruta_actual']):
                                nombre_cli = df_f[df_f['Codigo_Cliente'] == cod]['Cliente'].iloc[0]
                                st.write(f"**{i+1}.** {cod} - {nombre_cli}")
                            
                            st.markdown("---")
                            if st.button("💾 Guardar Ruta", use_container_width=True):
                                if 'Orden_Ruta' not in df.columns:
                                    df['Orden_Ruta'] = None
                                    
                                for i, cod in enumerate(st.session_state['ruta_actual']):
                                    df.loc[(df['Codigo_Cliente'] == cod) & (df['Vendedor'].isin(vendedores_sel)) & (df['Dia'].isin(dias_sel)), 'Orden_Ruta'] = i + 1
                                
                                df.to_excel(archivo_rutas, index=False)
                                st.success("¡Ruta guardada!")
                                st.session_state['ruta_actual'] = []
                                st.session_state['coordenadas_ruta'] = []

                else:
                    st.warning("No se encontraron registros.")
            else:
                st.info("👈 Selecciona Vendedor y Día en el menú lateral.")
        else:
            st.error(f"No se encuentra el archivo principal '{archivo_rutas}'.")


    # ==========================================
    # OPCIÓN 2: PANEL SECUNDARIO (Solo Visualización)
    # ==========================================
    elif modo == "Panel Secundario (Solo Visor)":
        archivo_nuevo = 'nuevos_clientes.xlsx'
        archivo_maestro = 'rutas_optimizadas.xlsx'

        if os.path.exists(archivo_nuevo) and os.path.exists(archivo_maestro):
            
            # 1. Cargar tu Excel Nuevo
            df_nuevo = pd.read_excel(archivo_nuevo)
            df_nuevo.columns = df_nuevo.columns.str.strip()
            
            if 'dia visita' in df_nuevo.columns:
                df_nuevo = df_nuevo.rename(columns={'dia visita': 'Dia'})
                
            df_nuevo['Codigo_Cliente'] = df_nuevo['Codigo_Cliente'].astype(str).str.replace('.0', '', regex=False).str.strip()

            # 2. Cargar TODA LA BASE MAESTRA
            df_viejo = pd.read_excel(archivo_maestro)
            df_viejo.columns = df_viejo.columns.str.strip()
            df_viejo['Codigo_Cliente'] = df_viejo['Codigo_Cliente'].astype(str).str.replace('.0', '', regex=False).str.strip()
            df_viejo = df_viejo.drop_duplicates(subset=['Codigo_Cliente'])

            # Limpiar columnas solapadas
            columnas_a_ignorar_del_viejo = ['Vendedor', 'Dia', 'Canal']
            for col in columnas_a_ignorar_del_viejo:
                if col in df_viejo.columns:
                    df_viejo = df_viejo.drop(columns=[col])

            # 3. CRUCE DE DATOS
            df_sec = pd.merge(df_nuevo, df_viejo, on='Codigo_Cliente', how='left')
            
            faltantes = df_sec[df_sec['Latitud'].isna() | df_sec['Longitud'].isna()]
            df_sec = df_sec.dropna(subset=['Latitud', 'Longitud'])

            st.title("🗺️ Visor de Nuevos Clientes")
            
            if not faltantes.empty:
                st.warning(f"⚠️ Atención: Hay {len(faltantes)} clientes en tu Excel nuevo que no tienen coordenadas en la base principal.")

            st.sidebar.header("Filtros de Visualización")
            vendedores_sel = st.sidebar.multiselect("Seleccionar Vendedores:", sorted(df_sec['Vendedor'].unique().tolist()), key="vend_sec")
            dias_sel = st.sidebar.multiselect("Seleccionar Días:", ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado'], default=[], key="dia_sec")

            if vendedores_sel and dias_sel:
                df_f = df_sec[(df_sec['Vendedor'].isin(vendedores_sel)) & (df_sec['Dia'].isin(dias_sel))].copy()
                
                if not df_f.empty:
                    centro = [df_f['Latitud'].mean(), df_f['Longitud'].mean()]
                    m = folium.Map(location=centro, zoom_start=14, tiles='cartodbpositron')

                    for _, row in df_f.iterrows():
                        coord = [row['Latitud'], row['Longitud']]
                        cod_cliente = row['Codigo_Cliente']
                        
                        promedio = row.get('Promedio_3Meses', 'NA')
                        tiene_compra = True
                        if pd.isna(promedio) or str(promedio).strip().upper() in ['NA', 'N/A', '', 'NAN']:
                            tiene_compra = False

                        if row['Dia'] == 'Lunes':
                            color_pin = 'darkred' if tiene_compra else 'red'
                        elif row['Dia'] == 'Martes':
                            color_pin = 'darkblue' if tiene_compra else 'lightblue'
                        elif row['Dia'] == 'Miercoles':
                            color_pin = 'darkgreen' if tiene_compra else 'lightgreen'
                        elif row['Dia'] == 'Jueves':
                            color_pin = 'brown' if tiene_compra else 'orange' 
                        elif row['Dia'] == 'Viernes':
                            color_pin = 'darkpurple' if tiene_compra else 'purple'
                        else:
                            color_pin = 'black'
                            
                        nombre_cliente = row.get('Cliente', 'Nombre no encontrado')
                        direccion = row.get('Direccion_Completa', 'N/A')
                            
                        html_popup = f"""
                        <div style="font-family: Arial, sans-serif; min-width: 250px; font-size: 12px;">
                            <h4 style="margin: 0 0 5px 0; color: #1565c0;">{nombre_cliente}</h4>
                            <table style="width: 100%; border-collapse: collapse;">
                                <tr><td><b>Código:</b></td><td>{row['Codigo_Cliente']}</td></tr>
                                <tr><td><b>Vendedor:</b></td><td>{row['Vendedor']}</td></tr>
                                <tr><td><b>Día de Visita:</b></td><td>{row['Dia']}</td></tr>
                                <tr><td colspan="2"><hr style="margin: 5px 0; border: 0; border-top: 1px solid #ccc;"></td></tr>
                                <tr><td><b>Canal:</b></td><td>{row.get('Canal', 'N/A')}</td></tr>
                                <tr><td><b>Prom. 3 Meses:</b></td><td>{row.get('Promedio_3Meses', 'N/A')}</td></tr>
                                <tr><td colspan="2"><hr style="margin: 5px 0; border: 0; border-top: 1px solid #ccc;"></td></tr>
                                <tr><td colspan="2"><b>Dirección:</b><br>{direccion}</td></tr>
                            </table>
                        </div>
                        """
                        
                        folium.Marker(
                            location=coord,
                            popup=folium.Popup(html_popup, max_width=350), 
                            tooltip=cod_cliente,
                            icon=folium.Icon(color=color_pin, icon='info-sign')
                        ).add_to(m)

                        # Muestra el código del cliente en texto negro fijo
                        folium.Marker(
                            location=coord,
                            icon=folium.DivIcon(
                                icon_size=(150,36),
                                icon_anchor=(7, 18),
                                html=f"""<div style="font-family: 'Arial Black'; color: #000; font-size: 10pt; font-weight: 900; text-shadow: 1px 1px 0 #FFF, -1px -1px 0 #FFF, 1px -1px 0 #FFF, -1px 1px 0 #FFF;">{cod_cliente}</div>"""
                            )
                        ).add_to(m)
                    
                    # Mapa a pantalla completa (sin columnas)
                    st_folium(m, width=1300, height=750, key="mapa_secundario_visor")

                else:
                    st.warning("No se encontraron registros que coincidan con los filtros y la geolocalización.")
            else:
                st.info("👈 Selecciona Vendedor y Día en el menú lateral.")
        else:
            st.error("Faltan archivos. Asegúrate de tener 'rutas_optimizadas.xlsx' y 'nuevos_clientes.xlsx' en la misma carpeta.")
