# Feature: Book Return
# Covers the return flow including late fee calculation and member reinstatement.

Feature: Book Return
  As a library staff member
  I want to process book returns
  So that books become available again and late fees are applied correctly

  Background:
    Given the library has a book titled "Design Patterns" with ISBN "9780201633610"
    And there is an active member named "Bob Jones" with email "bob@example.com"
    And Bob has an open loan for "Design Patterns"

  Scenario: On-time book return with no late fee
    Given the loan is within the 14-day loan period
    When Bob returns "Design Patterns"
    Then the loan is marked as returned
    And the late fee for this loan is 0.00
    And the book "Design Patterns" is marked as available again

  Scenario: Late return triggers a late fee
    Given the loan due date was 5 days ago
    When Bob returns "Design Patterns"
    Then the loan is marked as returned
    And the late fee for this loan is 2.50
    And Bob's outstanding balance is increased by 2.50

  Scenario: Late fee is capped at the maximum allowed amount
    Given the loan due date was 30 days ago
    When Bob returns "Design Patterns"
    Then the loan is marked as returned
    And the late fee for this loan is 10.00
    And the late fee does not exceed the maximum cap of 10.00

  Scenario: Outstanding fees above threshold suspends the member
    Given Bob's outstanding balance is 4.75 before this return
    And the loan due date was 2 days ago
    When Bob returns "Design Patterns"
    Then a late fee of 1.00 is applied
    And Bob's outstanding balance becomes 5.75
    And Bob's account status is set to suspended

  Scenario: Cannot return a book that was already returned
    Given the loan has already been closed
    When staff attempts to return "Design Patterns" again
    Then the system rejects the request
    And the error message contains "already been closed"
