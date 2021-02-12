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
from flask_cors import CORS
from binascii import a2b_base64
import base64
from base64 import b64decode
from string import Template
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
import smtplib
import codecs
from bs4 import BeautifulSoup
from PIL import Image


from email import encoders
import zipfile

Server_Status=False


ALLOWED_EXTENSIONS = ['.png', '.jpg']
PATH_MAYAPY = "../../../usr/autodesk/maya2020/bin/mayapy"
PATH_RIGME = "/Users/jasbakshi/Documents/GitHub/RigMe"

cors_configuration = {
    'CORSRules': [{
        'AllowedHeaders': ['Authorization'],
        'AllowedMethods': ['GET','PUT'],
        'AllowedOrigins': ['*'], # replace with https://*.rigme.io once ssl works
        'ExposeHeaders': ['GET'],
        'MaxAgeSeconds': 840000
    }]
}

import boto3
from botocore.exceptions import ClientError

# Replace sender@example.com with your "From" address.
# This address must be verified with Amazon SES.
SENDER = "hello@3dconvert.me"

# Specify a configuration set. If you do not want to use a configuration
# set, comment the following variable, and the 
# ConfigurationSetName=CONFIGURATION_SET argument below.
#CONFIGURATION_SET = "ConfigSet"

# If necessary, replace us-west-2 with the AWS Region you're using for Amazon SES.
AWS_REGION = "us-west-2"

# The subject line for the email.
SUBJECT = "3DConvertMe files are ready!"

CHARSET = "UTF-8"

s3 = boto3.resource('s3',aws_access_key_id="AKIAJE2BGFS3XAF4PBYA",
             aws_secret_access_key= "***REMOVED***", region_name=AWS_REGION)
s3_client = boto3.client('s3',aws_access_key_id="AKIAJE2BGFS3XAF4PBYA",
             aws_secret_access_key= "***REMOVED***", region_name=AWS_REGION)
s3_client.put_bucket_cors(Bucket='rigme-09-2020',
                   CORSConfiguration=cors_configuration)
ses_client = boto3.client('ses',region_name=AWS_REGION,aws_access_key_id="AKIAJE2BGFS3XAF4PBYA",
             aws_secret_access_key= "***REMOVED***")
sqs = boto3.resource('sqs',region_name=AWS_REGION,aws_access_key_id="AKIAJE2BGFS3XAF4PBYA",
             aws_secret_access_key= "***REMOVED***")
sqs_cl = boto3.client('sqs',region_name=AWS_REGION,aws_access_key_id="AKIAJE2BGFS3XAF4PBYA",
             aws_secret_access_key= "***REMOVED***")
lambda_client = boto3.client('lambda',aws_access_key_id="AKIAJE2BGFS3XAF4PBYA",
             aws_secret_access_key= "***REMOVED***",region_name=AWS_REGION)
#sqs_client = sqs_cl.get_queue_by_name(QueueName='rigme_sqs')
def get_concat_h(im1, im2):
    dst = Image.new('RGB', (im1.width + im2.width, im1.height))
    dst.paste(im1, (0, 0))
    dst.paste(im2, (im1.width, 0))
    return dst
#import ssl
#context = ssl.SSLContext()
#context.load_cert_chain('STAR_rigme_io.pem','private.key')
#context.load_verify_locations('STAR_rigme_io_ca.pem')
#TRUE = buisy, FALSE = free

#@app.errorhandler(Exception)
#def server_error(err):
#    app.logger.exception(err)
#    return err, 500

