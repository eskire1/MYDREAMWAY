USE DataBase_DropShipping
GO


--- /// Получение информации об индексах
--- Через представление sys.indexes
SELECT 
    t.name AS TableName,
    i.name AS IndexName,
    i.type_desc AS IndexType
FROM 
    sys.indexes i
JOIN 
    sys.tables t ON i.object_id = t.object_id
WHERE 
    i.name IS NOT NULL;


--- Через системную процедуру sp_helpindex
EXEC sp_helpindex 'Products';
EXEC sp_helpindex 'Suppliers';


--- Физическая статистика
SELECT 
    OBJECT_NAME(ips.object_id) AS TableName,
    i.name AS IndexName,
    ips.index_type_desc,
    ips.avg_fragmentation_in_percent
FROM 
    sys.dm_db_index_physical_stats (DB_ID(), NULL, NULL, NULL, 'LIMITED') ips
JOIN 
    sys.indexes i ON i.object_id = ips.object_id AND i.index_id = ips.index_id;



--- /// Сложные SELECT-запросы
-- 1. Total quantity of products ordered by customer
SELECT c.first_name, c.last_name, SUM(oi.quantity) AS total_quantity
FROM Customers c
JOIN Orders o ON c.id = o.customer_id
JOIN Order_Items oi ON o.id = oi.order_id
GROUP BY c.first_name, c.last_name
ORDER BY total_quantity DESC;

-- 2. Average product price by category
SELECT category, AVG(price) AS avg_price
FROM Products
GROUP BY category
ORDER BY avg_price DESC;

-- 3. Suppliers and total number of their products in stock
SELECT s.name, SUM(p.stock_quantity) AS total_stock
FROM Suppliers s
JOIN Products p ON s.id = p.supplier_id
GROUP BY s.name
ORDER BY total_stock DESC;

-- 4. Top 5 most frequently ordered products
SELECT TOP 5 p.name, COUNT(*) AS order_count
FROM Products p
JOIN Order_Items oi ON p.id = oi.product_id
GROUP BY p.name
ORDER BY order_count DESC;

-- 5. Orders with multiple items and total cost
SELECT o.id AS order_id, c.first_name, c.last_name, SUM(oi.purchase_price * oi.quantity) AS total_cost
FROM Orders o
JOIN Customers c ON o.customer_id = c.id
JOIN Order_Items oi ON o.id = oi.order_id
GROUP BY o.id, c.first_name, c.last_name
HAVING COUNT(oi.id) > 1
ORDER BY total_cost DESC;

-- 6. Products with no stock and their suppliers
SELECT p.name AS product, s.name AS supplier
FROM Products p
JOIN Suppliers s ON p.supplier_id = s.id
WHERE p.stock_quantity = 0;


--- Для просмотра фактического плана выполнения
--- SET STATISTICS PROFILE ON;


--- /// Создание индексов для улучшения запросов
-- По внешним ключам
CREATE INDEX IX_Orders_CustomerID ON Orders(customer_id);
CREATE INDEX IX_Order_Items_ProductID ON Order_Items(product_id);

-- Часто группируемые и фильтруемые поля
CREATE INDEX IX_Products_Category ON Products(category);
CREATE INDEX IX_Products_StockQuantity ON Products(stock_quantity);

-- Для сортировки и агрегации
CREATE INDEX IX_Order_Items_OrderID ON Order_Items(order_id);
