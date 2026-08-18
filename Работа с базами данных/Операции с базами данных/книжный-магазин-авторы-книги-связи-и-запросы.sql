CREATE DATABASE Lab2_BookShop;

EXEC sp_helpdb Lab2_BookShop;
Go

CREATE TABLE Authors (
	AuthorID int IDENTITY NOT NULL,
	FirstName VARCHAR(30) NOT NULL default 'unknown',
	LastName VARCHAR(30) NULL,
	YearBorn CHAR(4) NULL,
	YearDied CHAR(4) NOT NULL default 'no',
);

EXEC sp_help Authors;

ALTER TABLE Authors
ADD Info NVARCHAR(100) NULL;
GO

SELECT * FROM Authors;

ALTER TABLE Authors
ADD Descr VARCHAR(200) NOT NULL;
GO

INSERT INTO Authors (FirstName, LastName, YearBorn, YearDied, Descr)
VALUES ('Artur', 'Petrov', '2010', '1970', 'None');


USE Lab2_BookShop
GO
CREATE TABLE Books (
	BookID int not null PRIMARY KEY,
	Title VARCHAR(100) not null,
	Janr VARCHAR(50) null
);

EXEC sp_help Books;

USE Lab2_BookShop
GO

CREATE TABLE BooksAuthor (
	BookID int not null,
	AuthorID int not null
);

EXEC sp_help BooksAuthor;

ALTER TABLE BooksAuthor
ADD PRIMARY KEY (BookID, AuthorID)

ALTER TABLE BooksAuthor
ADD CONSTRAINT Books_BookID
FOREIGN KEY (BookID) REFERENCES Books (BookID)

ALTER TABLE Authors
ADD PRIMARY KEY (AuthorID)

ALTER TABLE BooksAuthor
ADD CONSTRAINT Books_AuthorID
FOREIGN KEY (AuthorID) REFERENCES Authors (AuthorID)

ALTER TABLE Authors
ADD CONSTRAINT check_YearBorn
CHECK (YearBorn LIKE '[1-2][0,6-9][0-9][0-9]');

ALTER TABLE Authors
ADD CONSTRAINT check_YearDied
CHECK (YearDied LIKE '[1-2][0,6-9][0-9][0-9]' or YearDied LIKE 'no');

ALTER TABLE Authors
ADD CONSTRAINT check_YearBorn_YearDied
CHECK (YearDied > YearBorn);

INSERT INTO Authors (FirstName, LastName, YearBorn, YearDied, Descr)
VALUES 
('George', 'Orwell', '1903', '1950', 'English novelist, essayist, journalist and critic.'),
('J.K.', 'Rowling', '1965', 'no', 'British author, best known for the Harry Potter series.'),
('Fyodor', 'Dostoevsky', '1821', '1881', 'Russian novelist, journalist, and philosopher.');

INSERT INTO Books (BookID, Title, Janr)
VALUES 
(1, '1984', 'Dystopian Fiction'),
(2, 'Harry Potter and the Philosopher"s Stone', 'Fantasy'),
(3, 'Crime and Punishment', 'Psychological Fiction');

INSERT INTO BooksAuthor (BookID, AuthorID)
VALUES 
(1, 1),  -- Orwell wrote "1984"
(2, 2),  -- Rowling wrote "Harry Potter"
(3, 3);  -- Dostoevsky wrote "Crime and Punishment"


SELECT * FROM Authors;
SELECT * FROM Books;
SELECT * FROM BooksAuthor;

SELECT * FROM Authors ORDER BY YearBorn DESC;

SELECT FirstName, LastName, YearBorn FROM Authors ORDER BY YearBorn ASC;

SELECT FirstName, LastName, YearBorn FROM Authors WHERE YearBorn > '1900';

SELECT Title FROM Books WHERE Janr = 'Fantasy';

SELECT Books.Title, Authors.FirstName, Authors.LastName FROM Books
JOIN BooksAuthor ON Books.BookID = BooksAuthor.BookID
JOIN Authors ON BooksAuthor.AuthorID = Authors.AuthorID;