#@app.route('/')
#def home_endpoint():
#    return 'Welcome to the RigMe API from Jas and Alex!'
import json
#@app.route('/api/convert_picture', methods=['POST'])
def pipeline(form):
	if len(form['file']) > 0:
		Server_Status = True
		print("Form: " + str(form))
		#print("Files: " + str(request.files))
		try:
			RECIPIENT =  form['recepient']
			ID = str(uuid.uuid1())
			output = "./output/" + RECIPIENT + ID
			os.makedirs(output)
			#data_json = request.get_json()
			#image_path = request.files['file']
			image = json.loads(form['file'])
			with open(output + '/image_raw_data' , 'wb') as f:
                               s3_client.download_fileobj('rigme-sqs-bucket', image[1]['s3Key'], f)
			image_data = open(output + '/image_raw_data', "r").read()
			header, encoded = image_data.split(",", 1)
			data = b64decode(encoded)
			#filename = secure_filename(image_path.filename)
			filename = ID + '.png'
			img = os.path.join(output, filename)
			with open(img,'wb') as fh:
				fh.write(data)
			#binary_data = a2b_base64(image_data)
			#fd = open(img,'wb')
			#fd.write(binary_data)
			#fd.close()
			#image_path.save(img)
			res = form['resolution']
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
				clean_image_path = clean_background_Image(img, filename, ID, RECIPIENT)
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
				t = convert_to_3d(output, output, res)
				print(t)
				obj_file = "result_" + filename + "_clean_" + res
				print(output + "/" + obj_file + "_remesh.obj")
				print(obj_file)
				print('predicting to 3d rect')
				obj_rect_convert(output, obj_file)
				print('converting to glb')
				#fbx_convert(obj_file, output)
				print(output + "/pifuhd_final/recon/" + obj_file + "_remesh.obj")
				print(output + "/pifuhd_final/recon/" + obj_file + "_remesh_rig.txt")
				print(output + "/pifuhd_final/recon/" + obj_file + ".glb")
				blender_glb_convert(output + "/pifuhd_final/recon/" + obj_file + "_remesh.obj", output + "/pifuhd_final/recon/" + obj_file + "_remesh_rig.txt", output + "/pifuhd_final/recon/" + obj_file + ".glb")
				##AWS Upload
				im1 = Image.open(clean_image_path)
				im2 = Image.open(output + "/pifuhd_final/recon/" + obj_file + ".png")
				get_concat_h(im1, im2).save(output + "/pifuhd_final/recon/COMBINED.png")
				with zipfile.ZipFile(output + "/ALL_FILE.zip", "w") as zf:
				    zf.write(output + "/pifuhd_final/recon/" + obj_file + "_remesh.obj")
				    zf.write(output + "/pifuhd_final/recon/" + obj_file + ".fbx")
				    zf.write(output + "/pifuhd_final/recon/" + obj_file + ".glb")
				    zf.write(output + "/pifuhd_final/recon/" + obj_file + ".stl")
				    zf.write(output + "/pifuhd_final/recon/COMBINED.png")
				    zf.close()

				for root, dirs, files in os.walk(output, topdown=False):
					for name in files:
						if not name.startswith('.'):
							t = os.path.join(root, name)
							print(name)
							print(root.split('/')[1])
							print(t)
							s3.meta.client.upload_file(t,'rigme-09-2020','output/' + RECIPIENT + ID + '/' + name)
				#os.rmdir('output/' + RECIPIENT + ID)
				fbx_url = create_presigned_url("rigme-09-2020",'output/' + RECIPIENT + ID + '/' + obj_file + '.fbx')
				#fbx_file
			    	
				glb_url = create_presigned_url("rigme-09-2020",'output/' + RECIPIENT + ID + '/' + obj_file + '.glb')
				# glb_file
			    	
				stl_url = create_presigned_url("rigme-09-2020",'output/' + RECIPIENT + ID + '/' + obj_file + '.stl')
				# stl_file
		    		
				obj_url = create_presigned_url("rigme-09-2020",'output/' + RECIPIENT + ID + '/' + obj_file + '_remesh.obj')
				# obj_file
				zip_url = create_presigned_url("rigme-09-2020",'output/' + RECIPIENT + ID + '/ALL_FILE.zip')
				##Delete local folder
				
				#os.rmdir('output/' + ID)
				with open("email.html", "r", encoding='utf-8') as f:
				    base_text= f.read()

				t = Template(base_text).safe_substitute(obj = obj_url, stl = stl_url, fbx = fbx_url,glb = glb_url, zip = zip_url)
				USERNAME_SMTP = "***REMOVED***"

# Replace smtp_password with your Amazon SES SMTP password.
				PASSWORD_SMTP = "***REMOVED***"
				HOST = "***REMOVED***"
				PORT = 587

				msg = MIMEMultipart('related')
