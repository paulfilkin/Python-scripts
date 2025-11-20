"""
Text parser for aligned multilingual content.
Parses text files with blank-line-separated language groups.
"""

from typing import List


class TextParser:
    """Parse aligned multilingual text files"""
    
    def parse_text(self, content: str) -> List[List[str]]:
        """
        Parse text content into aligned groups.
        
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
    
    def validate_alignment(self, groups: List[List[str]]) -> tuple[bool, str]:
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
