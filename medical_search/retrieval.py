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

import logging
#logging.basicConfig(level=logging.INFO)
import json

import streamlit as st
from google.protobuf.json_format import MessageToDict
from google.cloud import discoveryengine
from google.cloud.discoveryengine_v1beta.services.search_service.pagers import SearchPager
from google.cloud.discoveryengine_v1beta.services.document_service.pagers import ListDocumentsPager
import utils


def enterprise_search_list_docs(
        project_id: str,
        search_engine_id: str,
        location: str = 'global',
) -> ListDocumentsPager:
    """List Enterprise Search Corpus"""
    client = discoveryengine.DocumentServiceClient()
    parent = "projects/" + project_id + "/locations/" + location + \
        "/collections/default_collection/dataStores/" + search_engine_id + "/branches/default_branch"
    request = discoveryengine.ListDocumentsRequest(parent=parent)
    return client.list_documents(request=request)


def enterprise_search_query(
        project_id: str,
        search_engine_id: str,
        search_query: str,
        location: str = 'global',
        serving_config_id: str = 'default_config',
) -> SearchPager:
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

    search_spec = discoveryengine.SearchRequest.ContentSearchSpec()
    search_spec.summary_spec.summary_result_count = 3
    search_spec.snippet_spec.max_snippet_count = 3
    request = discoveryengine.SearchRequest(
        page_size=3,
        serving_config=serving_config,
        query=search_query,
        content_search_spec=search_spec
    )

    return client.search(request)


def _get_sources(response: SearchPager) -> list[(str, str, str, list)]:
    """Parse ES response and generate list of tuples for sources"""
    sources = []
    for result in response.results:
        doc_info = MessageToDict(result.document._pb)
        if doc_info.get('derivedStructData'):
            content = [snippet.get('snippet') for snippet in
                       doc_info.get('derivedStructData', {}).get('snippets', []) if
                       snippet.get('snippet') is not None]
            metadata = doc_info.get('structData')
            sources.append((
                metadata["title"],
                metadata["ncbi_ref"],
                metadata["download"],
                doc_info.get('derivedStructData')['link'],
                content))
    return sources


def generate_answer(query: str) -> dict:
    response = enterprise_search_query(
        project_id=utils.PROJECT_ID,
        search_engine_id=utils.SEARCH_ENGINE_ID,
        search_query=query)
    result = {}
    result['answer'] = response.summary.summary_text
    result['sources'] = _get_sources(response)
    logging.info(result['sources'])
    return result


@st.cache_data
def get_corpus() -> list[dict]:
    corpus = []
    docs = enterprise_search_list_docs(
        project_id=utils.PROJECT_ID,
        search_engine_id=utils.SEARCH_ENGINE_ID)
    for doc in docs:
        metadata = json.loads(doc.json_data)
        metadata['gcs_uri'] = doc.content.uri
        corpus.append(metadata)
    logging.info(corpus)
    return corpus
