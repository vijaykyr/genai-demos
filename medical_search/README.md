# Generative AI for Medical Search

Demonstrates using Enterprise Search for Q&A on a biomedical corpus with citations.  

[TODO: Add architecture diagram]

## Deploy Locally
Set environment variables
```commandline
export GOOGLE_CLOUD_PROJECT=[your-project-id]
export SEARCH_ENGINE_ID=[your-enterprise-search-engine-id]
```
Install dependencies
```commandline
pip install -r requirements.txt
```
Launch
```commandline
streamlit run About.py
```

## Deploy to App Engine

Ensure the default App Engine service account has the following IAM permissions:
- Log Writer
- Storage Object Viewer

Set the environment variables in `app.yaml`
```yaml
env_variables:
    SEARCH_ENGINE_ID: your-enterprise-search-engine-id
```

Deploy
```commandline
gcloud app deploy
```