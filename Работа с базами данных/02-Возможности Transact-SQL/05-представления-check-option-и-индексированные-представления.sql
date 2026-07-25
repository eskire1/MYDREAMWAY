USE DataBase_DropShipping
GO

--- Удаление всех представлений
DROP VIEW IF EXISTS v_ExpensiveProducts;
DROP VIEW IF EXISTS v_OutOfStock;
DROP VIEW IF EXISTS v_OrderDetails;
DROP VIEW IF EXISTS v_AvgPriceByCategory;
DROP VIEW IF EXISTS v_ReliableSuppliers;
DROP VIEW IF EXISTS v_TopReliableSuppliers;
DROP VIEW IF EXISTS v_SupplierProductSummary;
GO

--- Создание представления на основе таблицы Products
CREATE VIEW v_ExpensiveProducts
AS
SELECT *
FROM Products
WHERE price > 500;
GO


--- Выполнение двух запросов к представлению
-- Все товары из представления
SELECT * FROM v_ExpensiveProducts;
-- Только названия и цены
SELECT name, price FROM v_ExpensiveProducts WHERE category = 'Electronics';


--- Пробуем выполнение INSERT, UPDATE, DELETE
-- INSERT
INSERT INTO v_ExpensiveProducts (name, description, price, stock_quantity, supplier_id, category)
VALUES ('Smartphone UltraMax', 'High-end model', 999.99, 10, 1, 'Electronics');
-- UPDATE
UPDATE v_ExpensiveProducts
SET price = 550
WHERE name = 'Smartphone UltraMax';
-- DELETE
DELETE FROM v_ExpensiveProducts
WHERE name = 'Smartphone UltraMax';
GO


--- Изменение представления. Добавление WITH CHECK OPTION
ALTER VIEW v_ExpensiveProducts
AS
SELECT *
FROM Products
WHERE price > 500
WITH CHECK OPTION;
GO


--- Повтор INSERT, UPDATE, DELETE
-- INSERT, но с ценой меньше 500 — приведёт к ошибке!
INSERT INTO v_ExpensiveProducts (name, description, price, stock_quantity, supplier_id, category)
VALUES ('Budget Phone', 'Affordable model', 640, 15, 1, 'Electronics');
-- UPDATE: понизим цену существующего товара ниже 500 — приведёт к ошибке!
UPDATE v_ExpensiveProducts
SET price = 780
WHERE name = 'Smartphone UltraMax';
GO


--- Создание ещё 4-5 представлений
--- Товары без остатков
CREATE VIEW v_OutOfStock
AS
SELECT name, category
FROM Products
WHERE stock_quantity = 0;
GO
--- Товары с деталями
CREATE VIEW v_OrderDetails
AS
SELECT o.id AS order_id, c.first_name, c.last_name, p.name AS product, oi.quantity
FROM Orders o
JOIN Customers c ON o.customer_id = c.id
JOIN Order_Items oi ON o.id = oi.order_id
JOIN Products p ON oi.product_id = p.id;
GO
--- Средняя цена по категориям
CREATE VIEW v_AvgPriceByCategory
AS
SELECT category, AVG(price) AS avg_price
FROM Products
GROUP BY category;
GO
--- Поставщики с высокой надежностью
CREATE VIEW v_ReliableSuppliers
AS
SELECT * FROM Suppliers
WHERE reliability_rating >= 4;
GO
--- Представление на основе другого представления
CREATE VIEW v_TopReliableSuppliers
AS
SELECT name FROM v_ReliableSuppliers
WHERE delivery_time = '1 week';
GO


--- Выводим список всех представлений
SELECT name FROM sys.views;


--- Посмотреть код представления
EXEC sp_helptext 'v_OrderDetails';


--- Определить зависимости представлений от таблицы Products
SELECT DISTINCT OBJECT_NAME(object_id) AS ViewName
FROM sys.sql_dependencies
WHERE referenced_major_id = OBJECT_ID('Products');
GO


--- Влияние индексированного представления на производительность
--- Создание представления
CREATE VIEW v_SupplierProductSummary
WITH SCHEMABINDING
AS
SELECT s.id AS supplier_id, COUNT_BIG(*) AS product_count
FROM dbo.Suppliers s
JOIN dbo.Products p ON s.id = p.supplier_id
GROUP BY s.id;
GO
--- Создание уникального кластеризованного индекса
CREATE UNIQUE CLUSTERED INDEX IX_v_SupplierProductSummary
ON v_SupplierProductSummary(supplier_id);
--- Команда для сравнения плана представления
SELECT * FROM v_SupplierProductSummary

SELECT * FROM INFORMATION_SCHEMA.VIEWS
GO


--- Тесты (мои)
SELECT category, COUNT(*) AS count 
FROM Products 
GROUP BY category
GO