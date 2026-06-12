## ADDED Requirements

### Requirement: MoodleWSClient returns 502 when Moodle is unreachable

The system SHALL return HTTP `502 Bad Gateway` when the Moodle Web Services endpoint is unreachable or returns an error, so that the client can fall back to manual `.xlsx`/`.csv` import.

#### Scenario: Moodle WS returns 502 on connection timeout

- **WHEN** `MoodleWSClient.get_users()` is called and Moodle does not respond within 30 seconds
- **THEN** the client raises `MoodleWSError`
- **AND** the API layer maps it to HTTP `502 Bad Gateway`
- **AND** the response body includes a message suggesting manual import

#### Scenario: Moodle WS returns 502 on HTTP error status

- **WHEN** `MoodleWSClient.get_users()` is called and Moodle returns HTTP 500
- **THEN** the client raises `MoodleWSError`
- **AND** the API layer returns `502 Bad Gateway`

#### Scenario: Moodle WS succeeds and returns data

- **WHEN** `MoodleWSClient.get_users()` is called and Moodle responds with HTTP 200
- **THEN** the data is returned as parsed JSON
- **AND** no error is raised

### Requirement: MoodleWSClient retries failed requests with exponential backoff

The system SHALL retry failed HTTP requests to Moodle WS up to 3 times with exponential backoff before raising `MoodleWSError`.

#### Scenario: Request succeeds on second attempt after transient failure

- **WHEN** first request to Moodle fails with a network error
- **AND** second request succeeds
- **THEN** the client returns the data successfully
- **AND** no error is raised to the caller

#### Scenario: All retry attempts fail

- **WHEN** all 3 attempts to Moodle fail
- **THEN** `MoodleWSError` is raised after the last attempt
- **AND** the error message indicates the number of retries attempted

### Requirement: MoodleWSClient provides methods for users, activities, and enrollments

The client SHALL expose `get_users()`, `get_activities()`, and `sync_enrollments()` methods that return typed data structures for each Moodle entity.

#### Scenario: get_users returns user list

- **WHEN** `get_users(course_id)` is called
- **THEN** it returns a list of dicts with keys: `id`, `firstname`, `lastname`, `email`

#### Scenario: get_activities returns activity list

- **WHEN** `get_activities(course_id)` is called
- **THEN** it returns a list of dicts with keys: `id`, `name`, `type`, `duedate`

#### Scenario: sync_enrollments sends user-course mappings to Moodle

- **WHEN** `sync_enrollments(course_id, user_ids)` is called
- **THEN** it POSTs to Moodle WS endpoint with the enrollment data
- **AND** returns `True` on success