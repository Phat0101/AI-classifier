"""
Checklist validator using PydanticAI and Gemini 2.5 Pro for validating customs audit checklists.

This module handles:
- Running header-level validations (with PDF documents)
- Running valuation validations (with PDF documents)
- Direct document analysis by LLM instead of using extracted data
"""
from __future__ import annotations

import os
import asyncio
from pathlib import Path
from typing import Dict, Any, List
from pydantic_ai import Agent, BinaryContent
from pydantic_ai.models.gemini import GeminiModel, ThinkingConfig
from pydantic_ai.providers.google_gla import GoogleGLAProvider

from pydantic import BaseModel

from .checklist_models import (
    Region,
    ChecklistItemConfig,
    ChecklistValidationOutput,
    get_header_checks,
    get_valuation_checks,
)


class BatchValidationOutput(BaseModel):
    """Output model for batch validation of multiple checks in one LLM call."""
    validations: List[ChecklistValidationOutput]


# System prompt for batch checklist validation
_SYSTEM_PROMPT = """
You are an expert customs compliance auditor specializing in DHL Express shipments for Australia and New Zealand.

Your task is to validate MULTIPLE checklist items in a single pass by directly analyzing the provided PDF documents (entry prints, commercial invoices, and air waybills).

**Your Responsibilities**:
1. Read ALL the checklist items provided in the prompt
2. Analyze the PDF documents to locate and extract all relevant fields for ALL checks
3. For EACH checklist item:
   - Compare the values between source and target documents according to its checking logic
   - Determine if the check passes, fails, or is questionable
   - Provide detailed reasoning with specific values found in the documents
4. Return validation results for ALL checklist items

**Validation Rules**:
- **PASS**: Clear match or acceptable variation according to pass conditions
- **FAIL**: Clear mismatch or violation of pass conditions
- **QUESTIONABLE**: Ambiguous situation requiring human review

**Special Considerations**:
- If both source and target values are not found/missing in the documents, default to PASS
- For company names: Allow fuzzy matching (abbreviations, minor spelling differences, corporate codes)
- For numeric values: Allow reasonable rounding differences (e.g., 100.00 vs 100)
- For currencies and codes: Allow abbreviations (e.g., "USD" vs "US Dollar", "DDP" vs "Delivered Duty Paid")
- For incoterms: Consider that DDP requires special handling for importer identity
- For dates: Allow different formats (e.g., "2025-01-15" vs "15/01/2025")

**Critical**:
- You MUST return a validation result for EVERY checklist item provided
- Always extract and show the specific values you found in each document
- Reference the exact locations where you found the values (e.g., "Found in Entry Print header section")
- Cite the actual checking logic and pass conditions in your reasoning
- Be conservative: When in doubt between PASS and QUESTIONABLE, choose QUESTIONABLE
- Be thorough: Analyze all relevant sections of the documents

Return your validations as a JSON array with one entry per checklist item in the exact format specified.
"""


# Cache agent instance
_validator_agent: Agent | None = None


def _get_validator_agent() -> Agent:
    """Instantiate (or return cached) Gemini 2.5 Pro agent for checklist validation."""
    global _validator_agent
    
    if _validator_agent is not None:
        return _validator_agent
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY environment variable is required for Gemini agent")

    model = GeminiModel(
        "gemini-2.5-pro",
        provider=GoogleGLAProvider(api_key=api_key),
    )

    _validator_agent = Agent(
        model=model,
        instructions=_SYSTEM_PROMPT,
        output_type=BatchValidationOutput,  # Returns multiple validations at once
        retries=2,  # Retry up to 2 times on failure
        model_settings={"gemini_thinking_config": ThinkingConfig(thinking_budget=5000), "temperature": 0.05}, # Low temperature for consistent validation and thinking budget
    )
    
    return _validator_agent


