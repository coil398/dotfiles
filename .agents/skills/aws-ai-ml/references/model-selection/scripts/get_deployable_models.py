"""
Retrieves all deployable models from a SageMaker Hub and outputs structured metadata as JSON.

Usage:
    python get_deployable_models.py <hub-name> [region]

Arguments:
    hub-name    Name of the SageMaker Hub to query (e.g., SageMakerPublicHub)
    region      Optional AWS region override (defaults to boto3 session default)

Output:
    JSON array of model objects with fields: name, data_types, input_modalities,
    output_modalities, size, license, languages, context_window, model_type,
    framework, provider, tasks, bedrock_eligible.
"""

import json
import os
import sys

import boto3
import botocore.exceptions

os.environ.setdefault("AWS_SDK_UA_APP_ID", "AWSSkill-SageMaker")


# Canonical, non-overlapping size buckets. The hub's raw @model-size values are
# inconsistent — a mix of ranges (e.g. "1b-10b", "10b-70b") and exact parameter
# counts (e.g. "2b", "7b", "30b", "550b"), plus "<1b" and "unknown". Because the
# size filter is an EXACT match, that inconsistency makes deterministic
# soft->hard mapping impossible (e.g. "small" -> "1b-10b" would silently miss a
# model tagged "7b"). We normalize every raw value into one of these buckets so
# the filter and the soft-constraint mapping only ever deal with a clean set.
SIZE_BUCKETS = ("<=10b", "11b-70b", "71b-100b", ">100b", "unknown")


def normalize_size_bucket(raw):
    """Map a raw @model-size value to a canonical, non-overlapping bucket.

    Assignment rule by parameter count N (in billions):
        N <= 10   -> "<=10b"
        10 < N <= 70  -> "11b-70b"
        70 < N <= 100 -> "71b-100b"
        N > 100   -> ">100b"
        unparseable / missing -> "unknown"

    Handles both exact values ("7b", "30b", "550b") and the hub's own range
    labels ("1b-10b", "10b-70b", "70b-100b", ">100b", "<1b"). Range labels are
    classified by their UPPER bound (the largest models the range can contain),
    except ">100b" which is unbounded above and maps to ">100b". This keeps the
    mapping total and deterministic.

    Args:
        raw: The raw size string from the @model-size keyword, or None.

    Returns:
        One of SIZE_BUCKETS.
    """
    if not raw:
        return "unknown"

    value = raw.strip().lower()
    if value == "unknown":
        return "unknown"

    def bucket_for(n):
        if n <= 10:
            return "<=10b"
        if n <= 70:
            return "11b-70b"
        if n <= 100:
            return "71b-100b"
        return ">100b"

    # ">100b" (or any ">Nb") is unbounded above -> largest bucket.
    if value.startswith(">"):
        return ">100b"

    # "<1b" (or any "<Nb") -> use the upper bound N (e.g. <1b has upper bound 1).
    if value.startswith("<"):
        num = _parse_billions(value[1:])
        return bucket_for(num) if num is not None else "unknown"

    # Range label like "1b-10b" / "10b-70b" / "70b-100b": classify by upper bound.
    if "-" in value:
        upper = _parse_billions(value.split("-", 1)[1])
        return bucket_for(upper) if upper is not None else "unknown"

    # Exact value like "7b", "30b", "550b".
    num = _parse_billions(value)
    return bucket_for(num) if num is not None else "unknown"


def _parse_billions(token):
    """Parse a size token like '7b', '550b', '10' into a number of billions.

    Returns a float, or None if it cannot be parsed.
    """
    if not token:
        return None
    t = token.strip().lower().rstrip("b").strip()
    try:
        return float(t)
    except ValueError:
        return None


