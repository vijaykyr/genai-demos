import streamlit as st
import streamlit.components.v1 as components

components.html(
    '''
    <!-- Gen App Builder widget bundle -->
    <script src="https://gen-ai-app-builder.appspot.com/preview/client"></script>
    
    <!-- Search widget element is not visible by default -->
    <gen-search-widget
      widgetConfigName="projects/607718892999/locations/global/collections/default_collection/dataStores/unstructuredtest_1685643972007/widgetConfigs/default_search_widget_config"
      apiKey="AIzaSyBGjFpAt2upbZXIj_9EBP4dSzNmfVDs9mc"
      triggerId="searchWidgetTrigger">
    </gen-search-widget>
    
    <!-- Element that opens the widget on click. It does not have to be an input -->
    <input placeholder="Search here" id="searchWidgetTrigger" />
    ''',
    height=500)  # If height not specified results don't render
