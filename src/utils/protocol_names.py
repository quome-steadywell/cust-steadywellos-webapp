"""
Standardized protocol names utility.
This module provides consistent protocol names across all scripts and services.
"""

from src.models.patient import ProtocolType


def get_standard_protocol_names():
    """
    Get the standardized protocol names mapping.
    
    Returns:
        dict: Mapping of ProtocolType enum values to standardized names
    """
    return {
        ProtocolType.CANCER: 'Cancer Palliative Care Protocol',
        ProtocolType.HEART_FAILURE: 'Heart Failure Palliative Care Protocol',
        ProtocolType.COPD: 'COPD Palliative Care Protocol',
        ProtocolType.FIT: 'FIT Protocol - Wellness Monitoring'
    }


def get_standard_protocol_name(protocol_type):
    """
    Get the standardized name for a specific protocol type.
    
    Args:
        protocol_type: ProtocolType enum value or string representation
        
    Returns:
        str: The standardized protocol name
    """
    names = get_standard_protocol_names()
    
    # Handle string input (like 'CANCER', 'HEART_FAILURE', etc.)
    if isinstance(protocol_type, str):
        try:
            protocol_type = ProtocolType(protocol_type.lower())
        except ValueError:
            # Try finding by enum name
            for enum_val in ProtocolType:
                if enum_val.name == protocol_type:
                    protocol_type = enum_val
                    break
            else:
                return None
    
    return names.get(protocol_type)


def ensure_protocol_name_consistency(protocol):
    """
    Ensure a protocol has the correct standardized name.
    
    Args:
        protocol: Protocol model instance
        
    Returns:
        bool: True if name was updated, False if already correct
    """
    standard_name = get_standard_protocol_name(protocol.protocol_type)
    if standard_name and protocol.name != standard_name:
        protocol.name = standard_name
        return True
    return False