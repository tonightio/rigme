from flask import Flask, request, url_for, abort, g, send_file, send_from_directory, safe_join
import boto3
import sqs_extended_client
app = Flask(__name__)


AWS_REGION = "us-west-2"
db_client = boto3.client('dynamodb',region_name=AWS_REGION)
sqs = boto3.resource('sqs',region_name=AWS_REGION)
sqs_cl = boto3.client('sqs',region_name=AWS_REGION)
queue = sqs.get_queue_by_name(QueueName='rigme_sqs')
queue.large_payload_support = 'rigme-sqs-bucket'
queue.always_through_s3 = True

@app.route('/')
def home_endpoint():
    return 'Welcome to the RigMe API from Jas and Alex!'

@app.route('/api/new_request', methods=['POST'])
def new_order():
	if request.method == 'POST':
		RECIPIENT =  request.form.get('recepient')
		image_data = request.form.get('file')
		store=True
		#with open('Master_Email_List.txt', 'r') as f:
		#	for line in f:
        #   	 	# For each line, check if line contains the string
		#		if RECIPIENT in line:
		#			store=False
		#	f.close()
		#if store:
		#	with open('Master_Email_List.txt', 'a') as fi:
		#		fi.write(RECIPIENT + ",\n")
		#		fi.close()
		queue_t = queue.send_message(MessageBody=image_data, MessageAttributes={'email': {
	            'StringValue': RECIPIENT,
	            'DataType': 'String'
	        }
		})
		return({'status':200,'body':'Successfully sent Order!'})

if __name__ == "__main__":
    #app.run(host='0.0.0.0', port=80)#beginning once only
    app.run(host='0.0.0.0', port=443) #,ssl_context=context)
