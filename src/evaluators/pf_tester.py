import os
from typing import Any, List, Optional

import promptflow as pf
from dotenv import load_dotenv

from utils.ml_logging import get_logger

# Initialize logging
logger = get_logger()


class PromptFlowManagerEvaluator:
    """
    A class to interact with the PromptFlow API for evaluation.

    Attributes:
        eval_flow (str): The path to the evaluation flow file.
        cli (pf.PFClient): An instance of PFClient.
    """

    def __init__(
        self,
        eval_flow: Optional[str] = None,
    ):
        """
        Initialize the PromptFlowManagerEvaluator class with evaluation flow file path.

        :param eval_flow: The path to the evaluation flow file.
        """
        self.eval_flow = eval_flow
        self.cli = pf.PFClient()

        if self.eval_flow is None:
            self.load_environment_variables_from_env_file()

    # def check_connection(self) -> bool:
    #     self.api_key = os.getenv("OPENAI_API_KEY")
    #     self.api_base = os.getenv("OPENAI_API_ENDPOINT")
    #     self.connection_name = "open_ai_connection"

    #     if not self.check_connection():
    #         raise Exception("Failed to establish connection.")

    def load_environment_variables_from_env_file(self):
        """
        Loads required environment variables for the application from a .env file.

        This method should be called explicitly if environment variables are to be loaded from a .env file.
        """
        load_dotenv()

        self.eval_flow = os.getenv("EVAL_FLOW")

        # Check if eval_flow exists as a directory
        if not os.path.exists(self.eval_flow):
            raise ValueError(f"EVAL_FLOW directory does not exist: {self.eval_flow}")

        # Check for any missing required environment variables
        required_vars = {
            "EVAL_FLOW": self.eval_flow,
        }

        missing_vars = [var for var, value in required_vars.items() if not value]

        if missing_vars:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )

    def run_promptflow_evaluations(
        self, chat_history: List[str], question: str, answer: str, context: str
    ) -> Any:
        """
        Creates an instance of PFClient, calls the test method with provided arguments, and returns the result.

        Parameters:
        chat_history (List[str]): The chat history to be passed to the test method.
        question (str): The question to be passed to the test method.
        answer (str): The answer to be passed to the test method.
        context (str): The context to be passed to the test method.

        Returns:
        Any: The result returned from the test method of PFClient.
        """

        try:
            # Call the test method and get the result
            result = self.cli.test(
                self.eval_flow,
                inputs=dict(
                    chat_history=chat_history,
                    question=question,
                    answer=answer,
                    context=context,
                ),
            )

            # Log the result
            logger.info(f"Test result: {result}")

            return result
        except Exception as e:
            logger.error(f"An error occurred while testing: {e}")
            raise
