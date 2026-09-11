from app.main import app
from app.rag.prompts import STANDARD_REFUSAL_MESSAGE
from fastapi.testclient import TestClient

client = TestClient(app)


def test_chat_grounded_query_success():
    # 1. Upload a document
    content = (
        b"Company: Acme AI Labs\n"
        b"Role: Machine Learning Research Intern\n"
        b"Eligibility: Open to MS and PhD students graduating in 2027.\n"
        b"Stipend: $50/hour with relocation assistance."
    )
    files = {"file": ("acme_ml.txt", content, "text/plain")}
    upload_res = client.post("/api/v1/documents/upload", files=files)
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["document_id"]

    # 2. Ask a grounded question
    chat_payload = {
        "document_id": doc_id,
        "query": "What are the eligibility criteria and stipend?",
        "top_k": 4,
    }
    chat_res = client.post("/api/v1/chat", json=chat_payload)
    assert chat_res.status_code == 200
    data = chat_res.json()

    assert "answer" in data
    assert data["is_grounded"] is True
    assert len(data["sources"]) >= 1
    assert data["sources"][0]["document_id"] == doc_id
    assert data["sources"][0]["filename"] == "acme_ml.txt"
    assert "snippet" in data["sources"][0]


def test_chat_unanswerable_query_returns_refusal():
    # Ask a question when no matching document or context exists
    chat_payload = {
        "document_id": "non-existent-doc-id",
        "query": "What is the CEO's favorite food?",
    }
    chat_res = client.post("/api/v1/chat", json=chat_payload)
    assert chat_res.status_code == 200
    data = chat_res.json()

    assert data["is_grounded"] is False
    assert (
        STANDARD_REFUSAL_MESSAGE in data["answer"]
        or "cannot find sufficient information" in data["answer"].lower()
    )
    assert data["sources"] == []


def test_chat_with_conversation_history():
    content = b"Requirements: Proficiency in Python 3.12 and PyTorch."
    files = {"file": ("skills.txt", content, "text/plain")}
    upload_res = client.post("/api/v1/documents/upload", files=files)
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["document_id"]

    chat_payload = {
        "document_id": doc_id,
        "query": "What frameworks are mentioned?",
        "chat_history": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hello! Ask me about this internship."},
        ],
    }
    chat_res = client.post("/api/v1/chat", json=chat_payload)
    assert chat_res.status_code == 200
    assert chat_res.json()["is_grounded"] is True


def test_chat_invalid_payload_returns_422():
    # Empty query should fail validation
    chat_payload = {"query": ""}
    chat_res = client.post("/api/v1/chat", json=chat_payload)
    assert chat_res.status_code == 422
