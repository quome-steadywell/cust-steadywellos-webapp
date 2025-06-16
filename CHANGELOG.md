# Changelog

All notable changes to the SteadyWell Palliative Care Platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- Initial release with core palliative care platform features
- Patient management system
- Assessment workflows
- Call scheduling functionality
- User authentication and role-based access control