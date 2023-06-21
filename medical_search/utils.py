# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
import os
import re

from google.cloud import storage

PROJECT_ID = os.environ['GOOGLE_CLOUD_PROJECT']
SEARCH_ENGINE_ID = os.environ['SEARCH_ENGINE_ID']

def show_pdf(uri: str) -> str:
    """Given gs:// uri, return html code to embed pdf in iframe"""
    pdf_file = download_from_gcs(uri)
    base64_pdf = base64.b64encode(pdf_file).decode('utf-8')
    pdf_iframe = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="800" height="800" type="application/pdf"></iframe>'
    return pdf_iframe

def download_from_gcs(uri: str) -> bytes:
    """Given gs:// uri, download file"""
    client = storage.Client()
    matches = re.search(r'gs://(.*?)/(.*)', uri)
    bucket_name, object_name = matches.group(1), matches.group(2)
    blob = client.bucket(bucket_name).blob(object_name)
    return blob.download_as_string()