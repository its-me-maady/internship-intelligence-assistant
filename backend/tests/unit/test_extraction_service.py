from typing import Any, List

import pytest
from app.models.analysis_models import JobRequirementsSchema
from app.services.extraction_service import ExtractionService
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult

SAMPLE_JD_TEXT = """
Role: Backend Engineering Intern
Company: Acme Cloud Corp
Location: San Francisco, CA / Hybrid
Work Type: Hybrid
Compensation: $45 - $55 / hour
Duration: 12 weeks
Application Deadline: November 15, 2026

About the Role:
A 12-week summer backend internship focusing on Python microservices.

Requirements:
- Must have strong programming skills in Python, FastAPI, PostgreSQL, and Git.
- Preferred skills: Docker, Kubernetes, Redis, AWS.
- Soft skills: Team communication, Autonomous problem solving.
- Education: Currently pursuing B.S. or M.S. in Computer Science or STEM.
- Expected Graduation: 2026 or 2027.
- Minimum GPA: 3.0 or equivalent.
- Experience: No prior full-time experience required; personal projects expected.

Responsibilities:
- Design and implement RESTful microservices in Python
- Optimize PostgreSQL database queries and schemas
- Participate in daily agile standups and code reviews
"""

EXPECTED_DATA = {
    "job_title": "Backend Engineering Intern",
    "company_name": "Acme Cloud Corp",
    "location": "San Francisco, CA / Hybrid",
    "work_type": "Hybrid",
    "stipend_or_salary": "$45 - $55 / hour",
    "duration_weeks": 12,
    "application_deadline": "November 15, 2026",
    "required_technical_skills": ["Python", "FastAPI", "PostgreSQL", "Git"],
    "preferred_technical_skills": ["Docker", "Kubernetes", "Redis", "AWS"],
    "required_soft_skills": [
        "Team communication",
        "Autonomous problem solving",
    ],
    "minimum_education": (
        "Currently pursuing B.S. or M.S. in Computer Science or STEM"
    ),
    "expected_graduation_years": ["2026", "2027"],
    "minimum_gpa": "3.0 or equivalent",
    "prior_experience_required": (
        "No prior full-time experience required; personal projects expected"
    ),
    "key_responsibilities": [
        "Design and implement RESTful microservices in Python",
        "Optimize PostgreSQL database queries and schemas",
        "Participate in daily agile standups and code reviews",
    ],
    "raw_summary": (
        "A 12-week summer backend internship focusing on Python microservices."
    ),
}


class MockExtractionChatModel(BaseChatModel):
    """Mock LLM returning valid or invalid structured responses for testing."""

    return_valid: bool = True
    attempts_before_success: int = 0
    call_count: int = 0

    def with_structured_output(self, schema, **kwargs):
        class StructuredRunnable:
            def __init__(self, parent):
                self.parent = parent

            def invoke(self, input_messages, **run_kwargs):
                self.parent.call_count += 1
                if self.parent.call_count <= self.parent.attempts_before_success:
                    raise ValueError("Simulated malformed LLM extraction output")
                if not self.parent.return_valid:
                    raise ValueError("Malformed output that fails validation")
                return schema(**EXPECTED_DATA)

        return StructuredRunnable(self)

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Any = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        generation = ChatGeneration(message=AIMessage(content="{}"))
        return ChatResult(generations=[generation])

    @property
    def _llm_type(self) -> str:
        return "mock-extraction-model"


class TestExtractionService:
    """Unit tests for ExtractionService structured extraction and validation."""

    def test_extract_returns_validated_pydantic_schema(self):
        mock_llm = MockExtractionChatModel(return_valid=True)
        service = ExtractionService(llm=mock_llm)

        result = service.extract_job_requirements(SAMPLE_JD_TEXT)

        assert isinstance(result, JobRequirementsSchema)
        assert result.job_title == "Backend Engineering Intern"
        assert result.company_name == "Acme Cloud Corp"
        assert result.work_type == "Hybrid"
        assert result.duration_weeks == 12
        assert "Python" in result.required_technical_skills
        assert "Docker" in result.preferred_technical_skills
        assert "2026" in result.expected_graduation_years
        assert len(result.key_responsibilities) == 3

    def test_missing_optional_fields_default_to_none_or_empty(self):
        minimal_data = {
            "job_title": "Software Intern",
            "raw_summary": "Minimal internship posting without compensation.",
        }
        schema_obj = JobRequirementsSchema(**minimal_data)
        assert schema_obj.company_name is None
        assert schema_obj.location is None
        assert schema_obj.work_type is None
        assert schema_obj.stipend_or_salary is None
        assert schema_obj.duration_weeks is None
        assert schema_obj.application_deadline is None
        assert schema_obj.required_technical_skills == []
        assert schema_obj.preferred_technical_skills == []
        assert schema_obj.required_soft_skills == []
        assert schema_obj.minimum_education is None
        assert schema_obj.expected_graduation_years == []
        assert schema_obj.minimum_gpa is None
        assert schema_obj.prior_experience_required is None
        assert schema_obj.key_responsibilities == []

    def test_extraction_retries_on_initial_failure_and_succeeds(self):
        # Fails on 1st attempt, succeeds on 2nd attempt
        mock_llm = MockExtractionChatModel(return_valid=True, attempts_before_success=1)
        service = ExtractionService(llm=mock_llm, max_retries=2)

        result = service.extract_job_requirements(SAMPLE_JD_TEXT)

        assert mock_llm.call_count == 2
        assert result.job_title == "Backend Engineering Intern"

    def test_extraction_raises_after_exceeding_max_retries(self):
        # Fails continuously
        mock_llm = MockExtractionChatModel(return_valid=False)
        service = ExtractionService(llm=mock_llm, max_retries=2)

        with pytest.raises(
            ValueError, match="Failed to extract structured job requirements"
        ):
            service.extract_job_requirements(SAMPLE_JD_TEXT)
        assert mock_llm.call_count == 2
