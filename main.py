from flask import Flask, request, send_file, jsonify
from rembg import remove
from PIL import Image
import io
import os
import uuid
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Create uploads and results directories if they don't exist
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
RESULT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return '''
    <html>
        <head>
            <title>Background Removal API</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    line-height: 1.6;
                }
                h1 {
                    color: #333;
                    border-bottom: 1px solid #ddd;
                    padding-bottom: 10px;
                }
                pre {
                    background-color: #f5f5f5;
                    padding: 15px;
                    border-radius: 5px;
                    overflow-x: auto;
                }
                .endpoint {
                    margin-top: 30px;
                }
                form {
                    margin-top: 20px;
                    padding: 20px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                }
                input[type="file"] {
                    margin: 10px 0;
                }
                input[type="submit"] {
                    background-color: #4CAF50;
                    color: white;
                    padding: 10px 15px;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                }
                input[type="submit"]:hover {
                    background-color: #45a049;
                }
            </style>
        </head>
        <body>
            <h1>Background Removal API</h1>
            <p>This API removes backgrounds from images using the rembg library.</p>
            
            <div class="endpoint">
                <h2>API Endpoint</h2>
                <p>Send a POST request to <code>/api/remove-background</code> with an image file.</p>
                <pre>
curl -X POST -F "image=@your_image.jpg" https://your-domain.com/api/remove-background -o result.png
                </pre>
            </div>
            
            <div class="endpoint">
                <h2>Try it out</h2>
                <form action="/api/remove-background" method="post" enctype="multipart/form-data">
                    <p>Select an image to remove the background:</p>
                    <input type="file" name="image" accept="image/*" required>
                    <br>
                    <input type="submit" value="Remove Background">
                </form>
            </div>
        </body>
    </html>
    '''

@app.route('/api/remove-background', methods=['POST'])
def remove_background():
    try:
        # Check if image file is present in request
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        
        # Check if filename is empty
        if file.filename == '':
            return jsonify({'error': 'No image selected'}), 400
        
        # Generate unique filenames
        input_filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
        output_filename = str(uuid.uuid4()) + '.png'
        
        input_path = os.path.join(UPLOAD_FOLDER, input_filename)
        output_path = os.path.join(RESULT_FOLDER, output_filename)
        
        # Save the input image
        file.save(input_path)
        logger.info(f"Saved input image to {input_path}")
        
        # Process the image with rembg
        with open(input_path, 'rb') as input_file:
            input_data = input_file.read()
            
        # Remove background
        output_data = remove(input_data)
        logger.info("Background removed successfully")
        
        # Save the output image
        with open(output_path, 'wb') as output_file:
            output_file.write(output_data)
        logger.info(f"Saved output image to {output_path}")
        
        # Check if the request is from browser or API
        if request.headers.get('Accept', '').find('text/html') != -1:
            # Return image directly for browser requests
            return send_file(output_path, mimetype='image/png')
        else:
            # Return image file for API requests
            return send_file(output_path, mimetype='image/png', 
                            as_attachment=True, download_name='result.png')
            
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        # Clean up temporary files (optional)
        # Uncomment if you want to delete files after processing
        # if os.path.exists(input_path):
        #     os.remove(input_path)
        # if os.path.exists(output_path):
        #     os.remove(output_path)
        pass

if __name__ == '__main__':
    # Run the app on 0.0.0.0 to make it accessible externally
    app.run(host='0.0.0.0', port=5000, debug=False)
