from typing import List, Tuple

from app.models.analysis_models import (
    JobRequirementsSchema,
    RoadmapItem,
    ScoreBreakdown,
    SkillGapAnalysisResponse,
)
from app.utils.synonyms import canonicalize_skill
from rapidfuzz import fuzz


class SkillMatchingService:
    """Deterministic skill gap analysis and mathematical scoring engine.

    Implements multi-stage normalization, alias resolution, RapidFuzz token
    similarity, and the weighted formula specified in PRD Section FR-6.
    """

    SIMILARITY_THRESHOLD: float = 88.0

    SKILL_TOPIC_FOCUS = {
        "python": "Data structures, standard library, decorators, generators, async.",
        "fastapi": "Async routes, Pydantic validation, dependency injection, OpenAPI.",
        "postgresql": "ACID transactions, indexing, complex joins, and schema design.",
        "sql": "Query optimization, indexing, aggregations, window functions.",
        "docker": "Dockerfile multi-stage builds, networking, volumes, compose.",
        "kubernetes": "Pods, Deployments, Services, ConfigMaps, Ingress, Helm.",
        "redis": "In-memory data structures, caching patterns, pub/sub, TTL.",
        "git": "Branching workflows, rebasing, merge conflict resolution.",
        "react": "Component lifecycle, React hooks (useState, useEffect), state.",
        "typescript": "Generics, utility types, strict type checking, interfaces.",
        "go": "Goroutines, channels, interfaces, error handling, microservices.",
        "c++": "Memory management, pointers, STL algorithms, move semantics, RAII.",
        "java": "OOP principles, JVM memory model, multithreading, Spring Boot.",
        "aws": "Core compute (EC2/Lambda), storage (S3), IAM, cloud patterns.",
        "pytorch": "Tensors, autograd, Dataset/DataLoader, architectures, GPU.",
    }

    def is_skill_match(self, student_skill: str, target_skill: str) -> bool:
        """Determines whether a candidate skill matches a job requirement.

        Evaluates through:
        1. Exact match after canonicalization and alias substitution.
        2. RapidFuzz token sort ratio (threshold >= 88%).
        3. RapidFuzz token set ratio for compound skill descriptions.
        """
        if not student_skill or not target_skill:
            return False

        c_student = canonicalize_skill(student_skill)
        c_target = canonicalize_skill(target_skill)

        # 1. Exact canonical string match
        if c_student == c_target:
            return True

        # 2. Token sort ratio fuzzy matching
        sort_score = fuzz.token_sort_ratio(c_student, c_target)
        if sort_score >= self.SIMILARITY_THRESHOLD:
            return True

        # 3. Token set ratio for compound / multi-word phrases
        set_score = fuzz.token_set_ratio(c_student, c_target)
        if set_score >= self.SIMILARITY_THRESHOLD:
            return True

        return False

    def find_matching_skills(
        self, target_skills: List[str], candidate_skills: List[str]
    ) -> Tuple[List[str], List[str]]:
        """Categorizes a target skill list into matched and missing subsets."""
        matched: List[str] = []
        missing: List[str] = []

        for target in target_skills:
            is_matched = any(
                self.is_skill_match(candidate, target) for candidate in candidate_skills
            )
            if is_matched:
                matched.append(target)
            else:
                missing.append(target)

        return matched, missing

    def _create_roadmap_item(
        self, skill: str, category: str, priority: int
    ) -> RoadmapItem:
        """Constructs an actionable learning item for an unfulfilled skill gap."""
        canonical = canonicalize_skill(skill)
        default_focus = f"Core fundamentals, syntax, and hands-on projects for {skill}."
        focus = self.SKILL_TOPIC_FOCUS.get(canonical, default_focus)
        study_hours = 15 if category == "Critical Required" else 10

        return RoadmapItem(
            skill=skill,
            category=category,
            priority=priority,
            estimated_study_hours=study_hours,
            recommended_focus=focus,
        )

    def analyze_skill_gap(
        self,
        job_requirements: JobRequirementsSchema,
        user_skills: List[str],
    ) -> SkillGapAnalysisResponse:
        """Computes deterministic score, categorized buckets, and roadmap."""
        matched_req, missing_req = self.find_matching_skills(
            job_requirements.required_technical_skills, user_skills
        )
        matched_pref, missing_pref = self.find_matching_skills(
            job_requirements.preferred_technical_skills, user_skills
        )

        total_req = len(job_requirements.required_technical_skills)
        total_pref = len(job_requirements.preferred_technical_skills)
        cnt_matched_req = len(matched_req)
        cnt_matched_pref = len(matched_pref)

        # Handle weight allocation & zero-division edge cases
        if total_req > 0 and total_pref > 0:
            req_weight = 70.0
            pref_weight = 30.0
            req_ratio = cnt_matched_req / total_req
            pref_ratio = cnt_matched_pref / total_pref
            raw_score = (req_ratio * req_weight) + (pref_ratio * pref_weight)
            norm_score = min(100.0, max(0.0, raw_score))
            formula_str = (
                f"({req_ratio:.2f} * {req_weight}) + "
                f"({pref_ratio:.2f} * {pref_weight}) = "
                f"{raw_score:.1f} -> normalized to {norm_score:.1f}"
            )
        elif total_req > 0 and total_pref == 0:
            req_weight = 100.0
            pref_weight = 0.0
            req_ratio = cnt_matched_req / total_req
            pref_ratio = 0.0
            raw_score = req_ratio * 100.0
            formula_str = (
                f"({req_ratio:.2f} * 100.0) = {raw_score:.1f} "
                "(100% weight on required skills)"
            )
        elif total_req == 0 and total_pref > 0:
            req_weight = 0.0
            pref_weight = 100.0
            req_ratio = 0.0
            pref_ratio = cnt_matched_pref / total_pref
            raw_score = pref_ratio * 100.0
            formula_str = (
                f"({pref_ratio:.2f} * 100.0) = {raw_score:.1f} "
                "(100% weight on preferred skills)"
            )
        else:
            req_weight = 70.0
            pref_weight = 30.0
            req_ratio = 0.0
            pref_ratio = 0.0
            raw_score = 0.0
            formula_str = "No technical skills listed in job requirements."

        final_score = round(min(100.0, max(0.0, raw_score)), 1)

        breakdown = ScoreBreakdown(
            required_skills_weight=req_weight,
            required_skills_match_ratio=round(req_ratio, 2),
            preferred_skills_weight=pref_weight,
            preferred_skills_match_ratio=round(pref_ratio, 2),
            formula=formula_str,
        )

        # Build prioritized roadmap: Critical Required first, then High-Value Preferred
        roadmap: List[RoadmapItem] = []
        priority_idx = 1

        for missing in missing_req:
            roadmap.append(
                self._create_roadmap_item(missing, "Critical Required", priority_idx)
            )
            priority_idx += 1

        for missing in missing_pref:
            roadmap.append(
                self._create_roadmap_item(missing, "High-Value Preferred", priority_idx)
            )
            priority_idx += 1

        return SkillGapAnalysisResponse(
            match_score_percentage=final_score,
            score_breakdown=breakdown,
            matched_required_skills=matched_req,
            missing_required_skills=missing_req,
            matched_preferred_skills=matched_pref,
            missing_preferred_skills=missing_pref,
            priority_learning_roadmap=roadmap,
        )


# Global singleton instance
matching_service = SkillMatchingService()
