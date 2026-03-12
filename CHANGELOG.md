# Change Log

All notable changes to the "velora" extension will be documented in this file.

Check [Keep a Changelog](http://keepachangelog.com/) for recommendations on how to structure this file.

## [1.1.0] - 2026-03-09

### Changed
- Migrated from deprecated `google-generativeai` SDK to new `google-genai` SDK
- Updated AI model from `gemini-2.0-flash` / `gemini-1.5-flash` to `gemini-2.5-flash`
- Improved error handling — graceful API key validation before agent starts
- Fixed error popup spam from stderr (now shows only once)
- Fixed socket resource leak in internet connectivity check
- Removed stray JavaScript comment visible in the webview UI
- Updated README with comprehensive documentation

## [1.0.0]

- Initial release