<<<<<<< HEAD
"""Centralised HTTP error helpers for AssetFlow.

Every raised HTTPException should go through one of these helpers so that the
response body is always:

    {"detail": "<human message>", "code": "<ERROR_CODE>"}
"""
from fastapi import HTTPException, status


def _raise(http_status: int, detail: str, code: str) -> None:
    raise HTTPException(
        status_code=http_status,
        detail={"detail": detail, "code": code},
    )


# ── 404 Not Found ────────────────────────────────────────────────────────────

def not_found(detail: str, code: str) -> None:
    _raise(status.HTTP_404_NOT_FOUND, detail, code)


def department_not_found() -> None:
    not_found("Department not found", "DEPARTMENT_NOT_FOUND")


def category_not_found() -> None:
    not_found("Asset category not found", "CATEGORY_NOT_FOUND")


def asset_not_found() -> None:
    not_found("Asset not found", "ASSET_NOT_FOUND")


# ── 409 Conflict ─────────────────────────────────────────────────────────────

def conflict(detail: str, code: str) -> None:
    _raise(status.HTTP_409_CONFLICT, detail, code)


def department_code_conflict() -> None:
    conflict("Department code already exists", "DEPARTMENT_CODE_CONFLICT")


def department_name_conflict() -> None:
    conflict("Department name already exists", "DEPARTMENT_NAME_CONFLICT")


def category_name_conflict() -> None:
    conflict("Asset category name already exists", "CATEGORY_NAME_CONFLICT")


def asset_tag_conflict() -> None:
    conflict("Asset tag already exists", "ASSET_TAG_CONFLICT")


def asset_serial_conflict() -> None:
    conflict("Asset serial number already exists", "ASSET_SERIAL_CONFLICT")


# ── 400 Bad Request ──────────────────────────────────────────────────────────

def bad_request(detail: str, code: str) -> None:
    _raise(status.HTTP_400_BAD_REQUEST, detail, code)


def invalid_parent_department(reason: str = "Invalid parent department") -> None:
    bad_request(reason, "INVALID_PARENT_DEPARTMENT")


def invalid_asset_status(value: str) -> None:
    bad_request(
        f"'{value}' is not a valid asset status",
        "INVALID_ASSET_STATUS",
    )


def invalid_asset_condition(value: str) -> None:
    bad_request(
        f"'{value}' is not a valid asset condition",
        "INVALID_ASSET_CONDITION",
    )
=======
from fastapi import HTTPException, status


def api_error(status_code: int, detail: str, code: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"detail": detail, "code": code})


FORBIDDEN = api_error(status.HTTP_403_FORBIDDEN, "Not enough permissions", "FORBIDDEN_ROLE")
>>>>>>> 835db53a52e82859b982fe75ce7670b80b1489bd
