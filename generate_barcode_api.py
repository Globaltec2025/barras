from flask import Flask, request, jsonify, render_template, send_file
import requests
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.lib.utils import simpleSplit
import io
import os

app = Flask(__name__)
app.static_folder = 'static'

# Variable global para almacenar el token de acceso
token_acceso = None

def iniciar_sesion():
    global token_acceso
    if token_acceso:
        return token_acceso

    url_login = "https://globaltecsac.pe:8080/api/logingt"
    credenciales = {
        "username": "admin",
        "password": "gtec2022"
    }
    try:
        respuesta_login = requests.post(url_login, json=credenciales)
        if respuesta_login.status_code == 200:
            datos_login = respuesta_login.json()
            token_acceso = datos_login.get("token")
            return token_acceso
        else:
            print("Error al iniciar sesión:", respuesta_login.text)
    except requests.RequestException as e:
        print(f"Error de conexión al iniciar sesión: {e}")
    return None

def buscar_datos_externos(codigo):
    global token_acceso
    if not token_acceso:
        iniciar_sesion()

    if token_acceso:
        query = f"https://globaltecsac.pe:8080/api/items/search/*{codigo}*"
        headers = {"Authorization": f"token {token_acceso}"}
        
        print(f"Enviando solicitud a la API con el código: {codigo}")
        print(f"URL de la solicitud: {query}")
        
        try:
            respuesta_busqueda = requests.get(query, headers=headers)
            print(f"Respuesta de la API: {respuesta_busqueda.status_code}")
            if respuesta_busqueda.status_code == 200:
                datos = respuesta_busqueda.json()
                print(f"Datos recibidos: {datos}")
                
                if isinstance(datos, list) and datos:
                    marca = datos[0].get('marca', '')
                    medida = datos[0].get('medida', '')
                    print(f"Marca extraída: {marca}")
                    print(f"Medida extraída: {medida}")

                    return {
                        'description': datos[0].get('descripcion', ''),
                        'code': codigo,
                        'marca': marca,
                        'medida': medida
                    }
            else:
                print(f"Error al buscar el código: {respuesta_busqueda.text}")
        except requests.RequestException as e:
            print(f"Error al buscar código: {e}")
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/buscar')
def buscar():
    codigo = request.args.get('codigo')
    datos = buscar_datos_externos(codigo)
    if datos:
        return jsonify(datos)
    else:
        return jsonify({'error': 'No se encontraron datos para el código proporcionado.'})

@app.route('/generar_pdf', methods=['POST'])
def generar_pdf():
    data = request.json
    codigo = data.get('code')
    cantidad = int(data.get('quantity'))
    descripcion = data.get('description')
    marca = data.get('marca')
    medida = data.get('medida')

    # Crear el buffer para el archivo PDF
    buffer = io.BytesIO()
    custom_size = (96 * mm, 27 * mm)  # Ancho x Alto en milímetros
    p = canvas.Canvas(buffer, pagesize=custom_size)

    # Rutas de las imágenes
    logo_path = os.path.join(app.static_folder, 'imagenes/logo.jpg')
    new_code_path = os.path.join(app.static_folder, 'imagenes/new_code1.png')

    # Estilos de texto
    font_name = "Helvetica-Bold"
    code_font_size = 12  # Tamaño de letra para el código
    description_font_size = 7  # Tamaño de letra para la descripción
    marca_font_size = 7  # Tamaño de letra para la marca
    medida_font_size = 7  # Tamaño de letra para la medida
    max_width = 90 * mm  # Ancho máximo para dividir texto
    line_spacing = 2.7 * mm  # Espaciado entre líneas

    # Generar el PDF para la cantidad solicitada
    for _ in range(cantidad):
        # Dibujar imágenes
        p.drawImage(logo_path, 2, 18.5, width=9 * mm, height=11 * mm)
        p.drawImage(new_code_path, 30, 18.5, width=95 * mm, height=15 * mm)

        # Dibujar código
        p.setFont(font_name, code_font_size)  # Tamaño de letra ajustado para código
        p.drawString(37 * mm, 3 * mm, f"{codigo}")

        # Dibujar descripción
        p.setFont(font_name, description_font_size)  # Tamaño de letra ajustado para descripción
        lines = simpleSplit(descripcion, font_name, description_font_size, max_width)

        y_position = 24.5 * mm
        for line in lines:
            p.drawString(4 * mm, y_position, line)
            y_position -= line_spacing

        # Dibujar marca
        p.setFont(font_name, marca_font_size)  # Tamaño de letra para marca
        p.drawString(80 * mm, 0.2 * mm, f"{marca}")

        # Dibujar medida
        p.setFont(font_name, medida_font_size)  # Tamaño de letra para medida
        p.drawString(2 * mm, 0.2 * mm, f"{medida}")

        # Crear nueva página
        p.showPage()

    # Guardar y devolver el archivo PDF
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='codigo_sap.pdf', mimetype='application/pdf')


if __name__ == '__main__':
    app.run(debug=True)