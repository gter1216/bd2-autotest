from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List

class BaseCLIParser(ABC):
    @abstractmethod
    def parse_args(self) -> Dict[str, Any]:
        """Parse command line arguments"""
        pass

    def validate_choice(self, value: str, choices: List[str], param_name: str) -> bool:
        """Validate that a value is in a list of choices"""
        if value not in choices:
            print(f"Error: Invalid value for {param_name}. Must be one of: {', '.join(choices)}")
            return False
        return True

    def validate_int_range(self, value: int, param_name: str, 
                          min_val: Optional[int] = None, 
                          max_val: Optional[int] = None) -> bool:
        """Validate that an integer is within a range"""
        if min_val is not None and value < min_val:
            print(f"Error: {param_name} must be >= {min_val}")
            return False
        if max_val is not None and value > max_val:
            print(f"Error: {param_name} must be <= {max_val}")
            return False
        return True 