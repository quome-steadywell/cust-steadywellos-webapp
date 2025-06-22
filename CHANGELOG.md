# Changelog

All notable changes to the SteadyWell Palliative Care Platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
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

### Changed
- Migrated from Twilio to Retell.ai in documentation
- Updated architecture diagram to reflect current integrations
- Improved Justfile with new development commands
- Enhanced build process with proper dependency installation

### Fixed
- Fixed missing sentry_sdk module causing application crash
- Corrected environment variable references in documentation

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