def get_deployable_models(hub_name, region_name=None):
    """Query a SageMaker Hub and return structured model metadata.

    Args:
        hub_name: Name of the SageMaker Hub.
        region_name: Optional AWS region override.

    Returns:
        List of model dicts with extracted metadata fields.
    """
    sm_client = boto3.client("sagemaker", region_name=region_name)

    # Retrieve all models with pagination
    all_contents = []
    next_token = None

    while True:
        params = {
            "HubName": hub_name,
            "HubContentType": "Model",
            "MaxResults": 100,
        }

        if next_token:
            params["NextToken"] = next_token

        response = sm_client.list_hub_contents(**params)
        all_contents.extend(response.get("HubContentSummaries", []))

        next_token = response.get("NextToken")
        if not next_token:
            break

    # All hub models are deployable to SageMaker endpoints.
    # Extract structured metadata from search keywords for filtering.
    results = []
    for model in all_contents:
        keywords = model.get("HubContentSearchKeywords", [])
        entry = {
            "name": model.get("HubContentName"),
        }

        for kw in keywords:
            if kw.startswith("@data-type:"):
                entry.setdefault("data_types", []).append(kw.split(":", 1)[1])
            elif kw.startswith("@input-modality:"):
                entry.setdefault("input_modalities", []).append(kw.split(":", 1)[1])
            elif kw.startswith("@output-modality:"):
                entry.setdefault("output_modalities", []).append(kw.split(":", 1)[1])
            elif kw.startswith("@model-size:"):
                # Preserve the raw hub value for display, and store the
                # normalized canonical bucket under "size" (what the filter and
                # the soft-constraint mapping use).
                raw_size = kw.split(":", 1)[1]
                entry["size_raw"] = raw_size
                entry["size"] = normalize_size_bucket(raw_size)
            elif kw.startswith("@license:"):
                entry["license"] = kw.split(":", 1)[1]
            elif kw.startswith("@language:"):
                entry.setdefault("languages", []).append(kw.split(":", 1)[1])
            elif kw.startswith("@context-window:"):
                entry["context_window"] = kw.split(":", 1)[1]
            elif kw.startswith("@model-type:"):
                entry["model_type"] = kw.split(":", 1)[1]
            elif kw.startswith("@framework:"):
                # Framework (e.g., "pytorch", "tensorflow") stored separately from provider.
                # The filter script matches against 'provider' field only; framework is
                # preserved for informational purposes.
                entry["framework"] = kw.split(":", 1)[1]
            elif kw.startswith("@provider:"):
                entry["provider"] = kw.split(":", 1)[1]
            elif kw.startswith("@task:"):
                entry.setdefault("tasks", []).append(kw.split(":", 1)[1])

        # Bedrock eligibility
        entry["bedrock_eligible"] = "@capability:bedrock_console" in keywords

        # Original creation time for sorting by recency
        original_creation_time = model.get("OriginalCreationTime")
        if original_creation_time:
            entry["original_creation_time"] = (
                original_creation_time.isoformat()
                if hasattr(original_creation_time, "isoformat")
                else str(original_creation_time)
            )

        results.append(entry)

    return results


def list_available_values(models):
    """Extract all unique values for each metadata field across all models.

    Returns a dict of field_name -> sorted list of unique values.
    """
    values: dict[str, set[str]] = {
        "tasks": set(),
        "data_types": set(),
        "input_modalities": set(),
        "output_modalities": set(),
        "sizes": set(),
        "licenses": set(),
        "languages": set(),
        "context_windows": set(),
        "model_types": set(),
        "providers": set(),
        "frameworks": set(),
    }

    for model in models:
        for task in model.get("tasks", []):
            values["tasks"].add(task)
        for dt in model.get("data_types", []):
            values["data_types"].add(dt)
        for im in model.get("input_modalities", []):
            values["input_modalities"].add(im)
        for om in model.get("output_modalities", []):
            values["output_modalities"].add(om)
        if "size" in model:
            values["sizes"].add(model["size"])
        if "license" in model:
            values["licenses"].add(model["license"])
        for lang in model.get("languages", []):
            values["languages"].add(lang)
        if "context_window" in model:
            values["context_windows"].add(model["context_window"])
        if "model_type" in model:
            values["model_types"].add(model["model_type"])
        if "provider" in model:
            values["providers"].add(model["provider"])
        if "framework" in model:
            values["frameworks"].add(model["framework"])

    return {k: sorted(v) for k, v in values.items()}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python get_deployable_models.py <hub-name> [--list-values] [region]")
        sys.exit(1)

    args = sys.argv[1:]
    list_values_mode = False
    if "--list-values" in args:
        list_values_mode = True
        args.remove("--list-values")

    if not args:
        print("Usage: python get_deployable_models.py <hub-name> [--list-values] [region]")
        sys.exit(1)

    hub_name = args[0]
    region_name = args[1] if len(args) > 1 else None

    try:
        results = get_deployable_models(hub_name, region_name)
    except botocore.exceptions.ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_msg = e.response["Error"]["Message"]
        print(f"Error: AWS API call failed ({error_code}): {error_msg}", file=sys.stderr)
        sys.exit(1)
    except botocore.exceptions.NoCredentialsError:
        print(
            "Error: No AWS credentials found. Configure credentials via 'aws configure' or environment variables.",
            file=sys.stderr,
        )
        sys.exit(1)
    except botocore.exceptions.EndpointConnectionError as e:
        print(f"Error: Could not connect to SageMaker endpoint: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if list_values_mode:
        print(json.dumps(list_available_values(results)))
    else:
        print(json.dumps(results))
