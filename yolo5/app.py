import time
from flask import Flask, request, jsonify
import uuid
import yaml
from loguru import logger
from detect import run
import os
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from pymongo import MongoClient
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Initialize S3 client
s3_client = boto3.client('s3')
bucket_name = os.getenv('S3_BUCKET_NAME', 'bennyi-aws-s3-bucket')
s3_folder_path = 'docker-project'

# Update MongoDB connection URI to use Docker Compose service name
mongo_client = MongoClient('mongodb://mongo1:27017/')
db = mongo_client['predictions_db']
predictions_collection = db['predictions']

# Load YOLO label names
with open("data/coco128.yaml", "r") as stream:
    names = yaml.safe_load(stream)['names']

app = Flask(__name__)

@app.route('/predict', methods=['POST'])
def predict():
    prediction_id = str(uuid.uuid4())
    logger.info(f'Prediction ID: {prediction_id}. Start processing')

    data = request.get_json()
    logger.info(f'Received data: {data}')
    img_url = data.get('image_url')  # Updated to match the payload field

    if not img_url:
        logger.error('Image URL not provided')
        return {'error': 'Image URL not provided'}, 400

    if img_url.startswith(f'https://{bucket_name}.s3.eu-west-3.amazonaws.com/'):
        object_key = img_url.split(f'https://{bucket_name}.s3.eu-west-3.amazonaws.com/')[1]
    else:
        logger.error('Invalid image URL format')
        return {'error': 'Invalid image URL format'}, 400

    original_img_path = f'static/data/{prediction_id}/{os.path.basename(img_url)}'
    logger.info(f'Original image path: {original_img_path}')

    Path(original_img_path).parent.mkdir(parents=True, exist_ok=True)

    try:
        logger.info(f'Downloading from S3: {object_key}')
        s3_client.download_file(bucket_name, object_key, original_img_path)
        logger.info(f'Download completed: {original_img_path}')
        os.chmod(original_img_path, 0o644)
    except NoCredentialsError:
        logger.error('AWS credentials not available')
        return {'error': 'AWS credentials not available'}, 403
    except ClientError as e:
        logger.error(f'Client error: {e}')
        return {'error': f'Error downloading image: {e}'}, 500
    except Exception as e:
        logger.error(f'Unexpected error: {e}')
        return {'error': f'Error downloading image: {e}'}, 500

    if os.path.exists(original_img_path):
        logger.info(f'YOLO will process: {original_img_path}')
    else:
        logger.error(f'YOLO cannot find the image: {original_img_path}')

    try:
        run(
            weights='yolov5s.pt',
            data='data/coco128.yaml',
            source=original_img_path,
            project='static/data',
            name=prediction_id,
            save_txt=True,
            exist_ok=True
        )
        logger.info(f'YOLOv5 completed processing for {original_img_path}')
    except Exception as e:
        logger.error(f'Error during YOLOv5 inference: {e}')
        return {'error': f'Error during YOLOv5 inference: {e}'}, 500

    predicted_img_path = Path(f'static/data/{prediction_id}/{os.path.basename(img_url)}')
    try:
        predicted_img_s3_path = f'predictions/{prediction_id}/{os.path.basename(img_url)}'
        s3_client.upload_file(str(predicted_img_path), bucket_name, predicted_img_s3_path)
        logger.info(f'Uploaded predicted image to S3: {predicted_img_s3_path}')
    except NoCredentialsError:
        logger.error('AWS credentials not available')
        return {'error': 'AWS credentials not available'}, 403
    except ClientError as e:
        logger.error(f'Client error: {e}')
        return {'error': f'Error uploading predicted image: {e}'}, 500
    except Exception as e:
        logger.error(f'Unexpected error: {e}')
        return {'error': f'Error uploading predicted image: {e}'}, 500

    pred_summary_path = Path(f'static/data/{prediction_id}/labels/{os.path.basename(img_url).split(".")[0]}.txt')
    logger.info(f'Looking for prediction summary at: {pred_summary_path}')

    if pred_summary_path.exists():
        try:
            with open(pred_summary_path) as f:
                labels = f.read().splitlines()
                labels = [line.split(' ') for line in labels]
                labels = [{
                    'class': names[int(l[0])],
                    'cx': float(l[1]),
                    'cy': float(l[2]),
                    'width': float(l[3]),
                    'height': float(l[4]),
                } for l in labels]
                logger.info(f'Prediction summary: {labels}')
        except Exception as e:
            logger.error(f'Error parsing prediction labels: {e}')
            return {'error': 'Error parsing prediction labels'}, 500

        prediction_summary = {
            'prediction_id': str(prediction_id),
            'original_img_path': original_img_path,
            'predicted_img_path': predicted_img_s3_path,
            'labels': labels,
            'time': time.time()
        }

        logger.info(f'Prediction summary: {prediction_summary}')
        try:
            predictions_collection.insert_one(prediction_summary)
            logger.info(f'Prediction summary stored in MongoDB')
        except Exception as e:
            logger.error(f'Error storing prediction summary in MongoDB: {e}')
            return {'error': 'Error storing prediction summary'}, 500


        class_counts = {}
        for label in labels:
            obj_class = label['class']
            if obj_class in class_counts:
                class_counts[obj_class] += 1
            else:
                class_counts[obj_class] = 1


        # Format the output as required
        prediction_text = ""
        for obj_class, count in class_counts.items():
            prediction_text += f"{obj_class}: {count}\n"

        return jsonify({"prediction_text" : prediction_text})
    else:
        logger.error(f'Prediction result not found: {pred_summary_path}')
        return {'error': 'Prediction result not found'}, 404

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8081)
