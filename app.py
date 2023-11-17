# EJECUTAR PROGRAMA CON python app.py EN F:\xampp\htdocs\ALINEACION-MZ-HOCKEY>
# ABRIR SERVIDOR http://127.0.0.1:5000/
# CARGAR ARCHIVO EXCEL PARA QUE FUNCIENE ACTUALIZADO

from flask import Flask, render_template
import pandas as pd

app = Flask(__name__)

# Ruta principal del programa
@app.route('/')
def index():
    # Lee el archivo Excel
    df = pd.read_excel('tu_archivo_excel.xlsx')

    # Verifica los nombres exactos de las columnas en tu archivo Excel
    required_columns = ['Numero', 'NOMBRE', 'CEN', 'ALA', 'DEF', 'CTL']
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        return f"Error: Las siguientes columnas no se encontraron en el archivo Excel: {', '.join(missing_columns)}"

    # Encuentra los 4 mejores en la columna CEN con CTL >= 8
    top_cen = df[df['CTL'] >= 8].nlargest(4, 'CEN')[['Numero', 'NOMBRE', 'CEN']]

    # Crea una nueva columna 'Posicion' basada en el valor mayor entre ALA y DEF
    df['Posicion'] = df.apply(lambda row: 'ALA' if row['ALA'] > row['DEF'] else 'DEF', axis=1)

    # Encuentra los 8 mejores en la columna ALA que no estén en CEN
    top_ala = df[(df['Posicion'] == 'ALA') & ~df['Numero'].isin(top_cen['Numero'])].nlargest(8, 'ALA')[['Numero', 'NOMBRE', 'ALA']]

    # Encuentra los 8 mejores en la columna DEF que no estén en CEN
    top_def = df[(df['Posicion'] == 'DEF') & ~df['Numero'].isin(top_cen['Numero'])].nlargest(8, 'DEF')[['Numero', 'NOMBRE', 'DEF']]

    # Encuentra las reservas para ALA (los 2 mejores que no están en ALA, CEN ni DEF)
    reservas_ala = df[(df['Posicion'] == 'ALA') & ~df['Numero'].isin(top_cen['Numero']) & ~df['Numero'].isin(top_ala['Numero']) & ~df['Numero'].isin(top_def['Numero'])].nlargest(2, 'ALA')[['Numero', 'NOMBRE', 'ALA']]

    # Encuentra las reservas para DEF (los 2 mejores que no están en ALA, CEN ni DEF)
    reservas_def = df[(df['Posicion'] == 'DEF') & ~df['Numero'].isin(top_cen['Numero']) & ~df['Numero'].isin(top_ala['Numero']) & ~df['Numero'].isin(top_def['Numero'])].nlargest(2, 'DEF')[['Numero', 'NOMBRE', 'DEF']]

    return render_template('index.html', top_cen=top_cen.values.tolist(), top_ala=top_ala.values.tolist(),
                           top_def=top_def.values.tolist(), reservas_ala=reservas_ala.values.tolist(),
                           reservas_def=reservas_def.values.tolist())

if __name__ == '__main__':
    app.run(debug=True)
