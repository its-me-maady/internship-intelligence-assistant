from typing import List, Optional

from pydantic import BaseModel, Field


class JobRequirementsSchema(BaseModel):
    """Structured extraction schema for internship job descriptions.

    Matches PRD Section FR-5 schema fields verbatim.
    """

    job_title: str = Field(
        ...,
        description="The title of the internship position.",
    )
    company_name: Optional[str] = Field(
        default=None,
        description="Name of the hiring company or organization.",
    )
    location: Optional[str] = Field(
        default=None,
        description="Geographic location or remote policy.",
    )
    work_type: Optional[str] = Field(
        default=None,
        description="Work arrangement mode: 'On-site', 'Remote', or 'Hybrid'.",
    )
    stipend_or_salary: Optional[str] = Field(
        default=None,
        description="Stipend, hourly rate, or compensation range.",
    )
    duration_weeks: Optional[int] = Field(
        default=None,
        description="Duration of the internship in weeks (e.g. 12).",
    )
    application_deadline: Optional[str] = Field(
        default=None,
        description="Application closing date if specified.",
    )
    required_technical_skills: List[str] = Field(
        default_factory=list,
        description="Mandatory technical skills, languages, and tools.",
    )
    preferred_technical_skills: List[str] = Field(
        default_factory=list,
        description="Nice-to-have or preferred technical competencies.",
    )
    required_soft_skills: List[str] = Field(
        default_factory=list,
        description="Mandatory communication and interpersonal skills.",
    )
    minimum_education: Optional[str] = Field(
        default=None,
        description="Degree level or academic enrollment requirement.",
    )
    expected_graduation_years: List[str] = Field(
        default_factory=list,
        description="Eligible graduation years (e.g. ['2026', '2027']).",
    )
    minimum_gpa: Optional[str] = Field(
        default=None,
        description="Minimum GPA requirement if specified in the posting.",
    )
    prior_experience_required: Optional[str] = Field(
        default=None,
        description="Prior work, research, or personal project expectations.",
    )
    key_responsibilities: List[str] = Field(
        default_factory=list,
        description="Key responsibilities and daily engineering tasks.",
    )
    raw_summary: str = Field(
        ...,
        description="Executive 1-2 sentence summary of the internship posting.",
    )
