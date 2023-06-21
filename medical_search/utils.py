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


import os
import requests
import base64

PROJECT_ID = os.environ['GOOGLE_CLOUD_PROJECT']
SEARCH_ENGINE_ID = os.environ['SEARCH_ENGINE_ID']

def show_pdf(url):
    pdf_file = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})  # Need to override default header because
    # server blocks scrapers (https://scrapeops.io/web-scraping-playbook/403-forbidden-error-web-scraping/)
    base64_pdf = base64.b64encode(pdf_file.content).decode('utf-8')
    pdf_iframe = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="800" height="800" type="application/pdf"></iframe>'
    return pdf_iframe
