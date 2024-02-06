"""
`azure_openai.py` is a module for managing interactions with the Azure OpenAI API within our application.

"""
import os
from typing import Dict, List, Optional

import openai
from dotenv import load_dotenv
from openai import AzureOpenAI

from src.aoai.tokenizer import AzureOpenAITokenizer
from utils.ml_logging import get_logger

# Load environment variables from .env file
load_dotenv()

# Set up logger
logger = get_logger()


class AzureOpenAIManager:
    """
    A manager class for interacting with the Azure OpenAI API.

    This class provides methods for generating text completions and chat responses using the Azure OpenAI API.
    It also provides methods for validating API configurations and getting the OpenAI client.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_version: Optional[str] = None,
        azure_endpoint: Optional[str] = None,
        completion_model_name: Optional[str] = None,
        chat_model_name: Optional[str] = None,
        embedding_model_name: Optional[str] = None,
    ):
        """
        Initializes the Azure OpenAI Manager with necessary configurations.

        :param api_key: The Azure OpenAI Key. If not provided, it will be fetched from the environment variable "AZURE_OPENAI_KEY".
        :param api_version: The Azure OpenAI API Version. If not provided, it will be fetched from the environment variable "AZURE_OPENAI_API_VERSION" or default to "2023-05-15".
        :param azure_endpoint: The Azure OpenAI API Endpoint. If not provided, it will be fetched from the environment variable "AZURE_OPENAI_ENDPOINT".
        :param completion_model_name: The Completion Model Deployment ID. If not provided, it will be fetched from the environment variable "AZURE_AOAI_COMPLETION_MODEL_DEPLOYMENT_ID".
        :param chat_model_name: The Chat Model Name. If not provided, it will be fetched from the environment variable "AZURE_AOAI_CHAT_MODEL_NAME".
        :param embedding_model_name: The Embedding Model Deployment ID. If not provided, it will be fetched from the environment variable "AZURE_AOAI_EMBEDDING_DEPLOYMENT_ID".
        """
        self.api_key = api_key or os.getenv("AZURE_AOAI_API_KEY")
        self.api_version = (
            api_version or os.getenv("AZURE_AOAI_API_VERSION") or "2023-05-15"
        )
        self.azure_endpoint = azure_endpoint or os.getenv("AZURE_AOAI_API_ENDPOINT")
        self.completion_model_name = completion_model_name or os.getenv(
            "AZURE_AOAI_COMPLETION_MODEL_DEPLOYMENT_ID"
        )
        self.chat_model_name = chat_model_name or os.getenv(
            "AZURE_AOAI_CHAT_MODEL_DEPLOYMENT_ID"
        )
        self.embedding_model_name = embedding_model_name or os.getenv(
            "AZURE_AOAI_EMBEDDING_DEPLOYMENT_ID"
        )

        self.openai_client = AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.azure_endpoint,
        )

        self.tokenizer = AzureOpenAITokenizer()

        self._validate_api_configurations()

    def get_azure_openai_client(self):
        """
        Returns the OpenAI client.

        This method is used to get the OpenAI client that is used to interact with the OpenAI API.
        The client is initialized with the API key and endpoint when the AzureOpenAIManager object is created.

        :return: The OpenAI client.
        """
        return self.openai_client

    def _validate_api_configurations(self):
        """
        Validates if all necessary configurations are set.

        This method checks if the API key and Azure endpoint are set in the OpenAI client.
        These configurations are necessary for making requests to the OpenAI API.
        If any of these configurations are not set, the method raises a ValueError.

        :raises ValueError: If the API key or Azure endpoint is not set.
        """
        if not all(
            [
                self.openai_client.api_key,
                self.azure_endpoint,
            ]
        ):
            raise ValueError(
                "One or more OpenAI API setup variables are empty. Please review your environment variables and `SETTINGS.md`"
            )

    def generate_completion_response(
        self,
        query: str,
        temperature: float = 0.5,
        max_tokens: int = 100,
        model_name: Optional[str] = None,
        top_p: float = 1.0,
        **kwargs,
    ) -> Optional[str]:
        """
        Generates a text completion using Azure OpenAI's Foundation models.

        :param query: The input text query for the model.
        :param temperature: Controls randomness in the output. Default to 0.5.
        :param max_tokens: Maximum number of tokens to generate. Defaults to 100.
        :param model_name: The name of the AI model to use. Defaults to None.
        :param top_p: The cumulative probability cutoff for token selection. Defaults to 1.0.

        :return: The generated text or None if an error occurs.
        """
        try:
            response = self.openai_client.completions.create(
                model=model_name or self.completion_model_name,
                prompt=query,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                **kwargs,
            )

            completion = response.choices[0].text.strip()
            logger.info(f"Generated completion: {completion}")
            return completion

        except openai.APIConnectionError as e:
            logger.error("The server could not be reached")
            logger.error(e.__cause__)
            return None
        except openai.RateLimitError:
            logger.error("A 429 status code was received; we should back off a bit.")
            return None
        except openai.APIStatusError as e:
            logger.error("Another non-200-range status code was received")
            logger.error(e.status_code)
            logger.error(e.response)
            return None
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return None

    def generate_chat_response(
        self,
        conversation_history: List[Dict[str, str]],
        query: str,
        system_message_content: str = "You are an AI assistant that helps people find information. Please be precise, polite, and concise.",
        temperature: float = 0.7,
        max_tokens: int = 150,
        seed: int = 42,
        top_p: float = 1.0,
        **kwargs,
    ) -> Optional[str]:
        """
        Generates a text response considering the conversation history.

        :param conversation_history: A list of message dictionaries representing the conversation history.
        :param query: The latest query to generate a response for.
        :param system_message_content: The content of the system message. Defaults to "You are an AI assistant that helps people find information. Please be precise, polite, and concise."
        :param temperature: Controls randomness in the output. Defaults to 0.7.
        :param max_tokens: Maximum number of tokens to generate. Defaults to 150.
        :param seed: Random seed for deterministic output. Defaults to 42.
        :param top_p: The cumulative probability cutoff for token selection. Defaults to 1.0.

        :return: The generated text response or None if an error occurs.
        """
        try:
            system_message = {"role": "system", "content": system_message_content}
            if not conversation_history or conversation_history[0] != system_message:
                conversation_history.insert(0, system_message)

            messages_for_api = conversation_history + [
                {"role": "user", "content": query}
            ]
            logger.info(f"Sending request to OpenAI with query: {query}")

            response = self.openai_client.chat.completions.create(
                model=self.chat_model_name,
                messages=messages_for_api,
                temperature=temperature,
                max_tokens=max_tokens,
                seed=seed,
                top_p=top_p,
                **kwargs,
            )

            response_content = response.choices[0].message.content
            logger.info(f"Received response from OpenAI: {response_content}")

            conversation_history.append({"role": "user", "content": query})
            conversation_history.append({"role": "system", "content": response_content})

            return response_content

        except openai.APIConnectionError as e:
            logger.error("The server could not be reached")
            logger.error(e.__cause__)
            return None
        except openai.RateLimitError:
            logger.error("A 429 status code was received; we should back off a bit.")
            return None
        except openai.APIStatusError as e:
            logger.error("Another non-200-range status code was received")
            logger.error(e.status_code)
            logger.error(e.response)
            return None
        except Exception as e:
            logger.error(f"Contextual response generation error: {e}")
            return None

    def generate_embedding(
        self, input_text: str, model_name: Optional[str] = None, **kwargs
    ) -> Optional[str]:
        """
        Generates an embedding for the given input text using Azure OpenAI's Foundation models.

        :param input_text: The text to generate an embedding for.
        :param model_name: The name of the model to use for generating the embedding. If None, the default embedding model is used.
        :param kwargs: Additional parameters for the API request.
        :return: The embedding as a string, or None if an error occurred.
        :raises Exception: If an error occurs while making the API request.
        """
        try:
            response = self.openai_client.embeddings.create(
                input=input_text,
                model=model_name or self.embedding_model_name,
                **kwargs,
            )

            embedding = response.data[0].embedding
            logger.debug(f"Created embedding: {response.model_dump_json(indent=2)}")
            return embedding

        except openai.APIConnectionError as e:
            logger.error("The server could not be reached")
            logger.error(e.__cause__)
            return None
        except openai.RateLimitError:
            logger.error("A 429 status code was received; we should back off a bit.")
            return None
        except openai.APIStatusError as e:
            logger.error("Another non-200-range status code was received")
            logger.error(e.status_code)
            logger.error(e.response)
            return None
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return None
