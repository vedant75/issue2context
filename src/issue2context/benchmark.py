import re

DIFF_FILE_PATTERN = re.compile(
    r"^diff --git a/(.*?) b/(.*?)$",
    re.MULTILINE,
)

REQUIRED_RAW_FIELDS = [
    "instance_id",
    "repo",
    "base_commit",
    "problem_statement",
    "patch",
]

REQUIRED_VALIDATE_TASK_FIELDS = [
    "task_id",
    "repo",
    "base_commit",
    "issue_text",
    "gold_source_files",
]


def extract_changed_files(patch_text: str) -> list[str]:

    if not patch_text:
        return []

    matches = DIFF_FILE_PATTERN.findall(patch_text)

    seen = set()
    files = []

    for _, new_path in matches:
        if new_path not in seen:
            seen.add(new_path)
            files.append(new_path)

    return files


def validate_raw_row(raw_row: dict) -> tuple[bool, str | None]:

    for field in REQUIRED_RAW_FIELDS:
        if not raw_row.get(field):
            return False, f"missing_{field}"

    return True, None


def transform_row(raw_row: dict) -> dict:
    return {
        "task_id": raw_row["instance_id"],
        "repo": raw_row["repo"],
        "base_commit": raw_row["base_commit"],
        "version": raw_row.get("version"),
        "issue_text": raw_row["problem_statement"],
        "gold_source_files": extract_changed_files(raw_row["patch"]),
        "gold_test_files": extract_changed_files(raw_row.get("test_patch", "")),
    }


def validate_task(task) -> tuple[bool, str | None]:

    for field in REQUIRED_VALIDATE_TASK_FIELDS:
        if not task.get(field):
            return False, f"missing_{field}"

    return True, None


def build_benchmark(raw_rows: list[dict]) -> tuple[list[dict], list[dict]]:
    valid_tasks = []
    rejected_tasks = []

    for index, row in enumerate(raw_rows):
        is_valid_raw, raw_reason = validate_raw_row(row)

        if not is_valid_raw:
            rejected_tasks.append(
                {
                    "task_id": row.get("instance_id"),
                    "index": index,
                    "stage": "raw_validation",
                    "reason": raw_reason,
                }
            )
            continue

        transformed_row = transform_row(row)

        is_valid_task, task_reason = validate_task(transformed_row)

        if not is_valid_task:
            rejected_tasks.append(
                {
                    "task_id": transformed_row.get("task_id"),
                    "index": index,
                    "stage": "task_validation",
                    "reason": task_reason,
                }
            )
            continue

        valid_tasks.append(transformed_row)

    return valid_tasks, rejected_tasks
