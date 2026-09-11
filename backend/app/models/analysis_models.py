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


class ScoreBreakdown(BaseModel):
    """Breakdown of weights and match ratios in the mathematical formula."""

    required_skills_weight: float = Field(
        default=70.0,
        description="Weight percentage allocated to required skills.",
    )
    required_skills_match_ratio: float = Field(
        default=0.0,
        description="Ratio of matched required skills.",
    )
    preferred_skills_weight: float = Field(
        default=30.0,
        description="Weight percentage allocated to preferred skills.",
    )
    preferred_skills_match_ratio: float = Field(
        default=0.0,
        description="Ratio of matched preferred skills.",
    )
    formula: str = Field(
        default="",
        description="Explanatory formula string showing the computation.",
    )


class RoadmapItem(BaseModel):
    """Actionable learning recommendation for an unfulfilled skill gap."""

    skill: str = Field(..., description="The missing technical skill.")
    category: str = Field(
        ...,
        description="Importance tier: 'Critical Required' or 'High-Value Preferred'.",
    )
    priority: int = Field(
        ...,
        description="Priority index (1 = highest priority).",
    )
    estimated_study_hours: int = Field(
        default=10,
        description="Estimated study hours to acquire working familiarity.",
    )
    recommended_focus: str = Field(
        default="Core fundamentals, syntax, key frameworks, and projects.",
        description="Recommended focus areas and learning topics.",
    )


class SkillGapAnalysisRequest(BaseModel):
    """Request schema for deterministic skill gap analysis."""

    document_id: str = Field(
        ...,
        description="ID of the ingested internship document.",
    )
    user_skills: List[str] = Field(
        default_factory=list,
        description="List of technical skills possessed by the student.",
    )


class SkillGapAnalysisResponse(BaseModel):
    """Response schema for deterministic skill gap and match scoring analysis."""

    match_score_percentage: float = Field(
        ...,
        description="Deterministic overall match percentage (0.0 to 100.0).",
    )
    score_breakdown: ScoreBreakdown = Field(
        ...,
        description="Component breakdown of the match score calculation.",
    )
    matched_required_skills: List[str] = Field(
        default_factory=list,
        description="Mandatory required skills satisfied by the candidate.",
    )
    missing_required_skills: List[str] = Field(
        default_factory=list,
        description="Mandatory required skills missing (critical gaps).",
    )
    matched_preferred_skills: List[str] = Field(
        default_factory=list,
        description="Preferred skills satisfied by the candidate (bonus points).",
    )
    missing_preferred_skills: List[str] = Field(
        default_factory=list,
        description="Preferred skills missing (nice to have).",
    )
    priority_learning_roadmap: List[RoadmapItem] = Field(
        default_factory=list,
        description="Prioritized roadmap of missing skills ordered by importance.",
    )
