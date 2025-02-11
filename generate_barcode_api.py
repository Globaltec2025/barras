from flask import Flask, request, jsonify, render_template, send_file
import requests
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from pdf2image import convert_from_bytes
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

if __name__ == '__main__':
    app.run(debug=True)
