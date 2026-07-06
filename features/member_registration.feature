# Feature: Member Registration
# Covers the sign-up flow and the business rules that protect data integrity.

Feature: Member Registration
  As a library administrator
  I want to register new members
  So that they can borrow books from the library

  Scenario: Successful registration with all fields
    When I register a member with:
      | first_name | Jane          |
      | last_name  | Doe           |
      | email      | jane@test.com |
      | phone      | 555-9876      |
    Then a member profile is created
    And the member status is "active"
    And the outstanding fees balance is 0.00

  Scenario: Registration fails when email is already in use
    Given a member with email "jane@test.com" already exists
    When I try to register another member with email "jane@test.com"
    Then the system rejects the request
    And the error message contains "already exists"

  Scenario: Registration fails with an invalid email format
    When I try to register a member with email "not-valid-email"
    Then the system rejects the request
    And the error message contains "Invalid email address"

  Scenario: Registration fails when required fields are missing
    When I try to register a member without a last name
    Then the system rejects the request

  Scenario: Fee payment reinstates a suspended member
    Given a member "Charlie Brown" is suspended with 5.00 outstanding fees
    When Charlie pays 5.00
    Then Charlie's outstanding balance becomes 0.00
    And Charlie's account status is set to active

  Scenario: Overpaying fees is rejected
    Given a member "Charlie Brown" has 3.00 outstanding fees
    When Charlie tries to pay 5.00
    Then the system rejects the request
    And the error message contains "exceeds outstanding balance"

  Scenario: Filter members by suspended status
    Given there is one suspended member and one active member
    When I list members with status set to "suspended"
    Then only the suspended member appears in the results
