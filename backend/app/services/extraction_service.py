import logging
from typing import Optional

from app.models.analysis_models import JobRequirementsSchema
from app.services import llm_service
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)

STRUCTURED_EXTRACTION_SYSTEM_PROMPT = (
    "You are a precision information extraction engine for technical job "
    "descriptions.\n"
    "Extract all relevant internship parameters from the provided document text "
    "into the exact JSON schema requested.\n"
    "Do not infer skills that are not explicitly stated or directly required by "
    "listed tools.\n"
    "Distinguish strictly between MUST-HAVE (required) skills and NICE-TO-HAVE "
    "(preferred) skills."
)


class ExtractionService:
    """Extracts structured requirements and parameters from JDs."""

    def __init__(
        self,
        llm: Optional[BaseChatModel] = None,
        max_retries: int = 2,
    ):
        self._llm = llm
        self.max_retries = max_retries

    @property
    def llm(self) -> BaseChatModel:
        if self._llm is not None:
            return self._llm
        return llm_service.get_llm()

    def extract_job_requirements(self, text: str) -> JobRequirementsSchema:
        """Extracts structured JobRequirementsSchema with validation retries."""
        structured_llm = self.llm.with_structured_output(JobRequirementsSchema)
        messages = [
            SystemMessage(content=STRUCTURED_EXTRACTION_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"Job Description Document:\n\n{text}\n\n"
                    "Extract the structured parameters."
                )
            ),
        ]

        last_exception: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                result = structured_llm.invoke(messages)
                if isinstance(result, JobRequirementsSchema):
                    return result
                elif isinstance(result, dict):
                    return JobRequirementsSchema(**result)
                else:
                    raise ValueError(
                        f"Unexpected extraction result type: {type(result)}"
                    )
            except Exception as exc:
                last_exception = exc
                logger.warning(
                    f"Extraction attempt {attempt}/{self.max_retries} failed: {exc}"
                )

        raise ValueError(
            f"Failed to extract structured job requirements after "
            f"{self.max_retries} attempts: {last_exception}"
        )


# Global singleton instance
extraction_service = ExtractionService()
