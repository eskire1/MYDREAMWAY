-- 1. Create database
CREATE DATABASE ShopDB1;
GO

-- 2. Connect to database
USE ShopDB1;
GO

-- 3. Create table Goods
CREATE TABLE Goods (
    DeptID INT CHECK (DeptID BETWEEN 1 AND 10) NOT NULL,
    GoodID INT IDENTITY(10,10) PRIMARY KEY,
    GName VARCHAR(20) NOT NULL,
    Descr VARCHAR(50) NULL,
    Price SMALLMONEY CHECK (Price > 0) NOT NULL,
    GCount INT CHECK (GCount > 0) NOT NULL,
    CONSTRAINT unique_GName_Dept UNIQUE (DeptID, GName)
);
GO

-- 4. Insert data into Goods table
INSERT INTO Goods (DeptID, GName, Descr, Price, GCount) VALUES
(1, 'ballpoint pen', NULL, 2, 100),
(1, 'gel pen', NULL, 10, 50),
(1, 'pencil', NULL, 5, 200),
(1, 'mechanical pencil', NULL, 10, 30),
(2, 'household soap', NULL, 6, 200),
(2, 'baby soap', NULL, 7, 150),
(2, 'shampoo "Clean Line"', NULL, 50, 7);
GO

-- 5. Add new products
INSERT INTO Goods (DeptID, GName, Descr, Price, GCount) VALUES
(3, 'country bread', NULL, 20, 30),
(3, 'pen', NULL, 15, 40);
GO

-- 6. Delete products without description
DELETE FROM Goods WHERE Descr IS NULL;
GO

-- 7. Increase prices by 10%
UPDATE Goods SET Price = Price * 1.1;
GO

-- 8. Select all data from Goods table
SELECT * FROM Goods;
GO

-- 9. Select products from department 1
SELECT GoodID, GName, Descr FROM Goods WHERE DeptID = 1;
GO

-- 10. Select products in price range 10-30
SELECT * FROM Goods WHERE Price BETWEEN 10 AND 30;
GO

-- 11. Select products from departments 1 and 3
SELECT * FROM Goods WHERE DeptID IN (1, 3);
GO

-- 12. Select products with names starting with 'p'
SELECT * FROM Goods WHERE GName LIKE 'p%';
GO

-- 13. Select products with '_' in name
SELECT * FROM Goods WHERE GName LIKE '%_%';
GO

-- 14. Select all product names
SELECT GName FROM Goods;
GO

-- 15. Select distinct product names
SELECT DISTINCT GName FROM Goods;
GO

-- 16. Select products with computed total cost
SELECT *, (Price * GCount) AS TotalCost FROM Goods;
GO

-- 17. Select min, avg, max prices of products
SELECT MIN(Price) AS MinPrice, AVG(Price) AS AvgPrice, MAX(Price) AS MaxPrice FROM Goods;
GO

-- 18. Count products in department 1
SELECT COUNT(*) AS ProductCount FROM Goods WHERE DeptID = 1;
GO

-- 19. Count products with description
SELECT COUNT(*) AS DescribedProducts FROM Goods WHERE Descr IS NOT NULL;
GO

-- 20. Calculate total cost of products in department 2
SELECT SUM(Price * GCount) AS TotalDept2 FROM Goods WHERE DeptID = 2;
GO

-- 21. Sort products by name
SELECT * FROM Goods ORDER BY GName;
GO

-- 22. Sort products by department and descending price
SELECT * FROM Goods ORDER BY DeptID, Price DESC;
GO

-- 23. Calculate total sold product cost per department
SELECT DeptID, SUM(Price * GCount) AS TotalSold FROM Goods GROUP BY DeptID;
GO

-- 24. Calculate average price for products above 9
SELECT AVG(Price) AS AvgPrice FROM Goods WHERE Price > 9;
GO

-- 25. Calculate max price per product name
SELECT GName, MAX(Price) AS MaxPrice FROM Goods GROUP BY GName;
GO

-- 26. Select departments with more than two products
SELECT DeptID FROM Goods GROUP BY DeptID HAVING COUNT(GoodID) > 2;
GO


SELECT * FROM Goods;
GO
