import base64
import os
from typing import Dict, List, Optional, Union

import requests
from dotenv import load_dotenv
from IPython.display import Image, display
from requests.exceptions import RequestException

from src.extractors.blob_data_extractor import AzureBlobDataExtractor
from utils.ml_logging import get_logger

# Initialize logging
logger = get_logger()


class GPT4VisionManager:
    """
    A class to interact with the GPT-4 Vision API, including OCR and Azure Computer Vision enhancements.

    Attributes:
        openai_api_base (str): Base URL for OpenAI API.
        deployment_name (str): Name of the deployment.
        openai_api_version (str): API version.
        openai_api_key (str): OpenAI API key.
    """

    def __init__(
        self,
        openai_api_base: Optional[str] = None,
        deployment_name: Optional[str] = None,
        openai_api_version: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        container_name: Optional[str] = None,
    ):
        """
        Initialize the GPT4Vision class with OpenAI API configurations.

        :param openai_api_base: Base URL for OpenAI API.
        :param deployment_name: Name of the deployment.
        :param openai_api_version: API version.
        :param openai_api_key: OpenAI API key.
        :param container_client: Azure Container Client specific to the container.
        """
        self.openai_api_base = openai_api_base
        self.deployment_name = deployment_name
        self.openai_api_version = openai_api_version
        self.openai_api_key = openai_api_key
        if not self.openai_api_base or not self.openai_api_key:
            self.load_environment_variables_from_env_file()

        self.blob_manager = AzureBlobDataExtractor(container_name=container_name)

    def load_environment_variables_from_env_file(self):
        """
        Loads required environment variables for the application from a .env file.

        This method should be called explicitly if environment variables are to be loaded from a .env file.
        """
        load_dotenv()

        self.openai_api_base = os.getenv("AZURE_OPENAI_ENDPOINT_VISION")
        self.deployment_name = os.getenv("AZURE_OPENAI_API_DEPLOYMENT_NAME_VISION")
        self.openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION_VISION")
        self.openai_api_key = os.getenv("AZURE_OPENAI_API_KEY_VISION")

        # Check for any missing required environment variables
        required_vars = {
            "OPENAI_API_BASE": self.openai_api_base,
            "DEPLOYMENT_NAME": self.deployment_name,
            "OPENAI_API_VERSION": self.openai_api_version,
            "OPENAI_API_KEY": self.openai_api_key,
        }

        missing_vars = [var for var, value in required_vars.items() if not value]

        if missing_vars:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )

    @staticmethod
    def _prepare_system_message(system_text: str) -> Dict:
        """
        Prepares the system message for the GPT-4 Vision API call.

        :param system_text: The system text message.
        :return: A dictionary formatted as a system message.
        """
        return {"role": "system", "content": [{"type": "text", "text": system_text}]}

    @staticmethod
    def _prepare_user_message(user_text: str) -> Dict:
        """
        Prepares the user message for the GPT-4 Vision API call. (Internal method)

        :param user_text: The user text prompt.
        :return: A dictionary formatted as a user message.
        """
        return {"role": "user", "content": [{"type": "text", "text": user_text}]}

    @staticmethod
    def _encode_image_to_base64(image_file_path: str) -> str:
        """
        Encode an image file to base64. (Internal method)

        :param image_file_path: Path to the image file.
        :return: Base64 encoded string of the image.
        :raises FileNotFoundError: If the image file is not found.
        """
        try:
            with open(image_file_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        except FileNotFoundError as e:
            logger.error(f"Image file not found: {e}")
            raise

    @staticmethod
    def _encode_bytes_to_base64(image_bytes: bytes) -> str:
        """
        Encode image bytes to base64. (Internal method)

        :param image_bytes: Bytes of the image.
        :return: Base64 encoded string of the image.
        """
        return base64.b64encode(image_bytes).decode("utf-8")

    def prepare_instruction(self, system_text: str, user_text: str) -> List[Dict]:
        """
        Prepares the complete message structure for the GPT-4 Vision API call.

        :param system_text: The system text message.
        :param user_text: The user text prompt.
        :return: A list of dictionaries formatted as messages for the GPT-4 Vision API.
        """
        logger.info("Preparing instruction for GPT-4 Vision API call.")
        system_message = self._prepare_system_message(system_text)
        user_message = self._prepare_user_message(user_text)
        self.messages = [system_message, user_message]
        logger.info(f"Instruction: {self.messages}")
        return self.messages

    def _validate_message_structure(self, messages: List[Dict]) -> bool:
        """
        Validates the structure of the messages list of dictionaries.

        :param messages: The messages list of dictionaries to be validated.
        :return: A boolean indicating whether the structure of the messages is valid.
        """
        for message in messages:
            if not all(key in message for key in ["role", "content"]):
                return False
            for content in message["content"]:
                if not any(key in content for key in ["type", "text"]):
                    return False
        return True

    def add_image_url_to_user_message(
        self, image_url: str, message: Optional[Dict] = None
    ) -> Dict:
        """
        Adds the image URL to the user message.

        :param image_url: The URL of the image to be processed.
        :param message: The user message to which the image URL will be added.
        :return: The updated user message with the image URL added.
        """
        try:
            if message is None and self.messages is None:
                raise ValueError("No message provided to add the image URL to.")
            else:
                self.messages = message if message is not None else self.messages

            if not self._validate_message_structure(self.messages):
                raise ValueError("Invalid message structure.")

            self.messages[-1]["content"].append(
                {"type": "image_url", "image_url": {"url": image_url}}
            )
            logger.info("Image URL added to user message successfully.")

            return self.messages
        except Exception as e:
            logger.error(
                f"An error occurred while adding the image URL to the user message: {e}"
            )
            raise

    def call_gpt4v_image(
        self,
        image_file_paths: Union[str, List[str]],
        system_instruction: Optional[str] = None,
        user_instruction: Optional[str] = None,
        ocr: bool = False,
        grounding: bool = False,
        in_context: Optional[Dict] = None,
        use_vision_api: bool = False,
        temperature: float = 0.7,
        top_p: float = 0.95,
        max_tokens: int = 1000,
        seed: int = 5555,
        model_version: str = "gpt-4-vision-preview",
        display_image: bool = False,
    ) -> Dict:
        """
        Make an API call to the GPT-4 Vision model with optional OCR, grounding, and Azure Computer Vision API enhancements.

        :param image_file_path: Path to the image file to be processed.
        :param system_instruction: Optional system instruction text to guide the model's response.
        :param user_instruction: Optional user instruction text to guide the model's response.
        :param ocr: Optional boolean flag indicating whether to use OCR (Optical Character Recognition) to extract text from the image.
        :param grounding: Optional boolean flag indicating whether to use grounding to relate the text and image data.
        :param in_context: Optional dictionary containing context information to be included in the API call.
        :param use_vision_api: Optional boolean flag indicating whether to use Azure Computer Vision API to enhance the image processing.
        :param temperature: Optional float parameter for the GPT-4 model that controls the randomness of the model's output.
                        Higher values produce more random outputs.
        :param top_p: Optional float parameter for the GPT-4 model that controls the nucleus sampling method used by the model.
                        Lower values make the output more focused.
        :param max_tokens: Optional integer parameter for the GPT-4 model that sets the maximum number of tokens in the model's output.
        :param seed: Optional parameter for the GPT-4 model that sets the seed for the random number generator.
                        Using the same seed will ensure that the model produces the same output for the same input.
        :param model_version: Optional string parameter specifying the version of the GPT-4 Vision model to use.
        :param display_image: Optional boolean flag indicating whether to display the image.
        :return: A dictionary containing the response from the GPT-4 Vision API call. The dictionary includes the model's output
                    and any other information returned by the API.
        """
        try:
            if system_instruction is not None or user_instruction is not None:
                self.prepare_instruction(system_instruction, user_instruction)

            if isinstance(image_file_paths, str):
                image_file_paths = [image_file_paths]

            for image_file_path in image_file_paths:
                if image_file_path.startswith(("http://", "https://")):
                    if image_file_path.startswith("http://"):
                        raise ValueError(
                            "HTTP URLs are not supported. Please use HTTPS."
                        )
                    # If it's an HTTPS URL but contains "blob.core.windows.net", process it as a blob
                    elif "blob.core.windows.net" in image_file_path:
                        logger.info("Blob URL detected. Extracting content.")
                        content_bytes = self.blob_manager.extract_content(
                            image_file_path
                        )
                        encoded_image = self._encode_bytes_to_base64(content_bytes)
                else:
                    encoded_image = self._encode_image_to_base64(image_file_path)

                image_url = f"data:image/jpeg;base64,{encoded_image}"
                self.add_image_url_to_user_message(image_url)

            if use_vision_api:
                azure_endpoint_vision = os.getenv("AZURE_ENDPOINT_VISION")
                azure_key_vision = os.getenv("AZURE_KEY_VISION")

                if not azure_endpoint_vision or not azure_key_vision:
                    logger.error(
                        "Missing required Azure Computer Vision environment variables."
                    )
                    raise SystemExit(
                        "Missing required Azure Computer Vision environment variables."
                    )

                vision_api_config = {
                    "endpoint": azure_endpoint_vision,
                    "key": azure_key_vision,
                }

            if not all(
                [
                    self.openai_api_base,
                    self.deployment_name,
                    self.openai_api_version,
                    self.openai_api_key,
                ]
            ):
                raise SystemExit(
                    "Missing required OpenAI environment variables. Please call the function load_environment_variables_from_env_file"
                )

            api_url = f"{self.openai_api_base}/openai/deployments/{self.deployment_name}/{'extensions/' if ocr or grounding else ''}chat/completions?api-version={self.openai_api_version}"

            # Log the request
            logger.info(f"Sending request to {api_url}")

            # Payload setup
            payload = {
                "model": model_version,
                "messages": self.messages,
                "temperature": temperature,
                "top_p": top_p,
                "max_tokens": max_tokens,
                "seed": seed,
            }

            # HTTP headers
            headers = {
                "Content-Type": "application/json",
                "api-key": self.openai_api_key,
            }

            if ocr or grounding:
                payload["enhancements"] = {
                    "ocr": {"enabled": ocr},
                    "grounding": {"enabled": grounding},
                }

            data_sources = []

            if in_context is not None:
                data_sources.append(
                    {"type": "AzureCognitiveSearch", "parameters": in_context}
                )

            if use_vision_api:
                data_sources.append(
                    {"type": "AzureComputerVision", "parameters": vision_api_config}
                )

            if data_sources:
                payload["dataSources"] = data_sources

            # Send the request
            response = requests.post(api_url, headers=headers, json=payload)
            response.raise_for_status()
            logger.info("Request successful.")
            content = response.json()["choices"][0]["message"]["content"]

            if display_image:
                display(Image(image_file_path))

            return content

        except RequestException as e:
            logger.error(f"Failed to make the request. Error: {e}")
            raise SystemExit(f"Failed to make the request. Error: {e}")
