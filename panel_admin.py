import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os

# ... (Mantén tu configuración de login y session_state igual) ...

# --- FUNCIÓN PARA ACTUALIZAR EXCEL MAESTRO ---
def actualizar_base_maestra(df_maestro, df_nuevos):
    # Unimos manteniendo el maestro y actualizando solo si hay datos nuevos
    df_maestro = df_maestro.set_index('Codigo_Cliente')
    df_nuevos = df_nuevos.set_index('Codigo_Cliente')
    
    # Actualiza los datos existentes con la información nueva
    df_maestro.update(df_nuevos)
    
    # Agrega clientes que son totalmente nuevos
    df_final = pd.concat([df_maestro, df_nuevos[~df_nuevos.index.isin(df_maestro.index)]])
    return df_final.reset_index()

# ... (Dentro de tu lógica de la App) ...

    # ==========================================
    # PANEL PRINCIPAL (Ahora solo Visor)
    # ==========================================
    if modo == "Panel Principal (Rutas)":
        archivo_rutas = 'rutas_optimizadas.xlsx' 

        if os.path.exists(archivo_rutas):
            df = pd.read_excel(archivo_rutas)
            # ... (tus limpiezas de df) ...

            st.title("🗺️ Panel de Visualización de Rutas OKS")
            
            # FILTROS
            st.sidebar.header("Filtros")
            vendedores_sel = st.sidebar.multiselect("Seleccionar Vendedores:", sorted(df['Vendedor'].unique().tolist()))
            dias_sel = st.sidebar.multiselect("Seleccionar Días:", ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado'])

            if vendedores_sel and dias_sel:
                df_f = df[(df['Vendedor'].isin(vendedores_sel)) & (df['Dia'].isin(dias_sel))].copy()
                
                if not df_f.empty:
                    centro = [df_f['Latitud'].mean(), df_f['Longitud'].mean()]
                    m = folium.Map(location=centro, zoom_start=14, tiles='cartodbpositron')

                    # ... (Tu bucle de marcadores igual, pero SIN la lógica de st.session_state) ...
                    
                    # Mapa a pantalla completa
                    st_folium(m, width=1200, height=750)
                else:
                    st.warning("No se encontraron registros.")
            else:
                st.info("Selecciona Vendedor y Día en el menú lateral para visualizar.")

    # ==========================================
    # PANEL SECUNDARIO (Actualización de Clientes)
    # ==========================================
    elif modo == "Panel Secundario (Solo Visor)":
        st.title("🔄 Gestión y Actualización de Clientes")
        
        archivo_nuevo = 'nuevos_clientes.xlsx'
        archivo_maestro = 'rutas_optimizadas.xlsx'

        if st.button("Ejecutar Actualización del Maestro"):
            if os.path.exists(archivo_nuevo) and os.path.exists(archivo_maestro):
                df_m = pd.read_excel(archivo_maestro)
                df_n = pd.read_excel(archivo_nuevo)
                
                # Asegurar formatos
                df_m['Codigo_Cliente'] = df_m['Codigo_Cliente'].astype(str)
                df_n['Codigo_Cliente'] = df_n['Codigo_Cliente'].astype(str)
                
                df_actualizado = actualizar_base_maestra(df_m, df_n)
                df_actualizado.to_excel(archivo_maestro, index=False)
                st.success("¡Base de datos maestra actualizada correctamente!")
            else:
                st.error("Archivos no encontrados.")
