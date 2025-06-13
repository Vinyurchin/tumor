import os
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
from processing.tumor_detector import TumorDetector
from processing.image_processor import generate_visualizations
import sys
import numpy
import scipy
import tensorflow

print('Python version:', sys.version)
print('Numpy version:', numpy.__version__)
print('Scipy version:', scipy.__version__)
print('Tensorflow version:', tensorflow.__version__)

app = Flask(__name__)

# Configuración
UPLOAD_FOLDER = 'static/uploads'
RESULT_FOLDER = 'static/results'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'dcm'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER

# Crear directorios si no existen
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Procesamiento de la imagen
            detector = TumorDetector()
            result = detector.detect_tumor(filepath)
            
            # Generar visualizaciones
            base_name = os.path.splitext(filename)[0]
            result_images = generate_visualizations(
                filepath, 
                app.config['RESULT_FOLDER'], 
                base_name
            )
            
            return render_template('index.html',
                                original_image=filepath,
                                result_images=result_images,
                                has_tumor=result['has_tumor'],
                                confidence=f"{result['confidence']:.2f}%")
    
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def api_upload():
    if 'file' not in request.files:
        return {'result': 'No file provided'}, 400
    file = request.files['file']
    if file.filename == '':
        return {'result': 'No file selected'}, 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        # Procesamiento de la imagen
        detector = TumorDetector()
        result = detector.detect_tumor(filepath)
        # Generar visualizaciones
        base_name = os.path.splitext(filename)[0]
        result_images = generate_visualizations(
            filepath,
            app.config['RESULT_FOLDER'],
            base_name
        )
        # Convertir imagen de resultado a base64 (ejemplo: original)
        import base64
        result_img_path = os.path.join('static', result_images['original'])
        with open(result_img_path, 'rb') as img_file:
            img_base64 = base64.b64encode(img_file.read()).decode('utf-8')
        return {
            'result': 'Tumor Detected' if result['has_tumor'] else 'No Tumor',
            'confidence': f"{result['confidence']:.2f}%",
            'image_base64': img_base64
        }
    return {'result': 'Invalid file'}, 400

@app.route('/analyze', methods=['POST'])
def analyze_emotion():
    data = request.get_json()
    if not data or 'image_base64' not in data:
        return {'error': 'No image_base64 provided'}, 400
    # Decodificar imagen base64 y guardar temporalmente
    import base64, tempfile
    img_data = base64.b64decode(data['image_base64'])
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_img:
        temp_img.write(img_data)
        temp_img_path = temp_img.name
    # Aquí deberías poner tu lógica real de análisis de emociones
    # Por ahora, devolvemos un mock
    emotion = 'Feliz'  # Mock
    # Puedes devolver imágenes procesadas en base64 si lo deseas
    # Ejemplo: devolver la misma imagen como keypoint_image
    with open(temp_img_path, 'rb') as img_file:
        keypoint_image = base64.b64encode(img_file.read()).decode('utf-8')
    # Limpieza del archivo temporal
    os.remove(temp_img_path)
    return {
        'emotion': emotion,
        'keypoint_image': keypoint_image,
        'transformations_image': keypoint_image
    }

if __name__ == '__main__':
    app.run(debug=True)