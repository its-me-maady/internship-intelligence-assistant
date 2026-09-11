import re
from typing import Dict

# Extensible canonical skill mapping dictionary
SKILL_SYNONYMS: Dict[str, str] = {
    # Programming Languages
    "py": "python",
    "py3": "python",
    "python3": "python",
    "golang": "go",
    "go lang": "go",
    "ts": "typescript",
    "js": "javascript",
    "cpp": "c++",
    "c plus plus": "c++",
    "csharp": "c#",
    "c sharp": "c#",
    "rb": "ruby",
    # Frameworks & Libraries
    "reactjs": "react",
    "react.js": "react",
    "react js": "react",
    "nodejs": "nodejs",
    "node.js": "nodejs",
    "node js": "nodejs",
    "node": "nodejs",
    "vuejs": "vue",
    "vue.js": "vue",
    "vue js": "vue",
    "angularjs": "angular",
    "angular.js": "angular",
    "fastapi": "fastapi",
    "fast api": "fastapi",
    "fast-api": "fastapi",
    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "scikitlearn": "scikit-learn",
    "tf": "tensorflow",
    "torch": "pytorch",
    "rest": "restful apis",
    "rest api": "restful apis",
    "restful api": "restful apis",
    "restful apis": "restful apis",
    # Databases & Storage
    "postgres": "postgresql",
    "pgsql": "postgresql",
    "postgres sql": "postgresql",
    "postgres db": "postgresql",
    "mongo": "mongodb",
    "mongo db": "mongodb",
    "sql": "sql",
    "rdbms": "relational databases",
    # Cloud & DevOps
    "k8s": "kubernetes",
    "kube": "kubernetes",
    "aws": "amazon web services",
    "amazon cloud": "amazon web services",
    "gcp": "google cloud platform",
    "google cloud": "google cloud platform",
    "azure": "microsoft azure",
    "ms azure": "microsoft azure",
    "docker container": "docker",
    "docker-compose": "docker",
    "docker compose": "docker",
}


def normalize_skill_name(skill: str) -> str:
    """Normalizes skill names through case-folding and basic cleanup."""
    if not skill:
        return ""
    text = skill.strip().lower()

    # Preserve c++ and c# while standardizing punctuation in other tech names
    if text in {"c++", "cpp", "c plus plus"}:
        return "c++"
    if text in {"c#", "csharp", "c sharp"}:
        return "c#"

    # Replace dots in node.js, react.js, etc.
    text = text.replace(".js", "js")

    # Replace slashes and separators with space (e.g. linux/unix -> linux unix)
    text = text.replace("/", " ").replace(chr(92), " ")

    # Strip non-alphanumeric punctuation except +, #, -
    text = re.sub(r"[^a-z0-9+#\- ]", "", text)

    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


def canonicalize_skill(skill: str) -> str:
    """Converts raw skill string to canonical entity via synonym map."""
    normalized = normalize_skill_name(skill)
    return SKILL_SYNONYMS.get(normalized, normalized)
