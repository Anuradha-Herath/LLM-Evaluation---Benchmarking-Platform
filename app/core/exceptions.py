class LLMPlatformError(Exception):
    """Base exception for all errors in the LLM Evaluation Platform."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class LLMProviderError(LLMPlatformError):
    """Base exception for errors originating from LLM providers."""

    def __init__(self, message: str, provider_name: str = "unknown", model_name: str = "unknown"):
        super().__init__(message)
        self.provider_name = provider_name
        self.model_name = model_name


class LLMProviderTimeoutError(LLMProviderError):
    """Raised when an LLM provider request times out."""

    pass


class LLMProviderUnavailableError(LLMProviderError):
    """Raised when an LLM provider endpoint or server is unreachable or offline."""

    pass


class LLMProviderRateLimitError(LLMProviderError):
    """Raised when an LLM provider returns a 429 rate limit error."""

    pass


class LLMProviderAPIError(LLMProviderError):
    """Raised when an LLM provider API returns an HTTP error status code."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        provider_name: str = "unknown",
        model_name: str = "unknown",
    ):
        super().__init__(message, provider_name=provider_name, model_name=model_name)
        self.status_code = status_code


class LLMProviderInvalidResponseError(LLMProviderError):
    """Raised when an LLM provider returns an unparseable or unexpected payload structure."""

    pass


# Dataset Exceptions
class DatasetError(LLMPlatformError):
    """Base exception for dataset loading and validation errors."""

    pass


class DatasetFileNotFoundError(DatasetError):
    """Raised when a dataset file does not exist at the specified path."""

    pass


class DatasetValidationError(DatasetError):
    """Raised when a dataset record fails Pydantic schema validation."""

    pass


class DuplicateDatasetIDError(DatasetError):
    """Raised when a dataset contains non-unique record IDs."""

    def __init__(self, duplicate_id: str, message: str = ""):
        msg = message or f"Duplicate dataset record ID found: '{duplicate_id}'"
        super().__init__(msg)
        self.duplicate_id = duplicate_id

