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
from __future__ import annotations

import logging;

logging.basicConfig(level=logging.INFO)
import json

from google.protobuf.json_format import MessageToDict
from google.cloud import discoveryengine

import utils

with open('data/articles.json', 'r') as f:
    _articles = json.load(f)


def enterprise_search(
        project_id: str,
        search_engine_id: str,
        search_query: str,
        location: str = 'global',
        serving_config_id: str = 'default_config',
) -> List[discoveryengine.SearchResponse.SearchResult]:
    """Query Enterprise Search"""
    # Create a client
    client = discoveryengine.SearchServiceClient()

    # The full resource name of the search engine serving config
    # e.g. projects/{project_id}/locations/{location}
    serving_config = client.serving_config_path(
        project=project_id,
        location=location,
        data_store=search_engine_id,
        serving_config=serving_config_id,
    )

    summary_expansion = discoveryengine.SearchRequest.ContentSearchSpec()
    summary_expansion.summary_spec.summary_result_count = 3
    summary_expansion.snippet_spec.max_snippet_count = 3
    request = discoveryengine.SearchRequest(
        page_size=3,
        serving_config=serving_config,
        query=search_query,
        content_search_spec=summary_expansion
    )

    return client.search(request)


def _get_sources(response) -> list[(str, str)]:
    """Return list of (title, url) tuples for sources"""
    sources = []
    for result in response.results:
        doc_info = MessageToDict(result.document._pb)
        if doc_info.get('derivedStructData'):
            content = [snippet.get('snippet') for snippet in
                       doc_info.get('derivedStructData', {}).get('snippets', []) if
                       snippet.get('snippet') is not None]
            if content:
                file_name = doc_info.get('derivedStructData').get('link').split('/')[-1]
                for article in _articles:
                    if file_name.startswith(article['download'].split('/')[-1]):
                        sources.append((article["title"], article["ncbi_ref"], article["download"]))
    return sources


def generate_answer(query: str) -> dict:
    response = enterprise_search(
        project_id=utils.get_env_project_id(),
        search_engine_id=utils.get_search_engine_id(),
        search_query=query)
    result = {}
    result['answer'] = response.summary.summary_text
    result['sources'] = _get_sources(response)
    logging.info(result['sources'])
    return result
