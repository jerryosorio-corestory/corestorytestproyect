# Feature: Loan Renewal
# Extends the circulation workflow so staff can renew eligible loans.

Feature: Loan Renewal
  As a circulation desk staff member
  I want to renew active loans for members
  So that members can keep books longer without creating a new checkout

  Background:
    Given the library has a book titled "Refactoring" with ISBN "9780201485677"
    And there is an active member named "Dana Lopez" with email "dana@example.com"
    And Dana has an open loan for "Refactoring"

  Scenario: Renew an eligible loan
    Given the loan is still within the original 14-day period
    When staff renews Dana's loan for "Refactoring"
    Then the due date is extended by 7 more days
    And the renewal count becomes 1
    And the loan remains open

  Scenario: Cannot renew an overdue loan
    Given the loan due date was 1 day ago
    When staff renews Dana's loan for "Refactoring"
    Then the system rejects the request
    And the error message contains "already overdue"

  Scenario: Cannot renew a loan more than once
    Given Dana's loan for "Refactoring" has already been renewed once
    When staff renews Dana's loan for "Refactoring" again
    Then the system rejects the request
    And the error message contains "renewal limit"

  Scenario: Cannot renew a returned loan
    Given Dana has already returned "Refactoring"
    When staff renews Dana's loan for "Refactoring"
    Then the system rejects the request
    And the error message contains "already been closed"
