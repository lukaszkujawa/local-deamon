import re
from pathlib import Path
from functools import lru_cache
from typing import Optional, Set


class Prompt:
    """
    Prompt template loaded from markdown file with {{variable}} substitution.

    Example:
        prompt = Prompt.load("greeting")
        rendered = prompt.render(name="Alice", time="morning")
    """

    _pattern = re.compile(r'\{\{(\w+)\}\}')

    def __init__(self, name: str, template: str):
        self.name = name
        self.template = template

    @property
    def variables(self) -> Set[str]:
        """Extract variable names from template"""
        return set(self._pattern.findall(self.template))

    @classmethod
    @lru_cache(maxsize=32)
    def load(cls, name: str, spellbook_dir: Optional[Path] = None) -> "Prompt":
        """Load prompt from spellbook directory"""
        if spellbook_dir is None:
            spellbook_dir = Path(__file__).resolve().parent.parent / "spellbook"

        path = spellbook_dir / f"{name}.md"
        if not path.exists():
            available = [p.stem for p in spellbook_dir.glob("*.md")] if spellbook_dir.exists() else []
            raise FileNotFoundError(f"Prompt '{name}' not found. Available: {available}")

        return cls(name, path.read_text(encoding="utf-8"))

    def render(self, **kwargs) -> str:
        """
        Render prompt with variable substitution.

        Raises:
            KeyError: If required variables are missing
        """
        missing = self.variables - kwargs.keys()
        if missing:
            raise KeyError(f"Missing variables for '{self.name}': {missing}")

        return self._pattern.sub(lambda m: str(kwargs[m.group(1)]), self.template)

    def safe_render(self, **kwargs) -> str:
        """Render with partial substitution - missing variables remain as {{var}}"""
        return self._pattern.sub(
            lambda m: str(kwargs[m.group(1)]) if m.group(1) in kwargs else m.group(0),
            self.template
        )

    def __repr__(self) -> str:
        return f"Prompt('{self.name}', variables={self.variables})"
