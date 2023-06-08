from flask import Flask, request, render_template
import requests
import json

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            # Call your API to extract data from the PDF
            # Assuming the API takes the file as multipart/form-data
            #response = requests.post('https://your-api-url.com', files={'file': file.read()})
            response = json.JSONEncoder("{ data: 'success' }")
            
            # Get the extracted data from the API response
            data = response.json()

            # Render a template with the extracted data
            return render_template('result.html', data=data)

    # If the method is GET, render the file upload form
    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True)
