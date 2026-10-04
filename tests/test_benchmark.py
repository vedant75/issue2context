from issue2context.benchmark import (
    build_benchmark,
    extract_changed_files,
    transform_row,
    validate_raw_row,
    validate_task,
)


def test_extract_changed_files():
    patch = """
diff --git a/src/config/parser.py b/src/config/parser.py
diff --git a/src/config/models.py b/src/config/models.py
"""

    result = extract_changed_files(patch)

    assert result == [
        "src/config/parser.py",
        "src/config/models.py",
    ]


def test_extract_changed_files_removes_duplicates():
    patch = """
diff --git a/src/config.py b/src/config.py
diff --git a/src/config.py b/src/config.py
"""

    assert extract_changed_files(patch) == ["src/config.py"]


def test_extract_changed_files_empty_patch():
    assert extract_changed_files("") == []


# validate raw row


def test_validate_raw_row_valid():
    raw_row = {
        "instance_id": "django__django-123",
        "repo": "django/django",
        "base_commit": "abc123",
        "problem_statement": "QuerySet crashes when...",
        "patch": "diff --git a/file.py b/file.py",
    }

    result = validate_raw_row(raw_row)

    assert result == (True, None)


def test_validate_raw_row_missing_repo():
    raw_row = {
        "instance_id": "django__django-123",
        "base_commit": "abc123",
        "problem_statement": "QuerySet crashes when...",
        "patch": "diff --git a/file.py b/file.py",
    }

    result = validate_raw_row(raw_row)

    assert result == (False, "missing_repo")


def test_validate_raw_row_empty_patch():
    raw_row = {
        "instance_id": "django__django-123",
        "repo": "django/django",
        "base_commit": "abc123",
        "problem_statement": "QuerySet crashes when...",
        "patch": "",
    }

    result = validate_raw_row(raw_row)

    assert result == (False, "missing_patch")


def test_transform_row():
    raw_row = {
        "instance_id": "django__django-123",
        "repo": "django/django",
        "base_commit": "abc123",
        "problem_statement": "QuerySet crashes when...",
        "patch": """
diff --git a/django/db/models/query.py b/django/db/models/query.py
""",
        "test_patch": """
diff --git a/tests/queries/test_query.py b/tests/queries/test_query.py
""",
        "version": "4.2",
    }

    result = transform_row(raw_row)

    assert result == {
        "task_id": "django__django-123",
        "repo": "django/django",
        "base_commit": "abc123",
        "version": "4.2",
        "issue_text": "QuerySet crashes when...",
        "gold_source_files": [
            "django/db/models/query.py",
        ],
        "gold_test_files": [
            "tests/queries/test_query.py",
        ],
    }


def test_validate_task_valid():
    task = {
        "task_id": "django__django-123",
        "repo": "django/django",
        "base_commit": "abc123",
        "version": "4.2",
        "issue_text": "QuerySet crashes when...",
        "gold_source_files": [
            "django/db/models/query.py",
        ],
        "gold_test_files": [
            "tests/queries/test_query.py",
        ],
    }

    result = validate_task(task)

    assert result == (True, None)


def test_validate_task_missing_issue_text():
    task = {
        "task_id": "django__django-123",
        "repo": "django/django",
        "base_commit": "abc123",
        "version": "4.2",
        "issue_text": "",
        "gold_source_files": [
            "django/db/models/query.py",
        ],
        "gold_test_files": [],
    }

    result = validate_task(task)

    assert result == (False, "missing_issue_text")


def test_validate_task_missing_gold_source_files():
    task = {
        "task_id": "django__django-123",
        "repo": "django/django",
        "base_commit": "abc123",
        "version": "4.2",
        "issue_text": "QuerySet crashes when...",
        "gold_source_files": [],
        "gold_test_files": [],
    }

    result = validate_task(task)

    assert result == (False, "missing_gold_source_files")


def test_build_benchmark():
    raw_rows = [
        {
            "instance_id": "django__django-1",
            "repo": "django/django",
            "base_commit": "abc123",
            "problem_statement": "QuerySet crashes when...",
            "patch": """
diff --git a/django/db/models/query.py b/django/db/models/query.py
""",
            "test_patch": """
diff --git a/tests/queries/test_query.py b/tests/queries/test_query.py
""",
            "version": "4.2",
        },
        {
            "instance_id": "django__django-2",
            "repo": "",
            "base_commit": "def456",
            "problem_statement": "Some other issue...",
            "patch": """
diff --git a/django/db/models/sql/query.py b/django/db/models/sql/query.py
""",
            "test_patch": "",
            "version": "4.2",
        },
        {
            "instance_id": "django__django-3",
            "repo": "django/django",
            "base_commit": "ghi789",
            "problem_statement": "Another issue...",
            "patch": "this is not a valid git diff",
            "test_patch": "",
            "version": "4.2",
        },
    ]

    valid_tasks, rejected_tasks = build_benchmark(raw_rows)

    assert len(valid_tasks) == 1
    assert len(rejected_tasks) == 2

    assert valid_tasks[0] == {
        "task_id": "django__django-1",
        "repo": "django/django",
        "base_commit": "abc123",
        "version": "4.2",
        "issue_text": "QuerySet crashes when...",
        "gold_source_files": [
            "django/db/models/query.py",
        ],
        "gold_test_files": [
            "tests/queries/test_query.py",
        ],
    }

    assert rejected_tasks[0] == {
        "task_id": "django__django-2",
        "index": 1,
        "stage": "raw_validation",
        "reason": "missing_repo",
    }

    assert rejected_tasks[1] == {
        "task_id": "django__django-3",
        "index": 2,
        "stage": "task_validation",
        "reason": "missing_gold_source_files",
    }