def build_batch_validation_prompt(checks: List[ChecklistItemConfig]) -> str:
    """
    Build a validation prompt for multiple checklist items to be validated in ONE LLM call.
    
    Args:
        checks: List of checklist item configurations to validate together
        
    Returns:
        Formatted prompt string for the LLM
    """
    prompt = f"""
You are analyzing PDF documents to validate {len(checks)} checklist items in a SINGLE pass.

**Documents Provided Below**:
The following labeled PDF documents will be attached after this prompt:
- **ENTRY PRINT DOCUMENT**: The customs entry print/declaration
- **COMMERCIAL INVOICE DOCUMENT**: The commercial invoice
- **AIR WAYBILL DOCUMENT**: The air waybill (if referenced in checks)

Each document will be clearly labeled before its content so you can easily identify which is which.

---

**CHECKLIST ITEMS TO VALIDATE** ({len(checks)} total):

"""
    
    for idx, check in enumerate(checks, 1):
        # Get source and target field information
        source_fields = check.compare_fields.source_field
        if isinstance(source_fields, str):
            source_fields = [source_fields]
        
        target_fields = check.compare_fields.target_field
        if isinstance(target_fields, str):
            target_fields = [target_fields]
        
        prompt += f"""
### [{idx}/{len(checks)}] Check ID: {check.id}
**Auditing Criteria**: {check.auditing_criteria}

**Description**: {check.description}

**Checking Logic**: {check.checking_logic}

**Pass Conditions**: {check.pass_conditions}

**Compare**:
- Source: {check.compare_fields.source_doc} → {', '.join(source_fields)}
- Target: {check.compare_fields.target_doc} → {', '.join(target_fields)}

---
"""
    
    prompt += f"""

**Your Task**:
1. Review the labeled PDF documents provided below (ENTRY PRINT DOCUMENT, COMMERCIAL INVOICE DOCUMENT, AIR WAYBILL DOCUMENT)
2. For EACH of the {len(checks)} checklist items above:
   - Locate and extract the specified fields from the source and target documents
   - The document labels will help you identify which PDF corresponds to each document type
   - Compare the values according to the checking logic
   - Determine PASS/FAIL/QUESTIONABLE based on pass conditions
   - Document what you found with specific values and locations in the labeled documents

**Important**:
- Return a validation result for ALL {len(checks)} checklist items
- Show exact values found in each labeled document
- Reference the document labels (e.g., "Found in ENTRY PRINT DOCUMENT") and specific sections
- If a value is not found, note it as "NOT FOUND"
- Follow each item's pass conditions strictly

Return a JSON object with a "validations" array containing {len(checks)} ChecklistValidationOutput objects (one for each checklist item above).
"""
    
    return prompt


