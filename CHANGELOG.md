# Changelog

All notable changes to the SteadyWell Palliative Care Platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.0] - 2025-06-29

### Added
- **Database Backup and Import System**
  - Complete admin-only database backup functionality with export/import capabilities
  - Timestamped SQL backup files with PC/Mac compatible naming format (`steadywellos_YYYY-MM-DD_HH-MM-SS.sql`)
  - Secure data-only backups using PostgreSQL's `pg_dump` with `--data-only` and `--column-inserts` flags
  - Web-based backup management interface with role-based access control
  - Database import functionality with 2-minute timeout protection to prevent hanging operations
  - Backup status endpoint providing database size, table count, and tool availability information
  - Admin-only menu integration with automatic visibility control based on user roles
  - Comprehensive error handling and user feedback for backup operations

- **PostgreSQL Client Upgrade**
  - Upgraded Docker image to include PostgreSQL 17 client tools for compatibility with Quome Cloud
  - Added official PostgreSQL repository configuration for latest client versions
  - Enhanced Dockerfile with proper package management and security practices

- **Enhanced Security and Audit Logging**
  - All backup operations are logged through the audit system with user attribution
  - Role-based access control ensures only administrators can access backup functionality
  - Secure file handling with temporary file management and automatic cleanup

### Changed
- **Application Architecture**
  - Added new backup blueprint (`/api/v1/backup`) with three endpoints: export, import, and status
  - Enhanced main application factory to register backup routes and functionality
  - Updated navigation template to include conditional admin-only backup menu item
  - Improved JavaScript for dynamic UI elements based on user permissions

- **Database Operations**
  - Enhanced database configuration handling for both local and production environments
  - Improved error handling for database connectivity and backup tool availability
  - Added database size and metadata collection for backup status reporting

### Technical Improvements
- **Pre-commit Integration**
  - Added Black code formatter as pre-commit hook for consistent code style
  - Updated dependencies to include pre-commit tools in project requirements
  - All code automatically formatted to maintain consistent style standards

- **Development Workflow**
  - Enhanced GitFlow compliance with proper feature branch development
  - Improved commit message standards without external tool references
  - Better error handling and timeout management for long-running operations

### Fixed
- PostgreSQL version compatibility issues between client (v15) and server (v17) on Quome Cloud
- Role format handling in JavaScript for both quoted and unquoted user role responses
- Filename parsing in backup downloads for cross-browser compatibility
- Database import hanging issues by switching to data-only backups and adding timeouts

### Security
- **Access Control**
  - Strict admin-only access to all backup functionality through JWT and role decorators
  - No exposure of sensitive database credentials or internal paths
  - Secure temporary file handling with automatic cleanup

- **Audit Trail**
  - Complete audit logging for all backup export and import operations
  - User attribution and timestamp tracking for security compliance
  - Operation success/failure logging for administrative oversight

## [1.3.0] - 2025-06-23

### Added
- **Advance Directive Management Enhancement**
  - New advance directive status dropdown with options: "Not Started", "In Progress", "Complete"
  - Enhanced patient form layout with restructured advance directive section
  - Maintains existing advance directive on file checkbox for backward compatibility
  - Database schema updated with AdvanceDirectiveStatus enum type

- **Emergency Contact Medical Information Sharing**
  - New checkbox to control medical information sharing with emergency contacts
  - Updated patient model and API to handle emergency contact permissions
  - Enhanced patient details view to display sharing preferences
  - Database seeder updated with appropriate default values

- **Dashboard Patient Creation Modal**
  - Added complete patient creation modal functionality to dashboard
  - "+New Patient" button now opens full patient form modal
  - Identical functionality to patients page "Add Patient" feature
  - Streamlined workflow for patient management from dashboard

- **Sentry Error Tracking Integration**
  - Comprehensive error monitoring for production environments
  - Automatic exception capture with stack traces
  - Performance monitoring with transaction traces
  - Privacy-aware configuration (no PII by default)
  - Environment-specific error filtering
  - Custom context and tags for better categorization

- **Enhanced Documentation**
  - Updated README with Retell.ai integration details
  - Added Sentry configuration documentation
  - Updated available Just commands
  - Improved environment variable documentation
  - Added comprehensive schema documentation

### Changed
- **Patient Form Restructuring**
  - Reorganized advance directive section layout for better usability
  - Improved form flow with logical grouping of related fields
  - Enhanced visual hierarchy with proper spacing and alignment

- **Database Schema Enhancements**
  - Added emergency_contact_can_share_medical_info boolean field
  - Added advance_directive_status enum field with NOT_STARTED default
  - Updated all seed data to include new field values
  - Maintained backward compatibility with existing data

- **API Improvements**
  - Enhanced patient creation and update endpoints
  - Added validation for new advance directive status field
  - Updated patient schemas to handle new fields
  - Improved error handling and validation messages

- Migrated from Twilio to Retell.ai in documentation
- Updated architecture diagram to reflect current integrations
- Improved Justfile with new development commands
- Enhanced build process with proper dependency installation

### Fixed
- Fixed missing sentry_sdk module causing application crash
- Corrected environment variable references in documentation
- Resolved form handling for checkbox states in patient creation
- Fixed modal form reset functionality on dashboard

