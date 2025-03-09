from enum import Enum
from typing import Optional

from pydantic import BaseModel


class CodeAssistantCompany(str, Enum):
    CODEIUM_ENTERPRISE = "Codeium_Enterprise"
    CURSOR_ENTERPRISE = "Cursor_Enterprise"
    COPILOT_ENTERPRISE = "Copilot_Enterprise"


class BlogPost(BaseModel):
    url: str
    title: str
    date: Optional[str] = None
    content: str
    company: CodeAssistantCompany


# Example usage:
post = BlogPost(
    url="https://example.com",
    title="AI Development",
    content="Some content",
    company=CodeAssistantCompany.CODEIUM_ENTERPRISE,
)

print(post)

print(post)
