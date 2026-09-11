import pytest
from app.models.analysis_models import JobRequirementsSchema
from app.services.matching_service import SkillMatchingService
from app.utils.synonyms import canonicalize_skill, normalize_skill_name


class TestSkillCanonicalization:
    """Unit tests for multi-stage skill normalization and alias resolution."""

    def test_whitespace_and_case_folding(self):
        """Validates that skill names are stripped and lowercased."""
        assert normalize_skill_name("  Python  ") == "python"
        assert normalize_skill_name("  NODE.JS  ") == "nodejs"
        assert normalize_skill_name("React.js") == "reactjs"

    def test_synonym_and_alias_mapping(self):
        """Validates canonicalization against extensible synonym/alias table."""
        test_cases = [
            ("postgres", "postgresql"),
            ("pgsql", "postgresql"),
            ("py", "python"),
            ("k8s", "kubernetes"),
            ("golang", "go"),
            ("reactjs", "react"),
            ("react.js", "react"),
            ("ts", "typescript"),
            ("js", "javascript"),
            ("node.js", "nodejs"),
            ("docker-compose", "docker"),
            ("gcp", "google cloud platform"),
            ("aws", "amazon web services"),
        ]
        for raw, expected in test_cases:
            assert canonicalize_skill(raw) == expected

    def test_fuzzy_matching_via_rapidfuzz(self):
        """Validates fuzzy matching for typos/near-misses with >= 88% score."""
        service = SkillMatchingService()
        # "kubernets" (typo) should match "Kubernetes"
        assert service.is_skill_match("kubernets", "Kubernetes")
        # "postgresql database" should match "PostgreSQL"
        assert service.is_skill_match("postgresql database", "PostgreSQL")
        # Unrelated skills should not match
        assert not service.is_skill_match("Python", "Java")
        assert not service.is_skill_match("Rust", "Ruby")


class TestScoringFormulaAndEdgeCases:
    """Unit tests for deterministic mathematical match score calculation."""

    @pytest.fixture
    def matching_service(self):
        return SkillMatchingService()

    def test_standard_weighted_scoring_formula(self, matching_service):
        """Validates formula: (matched_req/tot_req*70) + (matched_pref/tot_pref*30)."""
        job = JobRequirementsSchema(
            job_title="Backend Intern",
            company_name="Acme Corp",
            required_technical_skills=["Python", "FastAPI", "PostgreSQL", "Git"],
            preferred_technical_skills=["Docker", "Kubernetes"],
            raw_summary="Backend internship focused on Python and APIs.",
        )
        # Student has: Python, Git, PostgreSQL (3/4 req = 75%), Docker (1/2 pref = 50%)
        # Expected: (0.75 * 70) + (0.50 * 30) = 52.5 + 15.0 = 67.5%
        student_skills = ["Python", "Git", "PostgreSQL", "Docker"]
        result = matching_service.analyze_skill_gap(job, student_skills)

        assert result.match_score_percentage == 67.5
        assert result.score_breakdown.required_skills_match_ratio == 0.75
        assert result.score_breakdown.preferred_skills_match_ratio == 0.50
        assert result.score_breakdown.required_skills_weight == 70.0
        assert result.score_breakdown.preferred_skills_weight == 30.0

    def test_zero_preferred_skills_edge_case(self, matching_service):
        """Validates zero preferred skills allocates 100% weight to required."""
        job = JobRequirementsSchema(
            job_title="Software Intern",
            company_name="Tech Corp",
            required_technical_skills=["Python", "FastAPI", "PostgreSQL", "Git"],
            preferred_technical_skills=[],  # Zero preferred skills
            raw_summary="Software intern role.",
        )
        # Student has 3 of 4 required skills -> 3/4 * 100 = 75.0%
        student_skills = ["Python", "FastAPI", "Git"]
        result = matching_service.analyze_skill_gap(job, student_skills)

        assert result.match_score_percentage == 75.0
        assert result.score_breakdown.required_skills_weight == 100.0
        assert result.score_breakdown.preferred_skills_weight == 0.0
        assert result.score_breakdown.preferred_skills_match_ratio == 0.0

    def test_zero_required_skills_edge_case(self, matching_service):
        """Validates zero required skills handled safely without zero division."""
        job = JobRequirementsSchema(
            job_title="Exploratory Intern",
            company_name="Tech Corp",
            required_technical_skills=[],
            preferred_technical_skills=["Python", "Go"],
            raw_summary="Exploratory role.",
        )
        student_skills = ["Python"]
        result = matching_service.analyze_skill_gap(job, student_skills)

        assert result.match_score_percentage == 50.0
        assert result.score_breakdown.required_skills_weight == 0.0
        assert result.score_breakdown.preferred_skills_weight == 100.0

    def test_all_zero_skills_edge_case(self, matching_service):
        """Validates empty job requirements produce a 0.0% score safely."""
        job = JobRequirementsSchema(
            job_title="Empty Requirements Role",
            company_name="Tech Corp",
            required_technical_skills=[],
            preferred_technical_skills=[],
            raw_summary="Empty role.",
        )
        result = matching_service.analyze_skill_gap(job, ["Python", "Go"])
        assert result.match_score_percentage == 0.0

    def test_empty_student_skills(self, matching_service):
        """Validates empty candidate skill list yields 0.0% score."""
        job = JobRequirementsSchema(
            job_title="Backend Intern",
            company_name="Acme Corp",
            required_technical_skills=["Python", "Go"],
            preferred_technical_skills=["Docker"],
            raw_summary="Backend intern role.",
        )
        result = matching_service.analyze_skill_gap(job, [])
        assert result.match_score_percentage == 0.0
        assert len(result.matched_required_skills) == 0
        assert len(result.matched_preferred_skills) == 0
        assert result.missing_required_skills == ["Python", "Go"]
        assert result.missing_preferred_skills == ["Docker"]

    def test_alias_and_fuzzy_matching_in_full_evaluation(self, matching_service):
        """Validates alias and fuzzy inputs match job requirements accurately."""
        job = JobRequirementsSchema(
            job_title="Cloud Engineer Intern",
            company_name="Cloud Solutions",
            required_technical_skills=["PostgreSQL", "Python", "Kubernetes"],
            preferred_technical_skills=["React", "Golang"],
            raw_summary="Cloud engineer role.",
        )
        # Student provides aliases and minor variations:
        # postgres -> PostgreSQL, py -> Python, k8s -> Kubernetes, reactjs -> React
        student_skills = ["postgres", "py", "k8s", "reactjs", "go"]
        result = matching_service.analyze_skill_gap(job, student_skills)

        assert result.match_score_percentage == 100.0
        assert set(result.matched_required_skills) == {
            "PostgreSQL",
            "Python",
            "Kubernetes",
        }
        assert set(result.matched_preferred_skills) == {"React", "Golang"}
        assert len(result.missing_required_skills) == 0
        assert len(result.missing_preferred_skills) == 0


