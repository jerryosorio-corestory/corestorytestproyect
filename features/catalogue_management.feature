# Feature: Book Catalogue Management
# Covers the full lifecycle of books in the system catalogue.

Feature: Book Catalogue Management
  As a library administrator
  I want to manage the book catalogue
  So that members can discover and borrow books

  Scenario: Add a new book with valid data
    When I add a book with:
      | title          | The Clean Coder            |
      | author         | Robert C. Martin           |
      | isbn           | 9780137081073              |
      | genre          | Software Engineering       |
      | published_year | 2011                       |
    Then the book appears in the catalogue
    And the book is marked as available

  Scenario: Adding a book with an invalid ISBN is rejected
    When I try to add a book with ISBN "INVALID-ISBN"
    Then the system rejects the request
    And the error message contains "Invalid ISBN format"

  Scenario: Adding a duplicate ISBN is rejected
    Given a book with ISBN "9780137081073" already exists in the catalogue
    When I try to add another book with ISBN "9780137081073"
    Then the system rejects the request
    And the error message contains "already exists"

  Scenario: Search for books by title keyword
    Given the catalogue contains books titled "Clean Code" and "Clean Architecture"
    When I search for "Clean"
    Then both books appear in the search results

  Scenario: Delete an available book
    Given the catalogue contains a book that is currently available
    When I delete that book
    Then the book is removed from the catalogue

  Scenario: Cannot delete a book that is on loan
    Given a book is currently checked out by a member
    When I try to delete that book
    Then the system rejects the request
    And the error message contains "currently on loan"
