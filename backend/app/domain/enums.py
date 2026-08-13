from enum import StrEnum


class AcquisitionMethod(StrEnum):
    OFFICIAL_API = "OFFICIAL_API"
    OFFICIAL_EXPORT = "OFFICIAL_EXPORT"
    PUBLIC_WEB = "PUBLIC_WEB"
    MANUAL_IMPORT = "MANUAL_IMPORT"
    INSTRUMENTED_APP = "INSTRUMENTED_APP"


class EvidenceQuality(StrEnum):
    A = "A"  # official API
    B = "B"  # official feed/export
    C = "C"  # platform-visible/public data
    D = "D"  # third party
    E = "E"  # unverified lead


class AcquisitionRisk(StrEnum):
    R0 = "R0"
    R1 = "R1"
    R2 = "R2"
    R3 = "R3"
    R4 = "R4"


class Capability(StrEnum):
    SEARCH = "SEARCH"
    SEARCH_OBSERVATION = "SEARCH_OBSERVATION"
    TREND = "TREND"
    RELATED_KEYWORD = "RELATED_KEYWORD"
    ITEM_DETAIL = "ITEM_DETAIL"
    PRODUCT = "PRODUCT"
    JOB = "JOB"
    REPOSITORY = "REPOSITORY"
    IMPORT = "IMPORT"
    APP_OBSERVATION = "APP_OBSERVATION"
    DISCOVERY_FEED = "DISCOVERY_FEED"


class QueryMode(StrEnum):
    KEYWORD = "KEYWORD"
    REGION = "REGION"
    PUSH_ONLY = "PUSH_ONLY"
    SCHEDULED = "SCHEDULED"


class ItemType(StrEnum):
    CONTENT = "CONTENT"
    PRODUCT = "PRODUCT"
    JOB = "JOB"
    REPOSITORY = "REPOSITORY"
    TREND = "TREND"
    APP_OBSERVATION = "APP_OBSERVATION"


class KeywordStatus(StrEnum):
    DISCOVERED = "DISCOVERED"
    WATCHING = "WATCHING"
    ACTIVE = "ACTIVE"
    TRENDING = "TRENDING"
    DECLINING = "DECLINING"
    ARCHIVED = "ARCHIVED"


class ProbeTaskStatus(StrEnum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"


class CollectionRunStatus(StrEnum):
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