## [1.2.0] - 2025-06-16

### Added
- **Ring Now Button**: Third action button on patients page for immediate call initiation
  - Yellow warning-style button with phone-volume icon
  - Confirmation dialog with patient name and phone number
  - Loading state with spinner during call initiation
  - Real-time call status feedback

- **Call Mode Toggle**: Simulation vs Real Call Mode switching
  - Visual toggle button (blue for simulation, red for real)
  - Warning confirmation when switching to real call mode
  - Persistent mode setting across sessions
  - Backend API endpoint for mode management

- **Retell.ai Integration**: Complete calling service integration
  - Environment-aware configuration (local vs production)
  - Support for local and remote agent IDs
  - Dynamic webhook URL construction
  - Phone number normalization to E.164 format
  - Mock call simulation for testing

### Changed
- Enhanced patient schema with phone_number field
- Improved call service with environment detection
- Updated patients page UI with three-button action layout

### Removed
- Twilio dependencies and unused packages
- Legacy Twilio-related imports and code

### Fixed
- Production deployment environment variable configuration
- Webhook URL construction for full domain format
- API endpoint URL paths for call management
- Role authorization for call features

### Security
- Enhanced role-based access control for call management
- Nurses restricted to assigned patients only
- Comprehensive audit logging for call actions

## [1.1.0] - 2025-06-15

### Added
- **Database schema recreation functionality** - New `--recreate-db` flag in deployment script allows complete schema reset
- **FIT Protocol support** - Added new protocol type for wellness monitoring of very fit individuals
- **Enhanced development workflow** - Added uv package manager support with virtual environment management
- **PyCharm integration** - Added setup documentation and configuration for PyCharm IDE
- **Virtual environment validation** - Added checks to ensure proper virtual environment activation
- **Centralized logging** - Implemented consistent logging across all application components
- **RECREATE_SCHEMA environment variable** - Added support for forcing database schema recreation

### Changed
- **Port configuration** - Changed default ports from 8081 to 5000 to avoid TLS terminator conflicts
- **RetellAI configuration** - Aligned variable naming with postgres-demo project (RETELLAI_* prefix)
- **Database seeding** - Enhanced with better logging and error handling
- **Patient data** - Updated seed data with real phone numbers and email addresses
- **Webhook handling** - Improved environment detection for local vs production webhooks
- **Docker configuration** - Updated to use dynamic PORT environment variable
- **Installation process** - Enhanced with multiple installation options (just, manual, PyCharm)

### Fixed
- **Port binding conflicts** - Resolved "Connection in use" errors on port 8081
- **Database enum mismatch** - Fixed production schema missing FIT enum value
- **Docker CMD syntax** - Corrected bash command syntax error in Dockerfile
- **Logging inconsistencies** - Replaced basic logging with centralized logger throughout codebase
- **Environment variable handling** - Improved configuration for dev/prod environments

### Technical Improvements
- Updated `.gitignore` to include `.venv/` directory
- Added proper newline at end of Dockerfile
- Enhanced justfile with uv support and virtual environment checks
- Improved error handling in database operations
- Added comprehensive debug logging for deployment troubleshooting

## [1.0.2] - Previous Release

### Fixed
- Removed redundant Docker build from Quome deployment script
- Updated test imports from app to src module

## [1.0.1] - Previous Release

### Fixed
- Various bug fixes and improvements

## [1.0.0] - Initial Release

### Added
- Initial palliative care platform implementation
- Patient management system
- Protocol-based assessments
- Call management and scheduling
- RetellAI webhook integration
- User authentication and authorization
- Database models and seeding
- Docker containerization
- Quome Cloud deployment support

---

## Release Notes

### Version 1.2.0 Highlights

This release introduces immediate call capabilities and advanced call management features:

**📞 Ring Now Feature**: Added immediate call functionality with a third action button on the patients page, enabling instant communication with patients through Retell.ai integration.

**🔄 Call Mode Management**: Implemented sophisticated call mode toggle between simulation and real call modes, with safety confirmations and persistent settings.

**🤖 Enhanced AI Integration**: Complete Retell.ai integration with environment-aware configuration, supporting both local development and production deployment scenarios.

**🔐 Security Improvements**: Enhanced role-based access control with comprehensive audit logging for all call-related actions.

**🗑️ Code Cleanup**: Removed legacy Twilio dependencies and code, streamlining the codebase for better maintainability.

### Version 1.1.0 Highlights

This release focuses on resolving critical deployment issues and improving the development experience:

**🔧 Port Configuration Fix**: The major issue where the application couldn't start due to port 8081 conflicts with the TLS terminator has been resolved. The application now uses port 5000 internally while maintaining external compatibility.

**🗃️ Database Management**: Added powerful database schema management with the new `--recreate-db` flag, allowing complete schema recreation when enum types or other schema changes are needed.

**💪 Enhanced Development**: Significant improvements to the development workflow with uv package manager support, virtual environment validation, and comprehensive documentation.

**📊 FIT Protocol**: New protocol type for monitoring very fit individuals, expanding the platform's capabilities beyond traditional palliative care.

**🔍 Better Logging**: Centralized logging implementation provides consistent, structured logging across all components for easier debugging and monitoring.
