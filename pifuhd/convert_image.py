from apps.recon import reconWrapper
#from lightweight.parse_image import pre_process_image
import argparse
from flask import Flask, request, url_for, abort, g, send_file, send_from_directory, safe_join
import sys, getopt, os
from flask import jsonify
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)


app = Flask(__name__)

ALLOWED_EXTENSIONS = ['png', 'jpg']

@app.route('/')
def home_endpoint():
    return 'Hello World!'

@app.route('/api/convert_picture', methods=['POST'])
def main():
	if request.method == 'POST':
		try:
			data_json = request.get_json()
			image_path = data_json['image_path']
			image_dir = os.path.dirname(image_path)
			#pre_process_image(image_path)
			t =convert_to_3d(image_dir)
			print(t)
			return 'Success'
		except Exception as e:
			return e

def convert_to_3d(file_dir):
	os.system("python -m apps.simple_test -r 128 -i " + file_dir)
	
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)#beginning once only
    app.run(host='0.0.0.0', port=80)