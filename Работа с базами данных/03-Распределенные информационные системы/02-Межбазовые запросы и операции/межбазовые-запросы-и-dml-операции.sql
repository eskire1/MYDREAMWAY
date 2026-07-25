use DataBase_Products
GO

SELECT name, price
FROM [DataBase_Products].dbo.Products;

SELECT *
FROM [DataBase_Products].dbo.Products
WHERE price > 700;

SELECT name, price
FROM [DataBase_Products].dbo.Products
WHERE price < 300
UNION
SELECT name, price
FROM [DataBase_Products].dbo.Products
WHERE price > 800;

SELECT name FROM dbo.Products
WHERE category = 'Electronics'
INTERSECT
SELECT name FROM dbo.Products
WHERE price > 500;

SELECT p.name AS Product, s.name AS Supplier
FROM [DataBase_Products].dbo.Products p
CROSS JOIN [DataBase_Products].dbo.Suppliers s;

INSERT INTO dbo.Products (name, category, price, stock_quantity, supplier_id)
VALUES ('Wireless Mouse', 'Electronics', 1200, 50, 3);

UPDATE dbo.Products
SET price = price * 1.1
WHERE category = 'Electronics';



USE [DataBase_Sales];
GO

INSERT INTO dbo.Customers (first_name, last_name, email, phone)
VALUES ('Anna', 'Smirnova', 'anna.smirnova@example.com', '+79991234567');

UPDATE dbo.Orders
SET status = 'Completed'
WHERE id = 5;

DELETE FROM dbo.Customers
WHERE id NOT IN (SELECT DISTINCT customer_id FROM dbo.Orders);



USE [DataBase_Products];
GO

DELETE FROM dbo.Products
WHERE stock_quantity = 0;