async def validate_batch_checks(
    checks: List[ChecklistItemConfig],
    documents: Dict[str, bytes],
    category: str = "checks"
) -> List[ChecklistValidationOutput]:
    """
    Validate MULTIPLE checklist items in ONE LLM call by analyzing PDF documents directly.
    
    Args:
        checks: List of checklist item configurations to validate together
        documents: Dictionary of document types to PDF binary content
                  Format: {"entry_print": bytes, "commercial_invoice": bytes, "air_waybill": bytes}
        category: Category name for logging (e.g., "header", "valuation")
        
    Returns:
        List of ChecklistValidationOutput (one for each check)
        
    Raises:
        Exception: If validation fails after retries
    """
    agent = _get_validator_agent()
    
    print(f"   Validating {len(checks)} {category} checks in ONE LLM call with PDFs...", flush=True)
    
    # Check if we have the required documents
    required_docs = set()
    for check in checks:
        required_docs.add(check.compare_fields.source_doc)
        required_docs.add(check.compare_fields.target_doc)
    
    missing_docs = [doc for doc in required_docs if doc not in documents or not documents[doc]]
    if missing_docs:
        print(f"❌ Missing required documents: {missing_docs}", flush=True)
        # Return FAIL for all checks
        return [
            ChecklistValidationOutput(
                check_id=check.id,
                auditing_criteria=check.auditing_criteria,
                status="FAIL",
                assessment=f"Required documents not available: {missing_docs}",
                source_document=check.compare_fields.source_doc,
                target_document=check.compare_fields.target_doc,
                source_value="DOCUMENT NOT FOUND",
                target_value="DOCUMENT NOT FOUND"
            )
            for check in checks
        ]
    
    # Build message parts list with text prompt and PDF documents
    message_parts = []
    
    # Add text prompt with ALL checks
    prompt = build_batch_validation_prompt(checks)
    message_parts.append(prompt)
    
    # Add ALL PDF documents with clear labels
    doc_labels = {
        "entry_print": "ENTRY PRINT DOCUMENT",
        "commercial_invoice": "COMMERCIAL INVOICE DOCUMENT",
        "air_waybill": "AIR WAYBILL DOCUMENT"
    }
    
    for doc_type in ["entry_print", "commercial_invoice", "air_waybill"]:
        if doc_type in documents and documents[doc_type]:
            # Add label before the PDF
            message_parts.append(f"\n**{doc_labels[doc_type]}**:\n")
            
            # Add the PDF binary content
            message_parts.append(BinaryContent(
                data=documents[doc_type],
                media_type="application/pdf"
            ))
            print(f"     Added {doc_type} PDF ({len(documents[doc_type]):,} bytes)", flush=True)
    
    # Run batch validation with PDFs - ONE LLM CALL for all checks
    try:
        print(f"   🔄 Calling Gemini with {len(checks)} checks and {len([m for m in message_parts if isinstance(m, BinaryContent)])} PDFs...", flush=True)
        result = await agent.run(message_parts)
        batch_output: BatchValidationOutput = result.output
        
        if len(batch_output.validations) != len(checks):
            print(f"⚠️  Expected {len(checks)} validations, got {len(batch_output.validations)}", flush=True)
        
        print(f"   ✅ Received {len(batch_output.validations)} validation results", flush=True)
        return batch_output.validations
        
    except Exception as e:
        print(f"❌ Failed to validate batch of {len(checks)} checks: {e}", flush=True)
        # Return FAIL for all checks
        return [
            ChecklistValidationOutput(
                check_id=check.id,
                auditing_criteria=check.auditing_criteria,
                status="FAIL",
                assessment=f"Batch validation error: {str(e)}",
                source_document=check.compare_fields.source_doc,
                target_document=check.compare_fields.target_doc,
                source_value="ERROR",
                target_value="ERROR"
            )
            for check in checks
        ]


async def validate_header_checks(
    region: Region,
    documents: Dict[str, bytes]
) -> List[ChecklistValidationOutput]:
    """
    Validate all header-level checks for a region using PDF documents.
    
    This makes ONE LLM call for ALL header checks together.
    
    Args:
        region: Region code (AU or NZ)
        documents: Dictionary of document types to PDF binary content
                  Format: {"entry_print": bytes, "commercial_invoice": bytes, "air_waybill": bytes}
        
    Returns:
        List of validation results for header checks
    """
    header_checks = get_header_checks(region)
    
    print(f"=" * 80, flush=True)
    print(f"🔍 HEADER VALIDATION - {region} Region", flush=True)
    print(f"=" * 80, flush=True)
    print(f"Running {len(header_checks)} header-level checks in ONE LLM call with PDF documents", flush=True)
    
    # ONE LLM call for all header checks
    results = await validate_batch_checks(header_checks, documents, category="header")
    
    # Log results
    for result in results:
        print(f"   ✓ {result.check_id}: {result.status}", flush=True)
    
    print(f"\n✅ Header checks complete: {len(results)} checks processed in ONE LLM call", flush=True)
    return results


