"""
Text parser for aligned multilingual content.
Supports two formats:
1. Blank-line-separated groups (original)
2. Language-prefixed lines (EN:, JA:, PL:, etc.)
"""

from typing import List, Dict, Optional, Tuple
import re


class TextParser:
    """Parse aligned multilingual text files"""
    
    def detect_format(self, content: str) -> str:
        """
        Detect the format of the input file.
        
        Args:
            content: Text file content
            
        Returns:
            'prefixed' or 'grouped'
        """
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        if not lines:
            return 'grouped'
        
        # Check if first few lines have language prefixes
        prefix_pattern = re.compile(r'^[A-Z]{2,3}:\s+')
        prefixed_count = sum(1 for line in lines[:10] if prefix_pattern.match(line))
        
        # If more than 50% of first 10 lines are prefixed, it's prefixed format
        return 'prefixed' if prefixed_count >= 5 else 'grouped'
    
    def extract_language_codes(self, content: str) -> List[str]:
        """
        Extract base language codes from prefixed format.
        
        Args:
            content: Text file content with prefixed lines
            
        Returns:
            List of unique language codes in order of first appearance
        """
        codes = []
        seen = set()
        
        prefix_pattern = re.compile(r'^([A-Z]{2,3}):\s+')
        
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            match = prefix_pattern.match(line)
            if match:
                code = match.group(1)
                if code not in seen:
                    codes.append(code)
                    seen.add(code)
        
        return codes
    
    def parse_text(self, content: str) -> List[List[str]]:
        """
        Parse text content into aligned groups.
        Auto-detects format and uses appropriate parser.
        
        Args:
            content: Text file content
            
        Returns:
            List of groups, where each group is a list of aligned lines
        """
        format_type = self.detect_format(content)
        
        if format_type == 'prefixed':
            return self.parse_prefixed_format(content)
        else:
            return self.parse_grouped_format(content)
    
    def parse_grouped_format(self, content: str) -> List[List[str]]:
        """
        Parse grouped format (original format).
        
        Args:
            content: Text file content
            
        Returns:
            List of groups, where each group is a list of aligned lines
            
        Example:
            Input:
                Line 1 EN
                Line 1 DE
                Line 1 FR
                
                Line 2 EN
                Line 2 DE
                Line 2 FR
                
            Output:
                [
                    ["Line 1 EN", "Line 1 DE", "Line 1 FR"],
                    ["Line 2 EN", "Line 2 DE", "Line 2 FR"]
                ]
        """
        groups = []
        current_group = []
        
        lines = content.split('\n')
        
        for line in lines:
            # Check if blank line (group separator)
            if not line.strip():
                if current_group:
                    groups.append(current_group)
                    current_group = []
            else:
                current_group.append(line.strip())
        
        # Add last group if exists
        if current_group:
            groups.append(current_group)
        
        return groups
    
    def parse_prefixed_format(self, content: str) -> List[List[str]]:
        """
        Parse prefixed format (EN:, JA:, PL:, etc.).
        
        Args:
            content: Text file content with language prefixes
            
        Returns:
            List of groups, where each group is a list of aligned lines (without prefixes)
            
        Example:
            Input:
                EN: Subject line
                JA: 件名行
                PL: Wiersz tematu
                
                EN: Support contacts
                JA: サポート連絡先
                PL: Osoby kontaktowe
                
            Output:
                [
                    ["Subject line", "件名行", "Wiersz tematu"],
                    ["Support contacts", "サポート連絡先", "Osoby kontaktowe"]
                ]
        """
        groups = []
        current_group = []
        
        prefix_pattern = re.compile(r'^[A-Z]{2,3}:\s+(.*)$')
        
        lines = content.split('\n')
        
        for line in lines:
            line_stripped = line.strip()
            
            # Check if blank line (group separator)
            if not line_stripped:
                if current_group:
                    groups.append(current_group)
                    current_group = []
            else:
                # Extract text after prefix
                match = prefix_pattern.match(line_stripped)
                if match:
                    text = match.group(1)
                    current_group.append(text)
        
        # Add last group if exists
        if current_group:
            groups.append(current_group)
        
        return groups
    
    def validate_alignment(self, groups: List[List[str]]) -> Tuple[bool, str]:
        """
        Validate that all groups have the same number of lines.
        
        Args:
            groups: List of text groups
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not groups:
            return False, "No groups found"
        
        expected_count = len(groups[0])
        
        if expected_count == 0:
            return False, "First group is empty"
        
        for idx, group in enumerate(groups):
            if len(group) != expected_count:
                return False, (
                    f"Alignment error in group {idx + 1}: "
                    f"expected {expected_count} lines, found {len(group)}"
                )
        
        return True, ""
    
    def get_statistics(self, groups: List[List[str]]) -> dict:
        """
        Get statistics about the parsed content.
        
        Args:
            groups: List of text groups
            
        Returns:
            Dictionary with statistics
        """
        if not groups:
            return {
                'total_groups': 0,
                'languages_per_group': 0,
                'total_segments': 0
            }
        
        return {
            'total_groups': len(groups),
            'languages_per_group': len(groups[0]),
            'total_segments': len(groups) * len(groups[0]),
            'average_length': sum(len(line) for group in groups for line in group) / (len(groups) * len(groups[0]))
        }
