
import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()

app = FastAPI(
    title="AI Legal Assistant API",
    description="Backend API for Indian legal guidance",
    version="0.3.0",
)


api_key = os.getenv("GROQ_API_KEY")

client = (
    OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
    )
    if api_key
    else None
)



class LegalQuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class LegalQuestionResponse(BaseModel):
    message: str
    status: str
    domain: str


@app.get("/health")
def health_check():
    return {"status": "ok"}



@app.post(
    "/api/v1/legal/questions",
    response_model=LegalQuestionResponse,
)
def submit_legal_question(request: LegalQuestionRequest):
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=422,
            detail="Please enter a legal question.",
        )

    if client is None:
        raise HTTPException(
            status_code=503,
            detail="Groq API key is not configured.",
        )

    try:
        # First classify the question into a legal domain.
        classification = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Classify the user's question under Indian law. "
                        "Return exactly one label from this list: "
                        "property_tenancy, criminal_law, family_law, "
                        "consumer_law, employment_law, contract_law, "
                        "constitutional_law, cyber_law, other, unsupported. "
                        "Use unsupported only if the question is clearly "
                        "unrelated to legal matters. Return only the label."
                    ),
                },
                {"role": "user", "content": question},
            ],
            temperature=0,
        )

        domain = (
            classification.choices[0].message.content or ""
        ).strip().lower()

        allowed_domains = {
            "property_tenancy",
            "criminal_law",
            "family_law",
            "consumer_law",
            "employment_law",
            "contract_law",
            "constitutional_law",
            "cyber_law",
            "other",
            "unsupported",
        }

        if domain not in allowed_domains:
            domain = "other"

        if domain == "unsupported":
            return LegalQuestionResponse(
                message=(
                    "I can help with questions related to Indian law. "
                    "Please ask a legal question about an Indian legal issue."
                ),
                status="unsupported",
                domain=domain,
            )

        # Generate an answer after classification.
        prompt = f"""
You are an informational assistant for Indian law.

The question has been classified under: {domain}.

Answer in clear, simple language.
Explain general legal concepts and practical next steps.
Do not invent laws, section numbers, cases, or citations.
If unsure about current law, clearly say so.
Do not claim to be a lawyer or replace qualified legal advice.
Mention that case-specific matters should be checked
with a qualified Indian lawyer.

User's question:
{question}
"""

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You provide general information about Indian law. "
                        "Do not invent legal citations or claim unverified facts."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )

        answer = response.choices[0].message.content

        if not answer:
            raise HTTPException(
                status_code=502,
                detail="Groq returned an empty response.",
            )

        return LegalQuestionResponse(
            message=answer,
            status="answered",
            domain=domain,
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Groq API error: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=502,
            detail="Groq request failed. Check the backend terminal.",
        )
