import argparse
from flask import Flask, request, url_for, abort, g, send_file, send_from_directory, safe_join
import sys, getopt, os
from flask import jsonify
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
import torch
import ntpath
import os.path
from os import path


app = Flask(__name__)

ALLOWED_EXTENSIONS = ['.png', '.jpg']
PATH_MAYAPY = "/Applications/Autodesk/maya2019/Maya.app/Contents/bin/mayapy"
PATH_RIGME = "/Users/jasbakshi/Documents/GitHub/RigMe"

@app.errorhandler(Exception)
def server_error(err):
    app.logger.exception(err)
    return err, 500

@app.route('/')
def home_endpoint():
    return 'Hello World!'

@app.route('/api/convert_picture', methods=['POST'])
def main():
	if request.method == 'POST':
		try:
			data_json = request.get_json()
			image_path = data_json['image_path']
			res = data_json['resolution']
			if path.exists(image_path) != True:
					raise Exception("Please enter a valid image path")
			base = ntpath.basename(image_path)
			filename, file_extension = os.path.splitext(base)
			print(filename)
			print(file_extension)
			print(image_path)
			if file_extension in ALLOWED_EXTENSIONS:
				clean_image_path = clean_background_Image(image_path, filename)
				print(clean_image_path)
				if path.exists(clean_image_path) != True:
					raise Exception("Cleaning Background of Image incomplete")
				print('converting rect')
				rect_path = rect_Image(clean_image_path, filename)
				if path.exists(rect_path) != True:
					raise Exception("Rect text file does not exist")
				print(rect_path)
				print('converting to obj')
				output = "./output/" + filename
				print(output)
				#pre_process_image(image_path)
				t = convert_to_3d(output, output, res)
				print(t)
				obj_file = "result_" + filename + "_clean_" + res
				print(output + "/" + obj_file + "_remesh.obj")
				print(obj_file)
				print('predicting to 3d rect')
				obj_rect_convert(output, obj_file)
				print('converting to fbx')
				fbx_convert(obj_file, output)
				return 'Success'
		except Exception as e:
			return str(e)

def convert_to_3d(file_dir, output, res):
	try:
		os.system("python ./pifuhd/apps/simple_test.py -o " + output + " -c ./pifuhd/checkpoints/pifuhd.pt -r " + res + " --use_rect -i " + file_dir)
		return True
	except:
		return False


def clean_background_Image(file_dir, file_name):
	try:
		output = "./output/" + file_name + "/" + file_name + "_clean.png"
		print(output)
		os.system("python3 ./image_background_remove_tool/main.py -o " + output + " -m u2net -prep bbd-fastrcnn -postp rtb-bnb -i " + file_dir)
		return output
	except:
		return False

def rect_Image(file_dir, file_name):
	try:
		os.system("python ./lightweight_human_pose_estimation/process_image.py --input " + file_dir)
		return True
	except Exception as e:
		print(e)
		return False

def obj_rect_convert(file_dir, obj_file_name):
	try:
		print(file_dir,obj_file_name)
		os.system("python ./RigNet_master/quick_start.py -i " + file_dir + "/pifuhd_final/recon/ -o " + obj_file_name)
		return True
	except Exception as e:
		print(e)
		return False

def fbx_convert(model_id, file_dir):
	try:
		print(model_id)
		os.system(PATH_MAYAPY + " ./RigNet_master/maya_save_fbx.py --id " + model_id + " -i + " + file_dir + "/pifuhd_final/recon")
		return True
	except Exception as e:
		print(e)
		return False

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)#beginning once only
    app.run(host='0.0.0.0', port=80)