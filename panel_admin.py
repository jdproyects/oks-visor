import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os

def arreglar_coord(val, limite):
    if pd.isna(val) or val == '':
        return None
    try:
        v = str(val).strip()
        # Si el Excel trajo separador de miles y coma decimal (ej: -34.567,89)
        if '.' in v and ',' in v:
            v = v.replace('.', '').replace(',', '.')
        else:
            v = v.replace(',', '.')
        
        num = float(v)
        
        # Si el número es gigante porque perdió el decimal, lo dividimos hasta que sea real
        while abs(num) > limite and num != 0:
            num = num / 10.0
            
        return num
    except:
        return None
        
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
    modo = st.sidebar.radio("Navegación:", [
        "Panel Principal (Rutas)", 
        "Panel Gestión (Actualizar Clientes)", 
        "Panel No Compradores"
    ])
    st.sidebar.markdown("---")

    if st.sidebar.button("Cerrar Sesión"):
        st.session_state['logueado'] = False
        st.rerun()

    # ==========================================
    # LISTA DE COLORES PARA LOS VENDEDORES
    # ==========================================
    colores_disponibles = [
        'red', 'blue', 'green', 'purple', 'orange', 'darkred', 
        'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue', 
        'darkpurple', 'pink', 'lightblue', 'lightgreen', 'black', 'gray', 'lightgray'
    ]

    # ==========================================
    # PANEL PRINCIPAL 
    # ==========================================
    if modo == "Panel Principal (Rutas)":
        archivo_rutas = 'rutas_optimizadas.xlsx' 

        if os.path.exists(archivo_rutas):
            df = pd.read_excel(archivo_rutas)
            df.columns = df.columns.str.strip()
            df['Codigo_Cliente'] = df['Codigo_Cliente'].astype(str).str.replace('.0', '', regex=False).str.strip()
            
            # --- LIMPIEZA DE DATOS ---
            df['Vendedor'] = df['Vendedor'].astype(str).str.strip()
            df['Dia'] = df['Dia'].astype(str).str.strip()
            
            # Reemplazar comas por puntos y forzar formato numérico de forma inteligente
            df['Latitud'] = df['Latitud'].apply(lambda x: arreglar_coord(x, 90))
            df['Longitud'] = df['Longitud'].apply(lambda x: arreglar_coord(x, 180))

            # Descartamos los clientes sin coordenadas válidas
            df = df.dropna(subset=['Latitud', 'Longitud'])
            
            # --- ASIGNACIÓN DINÁMICA DE COLORES POR VENDEDOR ---
            vendedores_unicos = sorted(df['Vendedor'].dropna().unique().tolist())
            mapa_colores = {vendedor: colores_disponibles[i % len(colores_disponibles)] for i, vendedor in enumerate(vendedores_unicos)}

            st.title("🗺️ Panel de Enrutamiento Interactivo OKS")
            st.sidebar.header("Filtros")
            vendedores_sel = st.sidebar.multiselect("Seleccionar Vendedores:", vendedores_unicos)
            dias_sel = st.sidebar.multiselect("Seleccionar Días:", ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado'], default=[])

            if vendedores_sel and dias_sel:
                df_f = df[(df['Vendedor'].isin(vendedores_sel)) & (df['Dia'].isin(dias_sel))].copy()
                
                if not df_f.empty:
                    centro = [df_f['Latitud'].mean(), df_f['Longitud'].mean()]
                    m = folium.Map(location=centro, zoom_start=14, tiles='OpenStreetMap')

                    for _, row in df_f.iterrows():
                        coord = [row['Latitud'], row['Longitud']]
                        cod_cliente = row['Codigo_Cliente']
                        vendedor_row = row['Vendedor']
                        
                        color_pin = mapa_colores.get(vendedor_row, 'gray')
                            
                        html_popup = f"""
                        <div style="font-family: Arial, sans-serif; min-width: 250px; font-size: 12px;">
                            <h4 style="margin: 0 0 5px 0; color: #d32f2f;">{row['Cliente']}</h4>
                            <table style="width: 100%; border-collapse: collapse;">
                                <tr><td><b>Código:</b></td><td>{row['Codigo_Cliente']}</td></tr>
                                <tr><td><b>Vendedor:</b></td><td>{vendedor_row}</td></tr>
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
    # PANEL GESTIÓN 
    # ==========================================
    elif modo == "Panel Gestión (Actualizar Clientes)":
        st.title("🔄 Reemplazo de la Base de Datos de Clientes")
        st.markdown("""
        ⚠️ **ATENCIÓN: Modo de Reemplazo Total.** Al subir un archivo nuevo, **se borrará toda la información anterior**. El mapa de rutas mostrará ÚNICAMENTE los clientes de este nuevo archivo.
        """)

        archivo_cargado = st.file_uploader("📂 Selecciona o arrastra tu archivo Excel (.xlsx)", type=["xlsx"])

        if archivo_cargado is not None:
            try:
                df_n = pd.read_excel(archivo_cargado)
                df_n.columns = df_n.columns.str.strip()

                st.subheader("👀 Vista previa de los nuevos datos:")
                st.dataframe(df_n.head(10)) 

                if st.button("🚀 Reemplazar Base de Datos"):
                    archivo_maestro = 'rutas_optimizadas.xlsx'

                    df_n['Codigo_Cliente'] = df_n['Codigo_Cliente'].astype(str).str.replace('.0', '', regex=False).str.strip()

                    columnas_requeridas = ['Codigo_Cliente', 'Cliente', 'Latitud', 'Longitud', 'Vendedor', 'Dia', 'Direccion_Completa']
                    columnas_faltantes = [col for col in columnas_requeridas if col not in df_n.columns]

                    if columnas_faltantes:
                        st.error(f"❌ El archivo que subiste no tiene todas las columnas necesarias. Faltan: {', '.join(columnas_faltantes)}")
                    else:
                        df_n.to_excel(archivo_maestro, index=False)
                        st.success("🎉 ¡Base de datos reemplazada con éxito! Ya podés ir al 'Panel Principal (Rutas)' y ver únicamente a tus nuevos clientes.")
            
            except Exception as e:
                st.error(f"❌ Ocurrió un error al procesar el archivo: {e}")
        else:
            st.info("💡 Por favor, subí un archivo Excel para habilitar el botón de reemplazo.")

    # ==========================================
    # PANEL NO COMPRADORES
    # ==========================================
    elif modo == "Panel No Compradores":
        archivo_no_compradores = 'no_compradores.xlsx' 
        archivo_coordenadas = 'clientes_prueba.xlsx' 

        st.title("🚫 Panel de Clientes No Compradores")
        st.markdown("Muestra la ubicación de aquellos clientes que requieren seguimiento, rescatando las coordenadas automáticamente desde tu base de clientes de prueba.")

        if os.path.exists(archivo_no_compradores):
            if os.path.exists(archivo_coordenadas):
                df_nc = pd.read_excel(archivo_no_compradores)
                df_nc.columns = df_nc.columns.str.strip()
                df_nc['Codigo_Cliente'] = df_nc['Codigo_Cliente'].astype(str).str.replace('.0', '', regex=False).str.strip()
                
                df_coords = pd.read_excel(archivo_coordenadas)
                df_coords.columns = df_coords.columns.str.strip()
                df_coords['Codigo_Cliente'] = df_coords['Codigo_Cliente'].astype(str).str.replace('.0', '', regex=False).str.strip()
                
                if 'Latitud' not in df_coords.columns or 'Longitud' not in df_coords.columns:
                    st.error("❌ El archivo 'clientes_prueba.xlsx' no tiene las columnas 'Latitud' y 'Longitud'. Por favor, verifica el archivo.")
                else:
                    df_coords['Latitud'] = pd.to_numeric(df_coords['Latitud'].astype(str).str.replace(',', '.'), errors='coerce')
                    df_coords['Longitud'] = pd.to_numeric(df_coords['Longitud'].astype(str).str.replace(',', '.'), errors='coerce')
                    
                    columnas_extraer = ['Codigo_Cliente', 'Latitud', 'Longitud']
                    
                    if 'Cliente' not in df_nc.columns and 'Cliente' in df_coords.columns:
                        columnas_extraer.append('Cliente')
                    if 'Direccion_Completa' not in df_nc.columns and 'Direccion_Completa' in df_coords.columns:
                        columnas_extraer.append('Direccion_Completa')
                        
                    df_coords_limpio = df_coords[columnas_extraer].drop_duplicates(subset=['Codigo_Cliente'])
                    
                    df_nc = pd.merge(df_nc, df_coords_limpio, on='Codigo_Cliente', how='left')

                    clientes_sin_coord = df_nc['Latitud'].isna().sum()
                    if clientes_sin_coord > 0:
                        st.warning(f"⚠️ Atención: {clientes_sin_coord} cliente(s) de tu lista no se encontraron en 'clientes_prueba.xlsx' o no tenían coordenadas válidas, por lo que no aparecerán en el mapa.") 
                    
                    df_nc = df_nc.dropna(subset=['Latitud', 'Longitud'])

                    columna_vendedor = 'Vendedor' if 'Vendedor' in df_nc.columns else df_nc.columns[2]
                    columna_dia = 'Dia' if 'Dia' in df_nc.columns else ('dia visita' if 'dia visita' in df_nc.columns else df_nc.columns[1])

                    df_nc[columna_vendedor] = df_nc[columna_vendedor].astype(str).str.strip()

                    vendedores_nc_unicos = sorted(df_nc[columna_vendedor].dropna().unique().tolist())
                    mapa_colores_nc = {vendedor: colores_disponibles[i % len(colores_disponibles)] for i, vendedor in enumerate(vendedores_nc_unicos)}

                    st.sidebar.header("Filtros No Compradores")
                    vendedores_nc = st.sidebar.multiselect("Seleccionar Vendedores:", vendedores_nc_unicos, key="vend_nc")
                    dias_unicos = sorted(df_nc[columna_dia].dropna().unique().tolist())
                    dias_nc = st.sidebar.multiselect("Seleccionar Días:", dias_unicos, default=[], key="dia_nc")

                    if vendedores_nc and dias_nc:
                        df_nc_f = df_nc[(df_nc[columna_vendedor].isin(vendedores_nc)) & (df_nc[columna_dia].isin(dias_nc))].copy()
                        
                        if not df_nc_f.empty:
                            centro = [df_nc_f['Latitud'].mean(), df_nc_f['Longitud'].mean()]
                            m_nc = folium.Map(location=centro, zoom_start=14, tiles='OpenStreetMap')

                            for _, row in df_nc_f.iterrows():
                                coord = [row['Latitud'], row['Longitud']]
                                cod_cliente = row['Codigo_Cliente']
                                nombre_cliente = row.get('Cliente', 'Nombre no disponible')
                                dir_cliente = row.get('Direccion_Completa', 'Dirección no disponible')
                                vendedor_actual = row[columna_vendedor]
                                
                                color_pin = mapa_colores_nc.get(vendedor_actual, 'gray')
                                    
                                html_popup = f"""
                                <div style="font-family: Arial, sans-serif; min-width: 250px; font-size: 12px;">
                                    <h4 style="margin: 0 0 5px 0; color: #555555;">{nombre_cliente}</h4>
                                    <table style="width: 100%; border-collapse: collapse;">
                                        <tr><td><b>Código:</b></td><td>{row['Codigo_Cliente']}</td></tr>
                                        <tr><td><b>Vendedor:</b></td><td>{vendedor_actual}</td></tr>
                                        <tr><td><b>Día:</b></td><td>{row[columna_dia]}</td></tr>
                                        <tr><td colspan="2"><hr style="margin: 5px 0;"></td></tr>
                                        <tr><td colspan="2"><b>Dirección:</b><br>{dir_cliente}</td></tr>
                                    </table>
                                </div>
                                """
                                
                                folium.Marker(
                                    location=coord,
                                    popup=folium.Popup(html_popup, max_width=350), 
                                    tooltip=cod_cliente,
                                    icon=folium.Icon(color=color_pin, icon='remove-circle', prefix='glyphicon')
                                ).add_to(m_nc)

                                folium.Marker(
                                    location=coord,
                                    icon=folium.DivIcon(
                                        icon_size=(150,36), icon_anchor=(7, 18),
                                        html=f"""<div style="font-family: 'Arial Black'; color: #000; font-size: 10pt; font-weight: 900; text-shadow: 1px 1px 0 #FFF, -1px -1px 0 #FFF;">{cod_cliente}</div>"""
                                    )
                                ).add_to(m_nc)
                            
                            st_folium(m_nc, width=1200, height=750)
                        else:
                            st.warning("No se encontraron registros de no compradores para estos filtros.")
                    else:
                        st.info("👈 Selecciona Vendedor y Día en el menú lateral para ver el mapa.")
            else:
                st.error("❌ No se encontró el archivo 'clientes_prueba.xlsx'. Recuerda subirlo a GitHub para que Streamlit lo pueda leer.")
        else:
            st.warning("⚠️ No se encontró el archivo 'no_compradores.xlsx'. Por favor, asegúrate de guardarlo en la misma carpeta que este script.")

