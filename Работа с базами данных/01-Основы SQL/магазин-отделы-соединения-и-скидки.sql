USE ShopDB
GO

-- 4.1 Create table Departments
CREATE TABLE Departments (
    DeptID INT PRIMARY KEY CHECK (DeptID BETWEEN 1 AND 10),
    DeptName VARCHAR(50) NOT NULL
);

-- 4.2 Populate Departments table (Department IDs from Goods table)
INSERT INTO Departments (DeptID, DeptName)
SELECT DISTINCT DeptID, '' FROM Goods;

-- 4.3 Manually fill department names via GUI
-- (This step is performed manually in SSMS)

-- 4.4 Cartesian product of Departments and Goods tables
SELECT * FROM Departments, Goods;

-- 4.5 Inner join using WHERE condition
SELECT * FROM Departments, Goods WHERE Departments.DeptID = Goods.DeptID;

-- 4.6 Inner join using JOIN
SELECT * FROM Departments INNER JOIN Goods ON Departments.DeptID = Goods.DeptID;

-- 4.7 Add new department
INSERT INTO Departments (DeptID, DeptName) VALUES (10, 'Electronics');

-- 4.8 Left join
SELECT * FROM Departments LEFT JOIN Goods ON Departments.DeptID = Goods.DeptID;

SET IDENTITY_INSERT Goods ON;

-- 4.9 Add new product without corresponding department
INSERT INTO Goods (DeptID, GoodID, GName, Descr, Price, GCount) 
VALUES (11, 100, 'Unknown Product', 'Description', 20, 5);

SET IDENTITY_INSERT Goods OFF;

-- 4.10 Right join
SELECT * FROM Departments RIGHT JOIN Goods ON Departments.DeptID = Goods.DeptID;

-- 4.11 Full join
SELECT * FROM Departments FULL JOIN Goods ON Departments.DeptID = Goods.DeptID;

-- 4.12 Select all mismatched records
SELECT DeptID, DeptName FROM Departments 
WHERE DeptID NOT IN (SELECT DISTINCT DeptID FROM Goods)
UNION
SELECT DeptID, GName FROM Goods
WHERE DeptID NOT IN (SELECT DISTINCT DeptID FROM Departments);

-- 4.13 Select departments with products (three methods)
-- 1. Using JOIN
SELECT DISTINCT Departments.DeptID, DeptName FROM Departments
JOIN Goods ON Departments.DeptID = Goods.DeptID;
-- 2. Using EXISTS
SELECT DISTINCT DeptID, DeptName FROM Departments
WHERE EXISTS (SELECT 1 FROM Goods WHERE Goods.DeptID = Departments.DeptID);
-- 3. Using COUNT()
SELECT DeptID, DeptName FROM Departments WHERE DeptID IN (
    SELECT DeptID FROM Goods GROUP BY DeptID HAVING COUNT(*) > 0
);

-- 4.14 Total sales amount per department
SELECT Departments.DeptID, DeptName, SUM(Price * GCount) AS TotalSales
FROM Departments
JOIN Goods ON Departments.DeptID = Goods.DeptID
GROUP BY Departments.DeptID, DeptName;

-- 4.15 Department with maximum total sales
SELECT TOP 1 Departments.DeptID, DeptName, SUM(Price * GCount) AS TotalSales
FROM Departments
JOIN Goods ON Departments.DeptID = Goods.DeptID
GROUP BY Departments.DeptID, DeptName
ORDER BY TotalSales DESC;

-- 4.16 Top two departments with highest sales
SELECT TOP 2 Departments.DeptID, DeptName, SUM(Price * GCount) AS TotalSales
FROM Departments
JOIN Goods ON Departments.DeptID = Goods.DeptID
GROUP BY Departments.DeptID, DeptName
ORDER BY TotalSales DESC;

-- 4.17 Percentage ratio of product price to total department price
SELECT G.GoodID, G.GName, G.Price, 
       (G.Price / SUM(G.Price) OVER (PARTITION BY G.DeptID)) * 100 AS PricePercent
FROM Goods G;

-- 4.18 Increase prices by 10% relative to the average price
UPDATE Goods SET Price = Price * 1.1;

-- 4.19 Create Discount table and insert data with discount calculation
CREATE TABLE Discount (
    GoodID INT PRIMARY KEY,
    GName VARCHAR(20),
    Price SMALLMONEY,
    DiscountAmount SMALLMONEY
);

INSERT INTO Discount (GoodID, GName, Price, DiscountAmount)
SELECT GoodID, GName, Price,
       CASE 
           WHEN Price < 10 THEN Price * 0.2
           WHEN Price BETWEEN 10 AND 50 THEN Price * 0.1
           ELSE Price * 0.05
       END
FROM Goods;

-- 4.20 Add foreign key constraint and fix errors
ALTER TABLE Goods ADD CONSTRAINT FK_Goods_Departments FOREIGN KEY (DeptID) REFERENCES Departments(DeptID);


SELECT * FROM Departments;
