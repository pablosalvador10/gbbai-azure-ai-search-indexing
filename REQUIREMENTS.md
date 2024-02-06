## Table of Contents

- [Setting Up Azure AI Services](#setting-up-azure-ai-services)
- [Configuration Environment Variables](#configuration-environment-variables)
- [Notebooks Setup](#notebooks-setup)
  - [Setting Up Conda Environment and Configuring VSCode for Jupyter Notebooks](#setting-up-conda-environment-and-configuring-vscode-for-jupyter-notebooks)

## Setting Up Azure AI Services

- **Azure AI search**: Delivering Deliver accurate, hyper-personalized responses in your Gen AI applications [start here](https://azure.microsoft.com/en-us/products/ai-services/ai-search/)
- **Azure Open AI Services**: To effectively vectorize data, we leverage the `ada` model within Azure OpenAI Services. This model, part of the suite of large language and generative AI models, is specifically designed for tasks that require nuanced understanding and processing of complex data. By utilizing `ada`, we can transform and represent diverse datasets in a vectorized format. [start here](https://techcommunity.microsoft.com/t5/ai-azure-ai-services-blog/azure-openai-service-launches-gpt-4-turbo-and-gpt-3-5-turbo-1106/ba-p/3985962)


## Configuration Environment Variables

Before running this notebook, you must configure certain environment variables. We will now use environment variables to store our configuration. This is a more secure practice as it prevents sensitive data from being accidentally committed and pushed to version control systems.

Create a `.env` file in your project root (use the provided `.env.sample` as a template) and add the following variables:

```env
# Required: Azure AI Search Service Configuration
AZURE_AI_SEARCH_SERVICE_ENDPOINT=""
AZURE_SEARCH_ADMIN_KEY=""
AZURE_SEARCH_INDEX_NAME_DOCUMENTS=""
AZURE_SEARCH_INDEX_NAME_IMAGES_AND_AUDIO=""

# Required: Azure Open API Configuration
AZURE_AOAI_API_KEY=''
AZURE_AOAI_API_ENDPOINT=''
AZURE_AOAI_EMBEDDING_DEPLOYMENT_ID=''
AZURE_AOAI_API_VERSION=''

# Required IF interacting with Blob Storage: Azure Storage Configuration
AZURE_STORAGE_CONNECTION_STRING=''

# Required IF interacting with SharePoint through Graph API: Microsoft Entra ID Configuration
TENANT_ID=''
CLIENT_ID=''
CLIENT_SECRET=''
SITE_DOMAIN=''
SITE_NAME=''

# REQUIRED IF APPLYING OCR: Azure Document Intelligence API Configuration
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=""
AZURE_DOCUMENT_INTELLIGENCE_KEY=""
```

Please replace the placeholders in the `.env` file with your actual configurations for Azure Open API, Azure Storage, Microsoft Entra ID, and Azure Document Intelligence API.

- `AZURE_AOAI_API_KEY`, `AZURE_AOAI_API_ENDPOINT`, `AZURE_AOAI_EMBEDDING_DEPLOYMENT_ID`, `AZURE_AOAI_API_VERSION`: These are your Azure Open API configurations. You can find these details in your Azure Open API service in the Azure portal.

- `AZURE_STORAGE_CONNECTION_STRING`: This is the connection string for your Azure Storage. You can find it in the "Access keys" section of your Storage account in the Azure portal.

- `TENANT_ID`, `CLIENT_ID`, `CLIENT_SECRET`, `SITE_DOMAIN`, `SITE_NAME`: These are your Microsoft Entra ID configurations required for interacting with SharePoint through the Graph API. You can find these details in your Azure Active Directory and SharePoint admin center. For a more detailed guide on SharePoint indexing with Azure Cognitive Search, please refer to this [GitHub repository](https://github.com/liamca/sharepoint-indexing-azure-cognitive-search).

- `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT`, `AZURE_DOCUMENT_INTELLIGENCE_KEY`: These are your Azure Document Intelligence API configurations. You can find these details in your Azure Document Intelligence service in the Azure portal.

> 📌 **Note**
> Remember not to commit the .env file to your version control system. Add it to your .gitignore file to prevent it from being tracked.


## Create Conda Environment from the Repository

> Instructions for Windows users:

1. **Create the Conda Environment**:
   - In your terminal or command line, navigate to the repository directory.
   - Execute the following command to create the Conda environment using the `environment.yaml` file:
     ```bash
     conda env create -f environment.yaml
     ```
   - This command creates a Conda environment as defined in `environment.yaml`.

2. **Activating the Environment**:
   - After creation, activate the new Conda environment by using:
     ```bash
     conda activate speech-ai-azure-services
     ```

> Instructions for Linux users (or Windows users with WSL or other linux setup):

1. **Use `make` to Create the Conda Environment**:
   - In your terminal or command line, navigate to the repository directory and look at the Makefile.
   - Execute the `make` command specified below to create the Conda environment using the `environment.yaml` file:
     ```bash
     make create_conda_env
     ```

2. **Activating the Environment**:
   - After creation, activate the new Conda environment by using:
     ```bash
     conda activate speech-ai-azure-services
     ```

## Configure VSCode for Jupyter Notebooks

1. **Install Required Extensions**:
   - Download and install the `Python` and `Jupyter` extensions for VSCode. These extensions provide support for running and editing Jupyter Notebooks within VSCode.

2. **Attach Kernel to VSCode**:
   - After creating the Conda environment, it should be available in the kernel selection dropdown. This dropdown is located in the top-right corner of the VSCode interface.
   - Select your newly created environment (`speech-ai-azure-services`) from the dropdown. This sets it as the kernel for running your Jupyter Notebooks.

3. **Run the Notebook**:
   - Once the kernel is attached, you can run the notebook by clicking on the "Run All" button in the top menu, or by running each cell individually.

4. **Voila! Ready to Go**:
   - Now that your environment is set up and your kernel is attached, you're ready to go! Please visit the notebooks in the repository to start exploring.

> **Note:** By following these steps, you'll establish a dedicated Conda environment for your project and configure VSCode to run Jupyter Notebooks efficiently. This environment will include all the necessary dependencies specified in your `environment.yaml` file. If you wish to add more packages or change versions, please use `pip install` in a notebook cell or in the terminal after activating the environment, and then restart the kernel. The changes should be automatically applied after the session restarts.
