import argparse
from flask import Flask, request, url_for, abort, g, send_file, send_from_directory, safe_join
import sys, getopt, os
from flask import jsonify
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
from werkzeug.utils import secure_filename

import torch
import ntpath
import os
import os.path
from os import path
import boto3
import uuid 
import shutil

from botocore.exceptions import ClientError
from typing import Optional


app = Flask(__name__)

ALLOWED_EXTENSIONS = ['.png', '.jpg']
PATH_MAYAPY = "usr/autodesk/maya2020/bin/mayapy"
PATH_RIGME = "/Users/jasbakshi/Documents/GitHub/RigMe"

# Define the configuration rules
cors_configuration = {
    'CORSRules': [{
        'AllowedHeaders': ['Authorization'],
        'AllowedMethods': ['GET','PUT'],
        'AllowedOrigins': ['*'], # replace with https://*.rigme.io once ssl works
        'ExposeHeaders': ['GET'],
        'MaxAgeSeconds': 3000
    }]
}


s3 = boto3.resource('s3',aws_access_key_id="AKIAJE2BGFS3XAF4PBYA",
             aws_secret_access_key= "***REMOVED***", region_name='us-west-2')
s3_client = boto3.client('s3',aws_access_key_id="AKIAJE2BGFS3XAF4PBYA",
             aws_secret_access_key= "***REMOVED***", region_name='us-west-2')
s3_client.put_bucket_cors(Bucket='rigme-09-2020',
                   CORSConfiguration=cors_configuration)

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
			ID = str(uuid.uuid1())
			output = "./output/" + ID
			os.makedirs(output)
			data_json = request.get_json()
			image_path = request.files['file']
			filename = secure_filename(image_path.filename)
			img = os.path.join(output, filename)
			image_path.save(img)
			res = request.form.get('resolution')
			print(res)
			if path.exists(img) != True:
					raise Exception("Please enter a valid image path")
			base = ntpath.basename(img)
			filename, file_extension = os.path.splitext(base)
			print(filename)
			print(file_extension)
			print(img)
			#Generate random ID
			
			if file_extension in ALLOWED_EXTENSIONS:
				clean_image_path = clean_background_Image(img, filename, ID)
				print(clean_image_path)
				if path.exists(clean_image_path) != True:
					raise Exception("Cleaning Background of Image incomplete")
				print('converting rect')
				rect_path = rect_Image(clean_image_path, filename)
				if path.exists(rect_path) != True:
					raise Exception("Rect text file does not exist")
				print(rect_path)
				print('converting to obj')
				print(output)
				#pre_process_image(image_path)
				#t = convert_to_3d(output, output, res)
				#print(t)
				obj_file = "result_" + filename + "_clean_" + res
				print(output + "/" + obj_file + "_remesh.obj")
				print(obj_file)
				print('predicting to 3d rect')
				#obj_rect_convert(output, obj_file)
				print('converting to fbx')
				#fbx_convert(obj_file, output)
			    
				##AWS Upload

				for root, dirs, files in os.walk(output, topdown=False):
					for name in files:
						if not name.startswith('.'):
							t = os.path.join(root, name)
							print(name)
							print(root.split('/')[1])
							print(t)
							s3.meta.client.upload_file(t,'rigme-09-2020','output/' + ID + '/' + name)
				url = create_presigned_url(
			        "rigme-09-2020",
			        'output/' + ID + '/' + filename + '_clean_rect.txt' # obj_file
		    	)

				##Delete local folder
				shutil.rmtree(output)
				return {
			        'url': url
			    }
		except Exception as e:
			return str(e)

def convert_to_3d(file_dir, output, res):
	try:
		os.system("python ./pifuhd/apps/simple_test.py -o " + output + " -c ./pifuhd/checkpoints/pifuhd.pt -r " + res + " --use_rect -i " + file_dir)
		return True
	except:
		return False


def clean_background_Image(file_dir, file_name, ID):
	try:
		output = "./output/" + ID + "/" + file_name + "_clean.png"
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
"""/Applications/Autodesk/maya2019/Maya.app/Contents/bin/mayapy ./RigNet_master/maya_save_fbx.py --id result_alex_clean_78 -i ./output/0a0474ac-037c-11eb-83e7-8c8590b37347/pifuhd_final/recon/"""
def fbx_convert(model_id, file_dir):
	try:
		print(model_id)
		os.system(PATH_MAYAPY + " ./RigNet_master/maya_save_fbx.py --id " + model_id + " -i " + file_dir + "/pifuhd_final/recon/")
		return True
	except Exception as e:
		print(e)
		return False

def create_presigned_url(
        bucket_name: str, object_name: str, expiration=3600) -> Optional[str]:
    """Generate a presigned URL to share an s3 object

    Arguments:
        bucket_name {str} -- Required. s3 bucket of object to share
        object_name {str} -- Required. s3 object to share

    Keyword Arguments:
        expiration {int} -- Expiration in seconds (default: {3600})

    Returns:
        Optional[str] -- Presigned url of s3 object. If error, returns None.
    """

    # Generate a presigned URL for the S3 object
    try:
        # note that we are passing get_object as the operation to perform
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={
                                                        'Bucket': bucket_name,
                                                        'Key': object_name
                                                    },
                                                    ExpiresIn=expiration)
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL
    return response

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)#beginning once only
    app.run(host='0.0.0.0', port=80)