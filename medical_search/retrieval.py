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
import json
#Temporary hack to till https://github.com/streamlit/streamlit/pull/6664 is merged
import pydantic; pydantic.class_validators._FUNCS.clear()

import vertexai

from typing import Any, Dict, List, Optional, ClassVar, Tuple

from langchain.llms import VertexAI
from langchain.utils import get_from_dict_or_env
from langchain.schema import BaseRetriever, Document
from langchain.prompts import PromptTemplate
from langchain.prompts.base import BasePromptTemplate
from langchain.chains import  LLMChain, RetrievalQAWithSourcesChain

from google.protobuf.json_format import MessageToDict
from google.cloud.discoveryengine_v1beta  import SearchServiceClient, DocumentServiceClient, SearchRequest, SearchResponse

from pydantic import BaseModel, Extra, root_validator, Field

import utils

class EnterpriseSearchRetriever(BaseRetriever, BaseModel):
    """Wrapper around Google Cloud Enterprise Search."""
    client: Any = None #: :meta private:
    serving_config: Any = None #: :meta private:Any
    content_search_spec: Any = None #: :meta private:Any
    project_id: str = None
    search_engine_id: str = None
    serving_config_id: str = 'default_config'
    location_id: str = 'global'
    max_snippet_count: int = 3
    max_matches: int = 15
    query_expansion_condition: int = 1
    credentials: Any = None
    "The default custom credentials (google.auth.credentials.Credentials) to use "
    "when making API calls. If not provided, credentials will be ascertained from "
    "the environment."


    class Config:
        """Configuration for this pydantic object."""
        extra = Extra.forbid
        arbitrary_types_allowed = True

    @root_validator()
    def validate_environment(cls, values: Dict) -> Dict:
        try:
            from google.cloud import discoveryengine_v1beta
        except ImportError:
            raise ImportError(
                "google.cloud.discoveryengine is not installed. "
                "Please install it with pip install google-cloud-discoveryengine"
            )

        values["project_id"] = get_from_dict_or_env(values, "project_id", "PROJECT_ID")
        values["search_engine_id"] = get_from_dict_or_env(values, "search_engine_id", "SEARCH_ENGINE_ID")
        values["location_id"] = get_from_dict_or_env(values, "location_id", "LOCATION_ID")
        values["max_snippet_count"] = get_from_dict_or_env(values, "max_snippet_count", "MAX_SNIPPET_COUNT")
        values["query_expansion_condition"] = get_from_dict_or_env(values, "query_expansion_condition", "QUERY_EXPANSION_CONDITION")

        client = SearchServiceClient(credentials=values['credentials'])
        values["client"] = client

        values["serving_config"] = client.serving_config_path(
            project=values["project_id"],
            location=values["location_id"],
            data_store=values["search_engine_id"],
            serving_config=values['serving_config_id'],
        )

        values["content_search_spec"] = {
            'snippet_spec': {
                'max_snippet_count': values["max_snippet_count"],
            }
        }
        values["query_expansion_spec"] = {
            'condition': values["query_expansion_condition"],
        }

        return values

    def _convert_search_response(self, search_results):
        """Converts search response to a list of LangChain documents."""
        documents = []
        for result in search_results:
            doc_info = MessageToDict(result.document._pb)
            if doc_info.get('derivedStructData'):
                if doc_info.get('structData'):
                    metadata = doc_info.get('structData')
                else:
                    metadata = {}
                for snippet in doc_info.get('derivedStructData', {}).get('snippets', []):
                    if snippet.get('snippet') is not None:
                        metadata['source'] = f"{doc_info.get('derivedStructData').get('link')}:{snippet.get('pageNumber')}"
                        metadata['id'] = doc_info.get('id')
                        document = Document(
                            page_content=snippet.get('snippet'),
                            metadata=metadata
                        )
                        documents.append(document)

        return documents

    def get_relevant_documents(self, query: str) -> List[Document]:
        """Get documents relevant for a query."""

        request = SearchRequest(
            query=query,
            serving_config=self.serving_config,
            content_search_spec=self.content_search_spec,
            query_expansion_spec=self.query_expansion_spec,
        )
        response = self.client.search(request)
        documents = self._convert_search_response(response.results)

        if len(documents) > self.max_matches:
            documents = documents[0:self.max_matches]

        return documents

    async def aget_relevant_documents(self, query: str) -> List[Document]:
        raise NotImplementedError("Async interface to GDELT not implemented")
#############
# This is a temporary (bad) hack for the prototype. We will need a better way - hopefully using ES metatada
# to get the article name
#
with open('data/articles.json', 'r') as f:
    _articles = json.load(f)

def _get_sources(document_list: List[str]) -> List[str]:
    sources = []
    for doc in document_list:
        file_name = doc.split('/')[-1]
        for article in _articles:
            if file_name.startswith(article['download'].split('/')[-1]):
                source = f'[{article["title"]}]({article["ncbi_ref"]})'
                sources.append(source)

    return sources
############

def create_retrieval_chain() -> RetrievalQAWithSourcesChain:
    retriever = EnterpriseSearchRetriever(
        project_id=utils.get_env_project_id(),
        search_engine_id=utils.get_search_engine_id(),
    )
    vertexai.init(project=utils.get_env_project_id(),
                  location=utils.get_region())
    llm = VertexAI(
        model_name='text-bison@001',
        max_output_tokens=1024,
        temperature=0.0,
        top_p=0.8,
        top_k=40,
        verbose=True,
    )
    chain = RetrievalQAWithSourcesChain.from_chain_type(llm=llm,
                                                        chain_type="stuff",
                                                        retriever=retriever)
    return chain


def generate_answer(chain: LLMChain, query:str) -> dict:
    result = chain({'question': query}, return_only_outputs=True)
    result['sources'] = _get_sources(result['sources'].split(','))
    return result