class TestOutputCategorizationAndRoadmap:
    """Unit tests for categorization buckets and prioritized learning roadmap."""

    @pytest.fixture
    def matching_service(self):
        return SkillMatchingService()

    def test_categorization_buckets(self, matching_service):
        """Verifies skills are accurately placed in the 4 output buckets."""
        job = JobRequirementsSchema(
            job_title="Full Stack Intern",
            company_name="Acme",
            required_technical_skills=["TypeScript", "React", "Node.js", "SQL"],
            preferred_technical_skills=["GraphQL", "AWS", "Docker"],
            raw_summary="Full stack role.",
        )
        student_skills = ["ts", "reactjs", "aws"]
        result = matching_service.analyze_skill_gap(job, student_skills)

        assert result.matched_required_skills == ["TypeScript", "React"]
        assert result.missing_required_skills == ["Node.js", "SQL"]
        assert result.matched_preferred_skills == ["AWS"]
        assert result.missing_preferred_skills == ["GraphQL", "Docker"]

    def test_preparation_roadmap_ordering(self, matching_service):
        """Verifies Critical Required missing skills precede High-Value Preferred."""
        job = JobRequirementsSchema(
            job_title="Backend Intern",
            company_name="Acme",
            required_technical_skills=["Python", "FastAPI", "SQL"],
            preferred_technical_skills=["Redis", "Kafka", "Docker"],
            raw_summary="Backend role.",
        )
        # Missing required: FastAPI, SQL
        # Missing preferred: Redis, Kafka
        student_skills = ["Python", "Docker"]
        result = matching_service.analyze_skill_gap(job, student_skills)

        roadmap = result.priority_learning_roadmap
        assert len(roadmap) == 4

        # Verify priority numbers are strictly sequential starting at 1
        priorities = [item.priority for item in roadmap]
        assert priorities == [1, 2, 3, 4]

        # Verify all Critical Required items precede High-Value Preferred items
        categories = [item.category for item in roadmap]
        assert categories == [
            "Critical Required",
            "Critical Required",
            "High-Value Preferred",
            "High-Value Preferred",
        ]

        roadmap_skills = [item.skill for item in roadmap]
        assert roadmap_skills == ["FastAPI", "SQL", "Redis", "Kafka"]
