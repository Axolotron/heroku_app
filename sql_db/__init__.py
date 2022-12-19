import logging
import os
import shutil
import sqlite3
import time
from datetime import datetime
from glob import glob
from git import Repo
import boto3
from apscheduler.schedulers.background import BackgroundScheduler
import huggingface_hub
import pandas as pd

from .const import DB_FILE, DB_NAME, TOKEN, HF_DB_PATH, HF_DB_DIR, REPO_NAME, AWS_ACCESS_KEY, AWS_SECRET_KEY, \
    IMAGE_DIR, BUCKET_NAME, S3_EXTRA_ARGS, DATABASE_URL
from sql_db.images import create_image_table, get_all_images, ImageData, add_image
from sql_db.users import create_user_table, add_user, get_all_users, get_user_by_email
from sql_db.rankings import create_rankings_table, add_ranking, get_all_rankings, RankingData
from utils import logger


def upload_images():
    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
    )
    for path in glob(f"{IMAGE_DIR}/*"):
        # we want to keep the file for one minute
        creation_time = os.path.getctime(path)
        current_time = time.time()
        time_difference = current_time - creation_time
        if time_difference < 60:
            continue
        s3_client.upload_file(path,
                              BUCKET_NAME,
                              path,
                              ExtraArgs=S3_EXTRA_ARGS)
        os.remove(path)


logger.debug("Setting up background jobs")
scheduler = BackgroundScheduler()
scheduler.add_job(func=upload_images, trigger="interval", seconds=180)
scheduler.start()
logger.debug("Finished setting up background jobs")