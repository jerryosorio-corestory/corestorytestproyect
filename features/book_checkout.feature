# Feature: Book Checkout
# Covers the primary borrowing flow and its constraint scenarios.
# These scenarios are designed to be consumed by the "Build BDD Scenarios" workflow.

Feature: Book Checkout
  As a library member
  I want to borrow books from the library
  So that I can read them at home

  Background:
    Given the library has a book titled "Clean Code" with ISBN "9780132350884"
    And there is an active member named "Alice Smith" with email "alice@example.com"

  Scenario: Successful book checkout
    When Alice checks out "Clean Code"
    Then a loan record is created for Alice
    And the book "Clean Code" is marked as unavailable
    And the due date is set to 14 days from today

  Scenario: Member attempts to borrow an already checked-out book
    Given "Clean Code" is already checked out by another member
    When Alice tries to check out "Clean Code"
    Then the system rejects the request
    And the error message is "not available — it is currently on loan"

  Scenario: Suspended member cannot borrow books
    Given Alice's account has been suspended
    When Alice tries to check out "Clean Code"
    Then the system rejects the request
    And the error message contains "cannot borrow books"

  Scenario: Member exceeds the concurrent loan limit
    Given Alice already has 3 books on loan
    And the library has another book titled "The Pragmatic Programmer"
    When Alice tries to check out "The Pragmatic Programmer"
    Then the system rejects the request
    And the error message contains "already has 3 books on loan"
