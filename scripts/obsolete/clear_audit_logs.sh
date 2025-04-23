#!/bin/bash
# Clear audit logs to avoid foreign key conflicts

set -e

# Print colorful messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=======================================${NC}"
echo -e "${YELLOW}  Clearing Audit Logs                 ${NC}"
echo -e "${YELLOW}=======================================${NC}"

# Check if containers are running
if ! docker-compose ps | grep -q "web\\|db"; then
  echo -e "${RED}Containers are not running. Please start them first with 'just up'.${NC}"
  exit 1
fi

# Run the audit log check and clear script
echo -e "${GREEN}Checking audit logs...${NC}"
docker-compose exec -T web python - <<EOF
from app import create_app, db
from app.models.audit_log import AuditLog

app = create_app()
with app.app_context():
    count = db.session.query(AuditLog).count()
    print(f"Found {count} audit log entries")
    if count > 0:
        db.session.query(AuditLog).delete()
        db.session.commit()
        print(f"Deleted {count} audit log entries")
EOF

echo -e "${GREEN}Audit logs cleared!${NC}"