from flask import Flask, jsonify, request 

app = Flask(__name__)

# Ruta principal que devuelve un mensaje simple
@app.route('/', methods=['GET']) 
def home(): 
    return jsonify(message="Bienvenido a la API")
    
# Ruta que recibe un nombre y devuelve un saludo personalizado
@app.route('/greet', methods=['POST']) 
def greet(): 
    data = request.get_json() 
    name = data.get('name', 'Invitado') 
    return jsonify(message=f"¡Hola, {name}!")
 
if __name__ == '__main__':
 # Solo se necesita una línea para ejecutar la app
    app.run(host='0.0.0.0', port=8080, debug=True)