# NZ Medical Document Assistant API Documentation

## Overview

This API provides endpoints for managing medical documents, generating content using LLMs with Retrieval-Augmented Generation (RAG), and validating generated content for New Zealand healthcare professionals.

Base URL: `/api/v1`

## Authentication

Currently, the API uses simple user ID passing through parameters. A proper authentication system should be implemented for production use.

## Response Format

All API responses follow a consistent JSON format:

```json
{
  "success": true|false,
  "data|error": {...}|"error message"
}
```

- `success`: Boolean indicating if the request was successful
- `data` or specific data field: Present when `success` is true
- `error`: Error message when `success` is false

## Endpoints

### Health Check

**GET /** - Check if the API is running

**Response:**
```json
{
  "success": true,
  "message": "NZ Medical Document Assistant API is running",
  "version": "1.0",
  "documentation": "/api/v1/docs"
}
```

### Documents

#### Upload Document

**POST /api/v1/documents**

Uploads and processes a document.

**Request:**
- Content-Type: `multipart/form-data`
- Body:
  - `file`: The document file (PDF or DOCX)
  - `title`: Document title
  - `doc_type`: Document type (see available document types)
  - `user_id`: User ID (optional, defaults to 1)

**Example Request:**
```
POST /api/v1/documents
Content-Type: multipart/form-data

file=@clinical_guidelines.pdf
title=Clinical Guidelines for Diabetes
doc_type=Best Practice
user_id=1
```

**Response (201 Created):**
```json
{
  "success": true,
  "document": {
    "id": 1,
    "title": "Clinical Guidelines for Diabetes",
    "doc_type": "Best Practice",
    "file_extension": "pdf",
    "original_filename": "clinical_guidelines.pdf",
    "uploaded_at": "2025-05-03T08:30:00.000Z"
  }
}
```

**Error Responses:**
- 400 Bad Request: Missing required fields or invalid file type
- 500 Internal Server Error: Error processing document

#### List Documents

**GET /api/v1/documents**

Retrieves all documents for a user.

**Parameters:**
- `user_id`: User ID (optional, defaults to 1)
- `doc_type`: Filter by document type (optional)

**Example Request:**
```
GET /api/v1/documents?user_id=1&doc_type=Policy
```

**Response:**
```json
{
  "success": true,
  "documents": [
    {
      "id": 1,
      "title": "Clinical Guidelines for Diabetes",
      "doc_type": "Best Practice",
      "file_extension": "pdf",
      "original_filename": "clinical_guidelines.pdf",
      "uploaded_at": "2025-05-03T08:30:00.000Z"
    },
    {
      "id": 2,
      "title": "Patient Privacy Policy",
      "doc_type": "Policy",
      "file_extension": "docx",
      "original_filename": "privacy_policy.docx",
      "uploaded_at": "2025-05-03T09:15:00.000Z"
    }
  ]
}
```

#### Get Document Details

**GET /api/v1/documents/:document_id**

Retrieves details of a specific document including a preview of its chunks.

**Example Request:**
```
GET /api/v1/documents/1
```

**Response:**
```json
{
  "success": true,
  "document": {
    "id": 1,
    "title": "Clinical Guidelines for Diabetes",
    "doc_type": "Best Practice",
    "file_extension": "pdf",
    "original_filename": "clinical_guidelines.pdf",
    "uploaded_at": "2025-05-03T08:30:00.000Z",
    "chunks": [
      {
        "id": 1,
        "chunk_index": 0,
        "text_content": "Introduction to Diabetes Management in Primary Care..."
      },
      {
        "id": 2,
        "chunk_index": 1,
        "text_content": "Diagnostic Criteria for Type 2 Diabetes..."
      }
    ]
  }
}
```

**Error Responses:**
- 404 Not Found: Document not found

### Content Generation

#### Generate Content

**POST /api/v1/generate**

Generates content using LLM with optional RAG.

**Request:**
- Content-Type: `application/json`
- Body:
  - `topic`: The main topic for content generation (required)
  - `content_type`: Type of content (Policy, Best Practice, etc.) (required)
  - `model_choice`: LLM model to use (optional, defaults to system default)
  - `use_rag`: Whether to use RAG (optional, defaults to true)
  - `user_id`: User ID (optional, defaults to 1)

**Example Request:**
```json
POST /api/v1/generate
Content-Type: application/json

{
  "topic": "Diabetes Management in Primary Care",
  "content_type": "Best Practice",
  "model_choice": "mistral",
  "use_rag": true,
  "user_id": 1
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "content": {
    "id": 1,
    "title": "Best Practice: Diabetes Management in Primary Care",
    "content_type": "Best Practice",
    "content": "# Diabetes Management in Primary Care\n\n## Introduction\n\nDiabetes is a chronic condition that affects...",
    "llm_model_used": "mistralai/Mistral-7B-Instruct-v0.2",
    "created_at": "2025-05-03T10:20:00.000Z",
    "validation_score": 0.85,
    "validation_feedback": {
      "consistency": "The document is internally consistent with no contradictions.",
      "clinical_relevance": "The content is clinically relevant and accurate for NZ healthcare settings.",
      "language_tone": "The language is formal and appropriate for medical professionals.",
      "recommendations": [
        "Add a reference to the latest NZ Diabetes Guidelines"
      ]
    },
    "rag_used": true,
    "source_documents": [
      {
        "id": 1,
        "title": "Clinical Guidelines for Diabetes",
        "relevance_score": 0.92
      }
    ]
  }
}
```

**Error Responses:**
- 400 Bad Request: Missing required fields
- 500 Internal Server Error: Error generating content

#### List Generated Contents

**GET /api/v1/contents**

Retrieves all generated contents for a user with optional filtering.

**Parameters:**
- `user_id`: User ID (optional, defaults to 1)
- `content_type`: Filter by content type (optional)
- `llm_model`: Filter by LLM model used (optional)
- `min_validation`: Filter by minimum validation score (optional)

**Example Request:**
```
GET /api/v1/contents?user_id=1&content_type=Best Practice&min_validation=0.8
```

**Response:**
```json
{
  "success": true,
  "contents": [
    {
      "id": 1,
      "title": "Best Practice: Diabetes Management in Primary Care",
      "content_type": "Best Practice",
      "created_at": "2025-05-03T10:20:00.000Z",
      "llm_model_used": "mistralai/Mistral-7B-Instruct-v0.2",
      "validation_score": 0.85,
      "rag_used": true
    },
    {
      "id": 2,
      "title": "Best Practice: Hypertension Management",
      "content_type": "Best Practice",
      "created_at": "2025-05-03T11:05:00.000Z",
      "llm_model_used": "mistralai/Mistral-7B-Instruct-v0.2",
      "validation_score": 0.91,
      "rag_used": false
    }
  ]
}
```

#### Get Content Details

**GET /api/v1/contents/:content_id**

Retrieves details of a specific generated content.

**Example Request:**
```
GET /api/v1/contents/1
```

**Response:**
```json
{
  "success": true,
  "content": {
    "id": 1,
    "title": "Best Practice: Diabetes Management in Primary Care",
    "content_type": "Best Practice",
    "content": "# Diabetes Management in Primary Care\n\n## Introduction\n\nDiabetes is a chronic condition that affects...",
    "llm_model_used": "mistralai/Mistral-7B-Instruct-v0.2",
    "created_at": "2025-05-03T10:20:00.000Z",
    "validation_score": 0.85,
    "validation_feedback": {
      "consistency": "The document is internally consistent with no contradictions.",
      "clinical_relevance": "The content is clinically relevant and accurate for NZ healthcare settings.",
      "language_tone": "The language is formal and appropriate for medical professionals.",
      "recommendations": [
        "Add a reference to the latest NZ Diabetes Guidelines"
      ]
    },
    "rag_used": true,
    "source_documents": [
      {
        "id": 1,
        "title": "Clinical Guidelines for Diabetes",
        "relevance_score": 0.92
      }
    ],
    "validation_results": [
      {
        "id": 1,
        "validator_model": "mistralai/Mistral-7B-Instruct-v0.2",
        "consistency_score": 0.88,
        "clinical_relevance_score": 0.92,
        "language_tone_score": 0.85,
        "nz_compliance_score": 0.78,
        "validation_details": {
          "consistency": "The document is internally consistent with no contradictions.",
          "clinical_relevance": "The content is clinically relevant and accurate for NZ healthcare settings.",
          "language_tone": "The language is formal and appropriate for medical professionals.",
          "nz_compliance": "Generally complies with NZ guidelines but could use more specific references."
        },
        "created_at": "2025-05-03T10:21:00.000Z"
      }
    ]
  }
}
```

**Error Responses:**
- 404 Not Found: Content not found

### Search and RAG

#### Search Documents

**POST /api/v1/search**

Searches documents using the RAG engine.

**Request:**
- Content-Type: `application/json`
- Body:
  - `query`: Search query (required)
  - `doc_type`: Filter by document type (optional)

**Example Request:**
```json
POST /api/v1/search
Content-Type: application/json

{
  "query": "diabetes screening recommendations",
  "doc_type": "Best Practice"
}
```

**Response:**
```json
{
  "success": true,
  "has_context": true,
  "document_count": 2,
  "context": "Document Chunk 1:\nScreening for Type 2 Diabetes should be considered in all adults over 45 years of age. If initial screening is normal, rescreening every 3 years is recommended...\n\nDocument Chunk 2:\nHigh-risk individuals including those with BMI >30, family history of diabetes, or history of gestational diabetes should be screened earlier, starting at age 30...",
  "documents": [
    {
      "id": 1,
      "title": "Clinical Guidelines for Diabetes",
      "doc_type": "Best Practice"
    },
    {
      "id": 3,
      "title": "Diabetes Screening Protocol",
      "doc_type": "Policy"
    }
  ]
}
```

**Error Responses:**
- 400 Bad Request: Missing required fields

### Metadata

#### Get Available Models

**GET /api/v1/models**

Returns a list of available LLM models.

**Example Request:**
```
GET /api/v1/models
```

**Response:**
```json
{
  "success": true,
  "models": {
    "llama": "meta-llama/Llama-2-7b-chat-hf",
    "mistral": "mistralai/Mistral-7B-Instruct-v0.2",
    "falcon": "tiiuae/falcon-7b-instruct"
  }
}
```

#### Get Document Types

**GET /api/v1/document-types**

Returns a list of available document types.

**Example Request:**
```
GET /api/v1/document-types
```

**Response:**
```json
{
  "success": true,
  "document_types": [
    "Policy",
    "Best Practice",
    "Procedure",
    "Standing Order"
  ]
}
```

## Error Codes

- 400: Bad Request - Invalid input or missing required fields
- 404: Not Found - Resource not found
- 500: Internal Server Error - Server-side error

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `HUGGINGFACE_API_KEY`: API key for Hugging Face Inference API (optional)