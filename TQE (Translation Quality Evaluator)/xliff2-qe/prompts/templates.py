"""
Prompt templates loaded dynamically from markdown files.
Each .md file in the prompts folder becomes an available template.
"""

import os
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class PromptTemplateManager:
    """Load and manage prompt templates from markdown files."""
    
    def __init__(self, prompts_dir: Optional[str] = None):
        """
        Initialise the template manager.
        
        Args:
            prompts_dir: Path to prompts folder. Defaults to same directory as this file.
        """
        if prompts_dir is None:
            prompts_dir = Path(__file__).parent
        else:
            prompts_dir = Path(prompts_dir)
        
        self.prompts_dir = prompts_dir
        self.templates: Dict[str, str] = {}
        self._load_templates()
    
    def _load_templates(self) -> None:
        """Scan prompts directory and load all .md files."""
        if not self.prompts_dir.exists():
            logger.warning(f"Prompts directory not found: {self.prompts_dir}")
            return
        
        for md_file in self.prompts_dir.glob("*.md"):
            template_name = md_file.stem  # filename without extension
            try:
                content = md_file.read_text(encoding='utf-8')
                self.templates[template_name] = content
                logger.debug(f"Loaded template: {template_name}")
            except Exception as e:
                logger.error(f"Failed to load template {md_file}: {e}")
        
        if self.templates:
            logger.info(f"Loaded {len(self.templates)} prompt templates: {list(self.templates.keys())}")
        else:
            logger.warning("No prompt templates found")
    
    def get_template(self, content_type: str) -> str:
        """
        Get prompt template for content type.
        
        Args:
            content_type: Name of the template (matches filename without .md)
        
        Returns:
            Template string, or general template if not found, or empty string if no templates.
        """
        if content_type in self.templates:
            return self.templates[content_type]
        
        # Fallback to general
        if 'general' in self.templates:
            logger.warning(f"Template '{content_type}' not found, using 'general'")
            return self.templates['general']
        
        # No templates available
        logger.error(f"No template found for '{content_type}' and no fallback available")
        return ""
    
    def list_templates(self) -> list:
        """Return list of available template names."""
        return sorted(self.templates.keys())
    
    def reload(self) -> None:
        """Reload all templates from disk."""
        self.templates.clear()
        self._load_templates()