# Add subject, from and to lines.
				msg['Subject'] = SUBJECT 
				msg['From'] = SENDER 
				msg['To'] = RECIPIENT
				msg_body = MIMEMultipart('alternative')
				htmlpart = MIMEText(t.encode(CHARSET), 'html', CHARSET)
				msg_body.attach(htmlpart)
				msg.attach(msg_body)
				with open(output + "/pifuhd_final/recon/COMBINED.png", 'rb') as f:
    # set attachment mime and file name, the image type is png
				    mime = MIMEBase('image', 'png', filename='combined.png')
    # add required header data:
				    mime.add_header('Content-Disposition', 'attachment', filename='combined.png')
				    mime.add_header('X-Attachment-Id', '4')
				    mime.add_header('Content-ID', '<4>')
				    # read attachment file content into the MIMEBase object
				    mime.set_payload(f.read())
				    # encode with base64
				    encoders.encode_base64(mime)
    # add MIMEBase object to MIMEMultipart object
				    msg.attach(mime)
				with open('static/obj.png', 'rb') as f:
    # set attachment mime and file name, the image type is png
				    mime = MIMEBase('image', 'png', filename='obj.png')
    # add required header data:
				    mime.add_header('Content-Disposition', 'attachment', filename='obj.png')
				    mime.add_header('X-Attachment-Id', '0')
				    mime.add_header('Content-ID', '<0>')
				    # read attachment file content into the MIMEBase object
				    mime.set_payload(f.read())
				    # encode with base64
				    encoders.encode_base64(mime)
    # add MIMEBase object to MIMEMultipart object
				    msg.attach(mime)
    
				with open('static/fbx.png', 'rb') as f:
				    # set attachment mime and file name, the image type is png
				    mime = MIMEBase('image', 'png', filename='fbx.png')
				    # add required header data:
				    mime.add_header('Content-Disposition', 'attachment', filename='fbx.png')
				    mime.add_header('X-Attachment-Id', '2')
				    mime.add_header('Content-ID', '<2>')
				    # read attachment file content into the MIMEBase object
				    mime.set_payload(f.read())
				    # encode with base64
				    encoders.encode_base64(mime)
				    # add MIMEBase object to MIMEMultipart object
				    msg.attach(mime)
    
				with open('static/stl.png', 'rb') as f:
    # set attachment mime and file name, the image type is png
				    mime = MIMEBase('image', 'png', filename='stl.png')
    # add required header data:
				    mime.add_header('Content-Disposition', 'attachment', filename='stl.png')
				    mime.add_header('X-Attachment-Id', '1')
				    mime.add_header('Content-ID', '<1>')
    # read attachment file content into the MIMEBase object
				    mime.set_payload(f.read())
    # encode with base64
				    encoders.encode_base64(mime)
    # add MIMEBase object to MIMEMultipart object
				    msg.attach(mime)

				with open('static/glb.png', 'rb') as f:
    # set attachment mime and file name, the image type is png
				    mime = MIMEBase('image', 'png', filename='glb.png')
				    mime.add_header('Content-Disposition', 'attachment', filename='glb.png')
				    mime.add_header('X-Attachment-Id', '3')
				    mime.add_header('Content-ID', '<3>')
    # read attachment file content into the MIMEBase object
				    mime.set_payload(f.read())
    # encode with base64
				    encoders.encode_base64(mime)
    # add MIMEBase object to MIMEMultipart object
				    msg.attach(mime)
				print('SENDING Email to: ' + RECIPIENT)
				try:
				    server = smtplib.SMTP(HOST, PORT)
				    server.ehlo()
				    server.starttls()
    #stmplib docs recommend calling ehlo() before & after starttls()
				    server.ehlo()
				    server.login(USERNAME_SMTP, PASSWORD_SMTP)
				    server.sendmail(SENDER, RECIPIENT, msg.as_string())
				    server.close()
				except ClientError as e:
				    print(e.response['Error']['Message'])

				shutil.rmtree(output)
				Server_Status=False
				timer()
				return {
			        	'fbx_url': fbx_url,
			        	'glb_url':glb_url,
			        	'stl_url':stl_url,
			        	'obj_url':obj_url
			    	}
				#Server_Status = False
		except Exception as e:
			Server_Status = False
			timer()
			return str(e)

#@app.route('/api/new_request', methods=['POST'])
def new_order():
	try:
		mesg = sqs_cl.receive_message(QueueUrl='https://sqs.us-west-2.amazonaws.com/235224322090/rigme_sqs',MaxNumberOfMessages=1,MessageAttributeNames=['email'])
		print(mesg)
		RECIPIENT = mesg['Messages'][0]['MessageAttributes']['email']['StringValue']
		img_data = mesg['Messages'][0]['Body']
		form = {'recepient':RECIPIENT,'file':img_data,'resolution':'78'}
		print(form)
		sqs_cl.delete_message(QueueUrl='https://sqs.us-west-2.amazonaws.com/235224322090/rigme_sqs',ReceiptHandle=mesg['Messages'][0]['ReceiptHandle'])
		pipeline(form)
		timer()
	except Exception as e:
		print(e)
		timer()

import time
def timer():
	print('timer....')
	time.sleep( 60 )
	if Server_Status == False:
		new_order()
	else:
		timer()

def convert_to_3d(file_dir, output, res):
	try:
		os.system("python3 ./pifuhd/apps/simple_test.py -o " + output + " -c ./pifuhd/checkpoints/pifuhd.pt -r " + res + " --use_rect -i " + file_dir)
		return True
	except:
		return False


def clean_background_Image(file_dir, file_name, ID, RECIPIENT):
	try:
		output = "./output/" + RECIPIENT + ID + "/" + file_name + "_clean.png"
		print(output)
		os.system("python3 ./image_background_remove_tool/main.py -o " + output + " -m u2net -prep bbd-fastrcnn -postp rtb-bnb -i " + file_dir)
		return output
	except:
		return False

def rect_Image(file_dir, file_name):
	try:
		os.system("python3 ./lightweight_human_pose_estimation/process_image.py --input " + file_dir)
		return True
	except Exception as e:
		print(e)
		return False

def obj_rect_convert(file_dir, obj_file_name):
	try:
		print(file_dir,obj_file_name)
		os.system("python3 ./RigNet_master/quick_start.py -i " + file_dir + "/pifuhd_final/recon/ -o " + obj_file_name)
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

def blender_glb_convert(object_dir, joint_text_file_dir, save_path):
	try:
		#print(model_id)
		os.system("blender --background --python ./loadskeleton.py -- -o=" + object_dir + " -t=" + joint_text_file_dir + " -s=" + save_path)
		return True
	except Exception as e:
		print(e)
		return False

def create_presigned_url(
        bucket_name: str, object_name: str, expiration=86400) -> Optional[str]:
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
	timer()
