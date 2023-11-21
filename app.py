from flask import Flask, render_template
import pandas as pd
import os
import sys

app = Flask(__name__)

# Ruta principal del programa
@app.route('/')
def index():
    # Obtén la ruta del directorio donde se encuentra este script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construye la ruta al archivo Excel, manejando el caso del entorno temporal (_MEIxxxxxx)
    if getattr(sys, 'frozen', False):
        # Se está ejecutando como ejecutable empaquetado
        excel_file_path = os.path.join(os.path.dirname(sys.executable), 'tu_archivo_excel.xlsx')
    else:
        # No se está ejecutando como ejecutable empaquetado
        excel_file_path = os.path.join(script_dir, 'tu_archivo_excel.xlsx')

    # Verifica si el archivo existe antes de intentar abrirlo
    if not os.path.exists(excel_file_path):
        return f"Error: El archivo Excel no se encuentra en la ruta especificada: {excel_file_path}"


    # Resto del código para leer y procesar el archivo Excel
    try:
        # Lee el archivo Excel
        df = pd.read_excel(excel_file_path)

        # Elimina filas con valores nulos en columnas relevantes
        df = df.dropna(subset=['DEF', 'TOTALES'])

        # Verifica los nombres exactos de las columnas en tu archivo Excel
        required_columns = ['Numero', 'NOMBRE', 'CEN', 'ALA', 'DEF', 'CTL', 'TOTALES']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            return f"Error: Las siguientes columnas no se encontraron en el archivo Excel: {', '.join(missing_columns)}"

        # Encuentra los 4 mejores en la columna CEN con CTL >= 8
        top_cen = df[df['CTL'] >= 8].nlargest(4, 'CEN')[['Numero', 'NOMBRE', 'CEN']]

        # Crea una nueva columna 'Posicion' basada en el valor mayor entre ALA y DEF
        df['Posicion'] = df.apply(lambda row: 'ALA' if row['ALA'] > row['DEF'] else 'DEF', axis=1)

        # Encuentra los 8 mejores en la columna ALA que no estén en CEN
        top_ala = df[(df['Posicion'] == 'ALA') & ~df['Numero'].isin(top_cen['Numero'])].nlargest(8, 'ALA')[['Numero', 'NOMBRE', 'ALA', 'TOTALES']]

        # Encuentra los 8 mejores en la columna DEF que no estén en CEN
        top_def = df[(df['Posicion'] == 'DEF') & ~df['Numero'].isin(top_cen['Numero'])].nlargest(8, 'DEF')[['Numero', 'NOMBRE', 'DEF', 'TOTALES']]

        # Resto del código para procesar las reservas y manejar empates

        # Encuentra las reservas para ALA (los 2 mejores que no están en ALA, CEN ni DEF)
        reservas_ala = df[(df['Posicion'] == 'ALA') & ~df['Numero'].isin(top_cen['Numero']) & ~df['Numero'].isin(top_ala['Numero']) & ~df['Numero'].isin(top_def['Numero'])].nlargest(2, 'ALA')[['Numero', 'NOMBRE', 'ALA', 'TOTALES']]

        # Encuentra las reservas para DEF (los 2 mejores que no están en ALA, CEN ni DEF)
        reservas_def = df[(df['Posicion'] == 'DEF') & ~df['Numero'].isin(top_cen['Numero']) & ~df['Numero'].isin(top_ala['Numero']) & ~df['Numero'].isin(top_def['Numero'])].nlargest(2, 'DEF')[['Numero', 'NOMBRE', 'DEF', 'TOTALES']]

        # Verifica si un reserva tiene más totales que un top y la diferencia en DEF o ALA es menor a 0.75, luego reemplaza el top por el reserva
        for reserva, top, columna in zip([reservas_ala, reservas_def], [top_ala, top_def], ['ALA', 'DEF']):
            for index, row in reserva.iterrows():
                for top_index, top_row in top.iterrows():
                    if row['TOTALES'] > top_row['TOTALES'] and abs(row[columna] - top_row[columna]) < 0.75:
                        # Encuentra el siguiente jugador con más totales
                        siguiente_mejor = df[(df['Posicion'] == columna) & ~df['Numero'].isin(top_cen['Numero']) & ~df['Numero'].isin(top_ala['Numero']) & ~df['Numero'].isin(top_def['Numero']) & (df['Numero'] != row['Numero'])].nlargest(1, 'TOTALES')
                        
                        # Actualiza el top con el siguiente mejor jugador
                        top.at[top_index, 'Numero'] = siguiente_mejor['Numero'].values[0]
                        top.at[top_index, 'NOMBRE'] = siguiente_mejor['NOMBRE'].values[0]
                        top.at[top_index, columna] = siguiente_mejor[columna].values[0]
                        top.at[top_index, 'TOTALES'] = siguiente_mejor['TOTALES'].values[0]


        return render_template('index.html', top_cen=top_cen.values.tolist(), top_ala=top_ala.values.tolist(),
                               top_def=top_def.values.tolist(), reservas_ala=reservas_ala.values.tolist(),
                               reservas_def=reservas_def.values.tolist())
    except Exception as e:
        return f"Error al procesar el archivo Excel: {str(e)}"


if __name__ == '__main__':
    # Ejecuta la aplicación Flask con el modo de depuración activado
    app.run(debug=True)
