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


#############
# This is a temporary (bad) hack for the prototype. We will need a better way - hopefully using ES metatada
# to get the article name
#
#TODO: load this from data/articles.json
_articles = [
    {   'bioasq_idl': '51406e6223fec90375000009',
        'title': 'Metformin Does Not Suppress Serum Thyrotropin by Increasing Levothyroxine Absorption',
        'download': 'https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4589100/pdf/thy.2015.0211.pdf',
        'ncbi_ref': 'http://www.ncbi.nlm.nih.gov/pubmed/26191653'},
    {   'bioasq_idl': '56c1f01def6e394741000045',
        'title': 'Orteronel for the treatment of prostate cancer',
        'download': 'https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4148348/pdf/nihms612517.pdf',
        'ncbi_ref': 'https://pubmed.ncbi.nlm.nih.gov/24799061/'},
    {   'bioasq_idl': '56c1f01def6e394741000045',
        'title': 'A phase 1 multiple-dose study of orteronel in Japanese patients with castration-resistant prostate cancer',
        'download': 'https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4305367/pdf/280_2014_Article_2654.pdf',
        'ncbi_ref': 'https://pubmed.ncbi.nlm.nih.gov/25537627/'},
    {   'bioasq_idl': '56c1f01def6e394741000045',
        'title': 'Phase III, randomized, double-blind, multicenter trial comparing orteronel (TAK-700) plus prednisone with placebo plus prednisone in patients with metastatic castration-resistant prostate cancer that has progressed during or after docetaxel-based therapy: ELM-PC 5',
        'download': 'https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4879718/pdf/zlj723.pdf',
        'ncbi_ref': 'https://pubmed.ncbi.nlm.nih.gov/25624429/'},
    {   'bioasq_idl': '56c1f01def6e394741000045',
        'title': 'Beyond abiraterone: new hormonal therapies for metastatic castration-resistant prostate cancer',
        'download': 'https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3928129/pdf/cbt-15-149.pdf',
        'ncbi_ref': 'https://pubmed.ncbi.nlm.nih.gov/24100689/'},
    {   'bioasq_idl': '52bf1db603868f1b06000011',
        'title': 'Optimal bone health management strategies in patients with prostate cancer',
        'download': 'https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3737681/pdf/IJU-29-89.pdf',
        'ncbi_ref': 'http://www.ncbi.nlm.nih.gov/pubmed/23956508'},
    {   'bioasq_idl': '52bf1db603868f1b06000011',
        'title': 'A changing landscape in castration-resistant prostate cancer treatment',
        'download': 'https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3399094/pdf/fendo-03-00085.pdf',
        'ncbi_ref': 'http://www.ncbi.nlm.nih.gov/pubmed/22826702'},
    {   'bioasq_idl': '52bf1db603868f1b06000011',
        'title': 'Therapeutic Fc-fusion proteins and peptides as successful alternatives to antibodies',
        'download': 'https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3225844/pdf/mabs0305_0415.pdf',
        'ncbi_ref': 'https://pubmed.ncbi.nlm.nih.gov/21785279/'},
    {   'bioasq_idl': '52bf1db603868f1b06000011',
        'title': 'Emerging novel therapies in the treatment of castrate-resistant prostate cancer',
        'download': 'https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3104424/pdf/cuaj-2-120.pdf',
        'ncbi_ref': 'https://pubmed.ncbi.nlm.nih.gov/21470540/'},
    {   'bioasq_idl': '54d4e03a3706e89528000001',
        'title': 'Therapeutic drug monitoring: antiarrhythmic drugs',
        'download': 'https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1874159/pdf/bcp0046-0307.pdf',
        'ncbi_ref': 'https://pubmed.ncbi.nlm.nih.gov/9803978/'}
]

def _get_sources(document_list: List[str]) -> List[str]:
    sources = []
    for doc in document_list:
        file_name = doc.split('/')[-1]
        for article in _articles:
            if file_name == article['download'].split('/')[-1]:
                source = f'[{article["title"]}]({article["ncbi_ref"]})'
                sources.append(source)

    return sources
############


class EnterpriseSearchRetriever(BaseRetriever, BaseModel):
    client: Any
    serving_config: Any
    project_id: Optional[str] = None
    search_engine_id: Optional[str] = None
    serving_config_id: str = 'default_config'
    location_id: str = 'global'
    max_snippet_count: int = 5

    class Config:
        """Configuration for this pydantic object."""
        extra = Extra.forbid

    @root_validator()
    def validate_environment(cls, values: Dict) -> Dict:
        project_id = get_from_dict_or_env(values, "project_id", "PROJECT_ID")
        values["project_id"] = project_id
        search_engine_id = get_from_dict_or_env(values, "search_engine_id", "SEARCH_ENGINE_ID")
        values["search_engine_id"] = search_engine_id
        location_id = get_from_dict_or_env(values, "location_id", "LOCATION_ID")
        values["location_id"] = location_id
        max_snippet_count = get_from_dict_or_env(values, "max_snippet_count", "MAX_SNIPPET_COUNT")
        values["max_snippet_count"] = max_snippet_count

        client = SearchServiceClient()
        values["client"] = client
        serving_config = client.serving_config_path(
            project=project_id,
            location=location_id,
            data_store=search_engine_id,
            serving_config=values['serving_config_id'],
        )
        values["serving_config"] = serving_config
        return values

    def _search(self, query:str):
        content_search_spec = {
            'snippet_spec': {
                'max_snippet_count': 5
            }
        }
        request = SearchRequest(
            serving_config=self.serving_config,
            query=query,
            content_search_spec=content_search_spec,
        )
        response = self.client.search(request)
        return response.results

    def _convert_search_response(self, search_results):
        documents = []
        for result in search_results:
            doc_info = MessageToDict(result.document._pb)
            if doc_info.get('derivedStructData'):
                content = [snippet.get('snippet') for snippet in doc_info.get('derivedStructData', {}).get('snippets', []) if snippet.get('snippet') is not None]
                if content:
                    document = Document(
                        page_content='\n'.join(content),
                        metadata={
                            'source': doc_info.get('derivedStructData').get('link'),
                            'id': doc_info.get('derivedStructData').get('id')
                        }
                    )
                    documents.append(document)

        return documents

    def get_relevant_documents(self, query: str) -> List[Document]:
        results = self._search(query)
        documents = self._convert_search_response(results)
        return documents

    async def aget_relevant_documents(self, query: str) -> List[Document]:
        raise NotImplementedError("Async interface to GDELT not implemented")


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