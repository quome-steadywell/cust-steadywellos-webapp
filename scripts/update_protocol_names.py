#!/usr/bin/env python3
"""
Update protocol names to use normalized titles.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src import create_app, db
from src.models.protocol import Protocol
from src.models.patient import ProtocolType
from src.utils.logger import get_logger

logger = get_logger()


def update_protocol_names():
    """Update protocol names to normalized titles."""
    logger.info("🔧 Updating protocol names to normalized titles...")
    
    # Import standardized protocol names
    from src.utils.protocol_names import get_standard_protocol_names
    protocol_names = get_standard_protocol_names()
    
    updated_count = 0
    
    for protocol_type, new_name in protocol_names.items():
        try:
            protocol = Protocol.query.filter_by(protocol_type=protocol_type).first()
            
            if not protocol:
                logger.warning(f"No protocol found for type {protocol_type}")
                continue
            
            old_name = protocol.name
            logger.info(f"Updating {protocol_type.value} protocol name...")
            logger.info(f"  From: {old_name}")
            logger.info(f"  To: {new_name}")
            
            # Update the name directly
            from sqlalchemy import text
            db.session.execute(
                text("""UPDATE protocols 
                        SET name = :name,
                            updated_at = NOW()
                        WHERE id = :protocol_id"""),
                {
                    'name': new_name,
                    'protocol_id': protocol.id
                }
            )
            
            logger.info(f"✅ Updated {protocol_type.value} protocol name")
            updated_count += 1
            
        except Exception as e:
            logger.error(f"Error updating {protocol_type}: {e}")
    
    if updated_count > 0:
        db.session.commit()
        logger.info(f"🎉 Successfully updated {updated_count} protocol names!")
        return True
    else:
        logger.error("❌ No protocol names were updated")
        return False


def main():
    """Main function."""
    logger.info("Protocol Name Update Script Starting...")
    
    app = create_app()
    
    with app.app_context():
        success = update_protocol_names()
        
        if success:
            logger.info("🚀 All protocol names have been normalized!")
            logger.info("Visit http://localhost:8081/protocols to see the updated names")
        else:
            logger.error("❌ Protocol name update failed")
            sys.exit(1)


if __name__ == "__main__":
    main()