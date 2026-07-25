-- 1. Создаём базу данных
CREATE DATABASE TradeDB;
GO
USE TradeDB;
GO

-- 2. Таблица поставщиков
CREATE TABLE Suppliers (
    SupplierID INT IDENTITY(1,1) PRIMARY KEY,     -- аналог +Autoincrement
    SupplierName NVARCHAR(100) NOT NULL,          -- обязательное поле
    Phone NVARCHAR(20) NULL,
    City NVARCHAR(50) NULL
);
GO

-- 3. Таблица товаров
CREATE TABLE Products (
    ProductID INT IDENTITY(1,1) PRIMARY KEY,      -- ключевое поле
    ProductName NVARCHAR(100) NOT NULL,
    Category NVARCHAR(50) NULL,
    Price DECIMAL(10,2) NOT NULL,
    Quantity INT NOT NULL,
    SupplierID INT NOT NULL,
    CONSTRAINT FK_Products_Suppliers FOREIGN KEY (SupplierID)
        REFERENCES Suppliers(SupplierID)          -- связь "многие к одному"
);
GO

-- 4. Таблица заказов
CREATE TABLE Orders (
    OrderID INT IDENTITY(1,1) PRIMARY KEY,
    OrderDate DATE NOT NULL,
    CustomerName NVARCHAR(100) NOT NULL,
    ProductID INT NOT NULL,
    Quantity INT NOT NULL,
    UnitPrice DECIMAL(10,2) NOT NULL,                 -- цена на момент заказа
    TotalPrice AS (Quantity * UnitPrice) PERSISTED,   -- вычисляемый столбец (без подзапроса)
    CONSTRAINT FK_Orders_Products FOREIGN KEY (ProductID)
        REFERENCES Products(ProductID)
);
GO

-- 5. Добавляем пример данных в таблицу поставщиков
INSERT INTO Suppliers (SupplierName, Phone, City) VALUES
(N'ООО "КофеТорг"', N'+7 (999) 111-22-33', N'Москва'),
(N'ЗАО "Сладкий Дом"', N'+7 (999) 222-33-44', N'Санкт-Петербург');
GO

-- 6. Добавляем товары
INSERT INTO Products (ProductName, Category, Price, Quantity, SupplierID) VALUES
(N'Кофе арабика', N'Продукты', 299.99, 50, 1),
(N'Шоколад молочный', N'Сладости', 149.50, 100, 2);
GO

-- 7. Добавляем заказы
INSERT INTO Orders (OrderDate, CustomerName, ProductID, Quantity, UnitPrice)
SELECT '2025-11-06', N'Петров П.П.', p.ProductID, 3, p.Price
FROM Products p
WHERE p.ProductID = 2;
GO

-- 8. Проверим данные
SELECT * FROM Suppliers;
SELECT * FROM Products;
SELECT * FROM Orders;
GO

-- Пример запроса (аналог ADOQuery)
SELECT ProductID, ProductName, Price
FROM Products
WHERE Price > 100;

-- Первая запись
SELECT TOP 1 * FROM Products ORDER BY ProductID ASC;

-- Последняя запись
SELECT TOP 1 * FROM Products ORDER BY ProductID DESC;

-- Вставка
INSERT INTO Products (ProductName, Category, Price, Quantity, SupplierID)
VALUES (N'Чай зеленый', N'Продукты', 199.99, 30, 1);

SELECT * FROM Products;

-- Редактирование
UPDATE Products
SET Price = 179.99
WHERE ProductID = 1;

SELECT * FROM Products;

-- Удаление
DELETE FROM Products
WHERE ProductID = 4;

SELECT * FROM Products;




--- Алиас
EXEC sp_addlinkedserver 
    @server = 'ServerAlias',         -- имя-алиас
    @srvproduct = '', 
    @provider = 'SQLNCLI',
    @datasrc = 'localhost';         -- имя реального сервера
GO