async def validate_valuation_checks(
    region: Region,
    documents: Dict[str, bytes]
) -> List[ChecklistValidationOutput]:
    """
    Validate all valuation checks for a region using PDF documents.
    
    This makes ONE LLM call for ALL valuation checks together.
    
    Args:
        region: Region code (AU or NZ)
        documents: Dictionary of document types to PDF binary content
                  Format: {"entry_print": bytes, "commercial_invoice": bytes, "air_waybill": bytes}
        
    Returns:
        List of validation results for valuation checks
    """
    valuation_checks = get_valuation_checks(region)
    
    print(f"\n" + "=" * 80, flush=True)
    print(f"💰 VALUATION VALIDATION - {region} Region", flush=True)
    print(f"=" * 80, flush=True)
    print(f"Running {len(valuation_checks)} valuation checks in ONE LLM call with PDF documents", flush=True)
    
    # ONE LLM call for all valuation checks
    results = await validate_batch_checks(valuation_checks, documents, category="valuation")
    
    # Log results
    for result in results:
        print(f"   ✓ {result.check_id}: {result.status}", flush=True)
    
    print(f"\n✅ Valuation checks complete: {len(results)} checks processed in ONE LLM call", flush=True)
    return results


async def validate_all_checks(
    region: Region,
    documents: Dict[str, bytes]
) -> Dict[str, Any]:
    """
    Validate all checks (header + valuation) for a region using PDF documents.
    
    This function makes EXACTLY TWO LLM calls IN PARALLEL:
    1. ONE call for ALL header checks (13 checks)
    2. ONE call for ALL valuation checks (7 checks)
    
    Both calls run simultaneously using asyncio.gather() for maximum performance.
    
    Args:
        region: Region code (AU or NZ)
        documents: Dictionary of document types to PDF binary content
                  Format: {"entry_print": bytes, "commercial_invoice": bytes, "air_waybill": bytes}
        
    Returns:
        Dictionary with results grouped by category:
        {
            "header": [ChecklistValidationOutput, ...],
            "valuation": [ChecklistValidationOutput, ...],
            "summary": {"total": 20, "passed": 15, "failed": 2, "questionable": 3}
        }
    """
    print(f"\n" + "=" * 80, flush=True)
    print(f"🚀 STARTING COMPLETE VALIDATION FOR {region} REGION", flush=True)
    print(f"=" * 80, flush=True)
    print(f"Documents provided: {list(documents.keys())}", flush=True)
    print(f"This will make EXACTLY TWO LLM calls IN PARALLEL:", flush=True)
    print(f"  1. ONE call for ALL 13 header checks (with PDFs)", flush=True)
    print(f"  2. ONE call for ALL 7 valuation checks (with PDFs)", flush=True)
    print(f"  Total: 2 LLM calls running simultaneously for 20 checklist items", flush=True)
    print(f"", flush=True)
    
    # Run header and valuation checks IN PARALLEL
    print(f"🔄 Starting both validation calls in parallel...", flush=True)
    header_results, valuation_results = await asyncio.gather(
        validate_header_checks(region, documents),
        validate_valuation_checks(region, documents)
    )
    
    # Summary
    total_checks = len(header_results) + len(valuation_results)
    passed = sum(1 for r in (header_results + valuation_results) if r.status == "PASS")
    failed = sum(1 for r in (header_results + valuation_results) if r.status == "FAIL")
    questionable = sum(1 for r in (header_results + valuation_results) if r.status == "QUESTIONABLE")
    
    print(f"\n" + "=" * 80, flush=True)
    print(f"🎉 VALIDATION COMPLETE FOR {region} REGION", flush=True)
    print(f"=" * 80, flush=True)
    print(f"Total checks: {total_checks}", flush=True)
    print(f"  ✅ PASS: {passed}", flush=True)
    print(f"  ❌ FAIL: {failed}", flush=True)
    print(f"  ⚠️  QUESTIONABLE: {questionable}", flush=True)
    print(f"=" * 80, flush=True)
    
    return {
        "header": header_results,
        "valuation": valuation_results,
        "summary": {
            "total": total_checks,
            "passed": passed,
            "failed": failed,
            "questionable": questionable
        }
    }

