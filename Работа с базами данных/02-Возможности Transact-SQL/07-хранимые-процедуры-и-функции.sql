USE DataBase_DropShipping
GO

--- Хранимые процедуры без параметров ---
--- Процедура для вывода списка товаров с низким запасов (менее 10 единиц)
CREATE PROCEDURE sp_GetLowStockProducts
AS
BEGIN
    SELECT p.name AS ProductName, p.stock_quantity, s.name AS SupplierName
    FROM Products p
    JOIN Suppliers s ON p.supplier_id = s.id
    WHERE p.stock_quantity < 10
    ORDER BY p.stock_quantity;
END;
GO

-- Проверка работы процедуры
EXEC sp_GetLowStockProducts;
GO

--- Хранимые процедуры с входными параметрами ---
--- Процедура для добавления нового заказа
CREATE PROCEDURE sp_AddNewOrder
    @customer_id INT,
    @product_id INT,
    @quantity INT
AS
BEGIN
    DECLARE @product_price DECIMAL(18,2);
    DECLARE @order_id INT;
    
    -- Получаем цену товара
    SELECT @product_price = price FROM Products WHERE id = @product_id;
    
    -- Создаем запись о заказе
    INSERT INTO Orders (customer_id, order_date, total_quantity, status)
    VALUES (@customer_id, GETDATE(), @quantity, 'In processing');
    
    SET @order_id = SCOPE_IDENTITY();
    
    -- Добавляем товар в заказ
    INSERT INTO Order_Items (order_id, product_id, quantity, purchase_price)
    VALUES (@order_id, @product_id, @quantity, @product_price);
    
    -- Обновляем количество товара на складе
    UPDATE Products
    SET stock_quantity = stock_quantity - @quantity
    WHERE id = @product_id;
    
    SELECT @order_id AS NewOrderId;
END;
GO

-- Проверка работы процедуры
EXEC sp_AddNewOrder @customer_id = 1, @product_id = 2, @quantity = 1;
GO


--- Хранимые процедуры  с выходными параметрами ---
--- Процедура для расчета общей стоимости заказов клиента
CREATE PROCEDURE sp_GetCustomerTotalSpent
    @customer_id INT,
    @total_spent DECIMAL(18,2) OUTPUT
AS
BEGIN
    SELECT @total_spent = SUM(oi.quantity * oi.purchase_price)
    FROM Orders o
    JOIN Order_Items oi ON o.id = oi.order_id
    WHERE o.customer_id = @customer_id;
END;
GO

-- Проверка работы процедуры
DECLARE @total DECIMAL(18,2);
EXEC sp_GetCustomerTotalSpent @customer_id = 1, @total_spent = @total OUTPUT;
SELECT @total AS TotalSpent;
GO


--- Функции, возвращающие скалярное значение ---
--- Функция для расчета средней стоимости заказа
CREATE FUNCTION fn_GetAverageOrderValue()
RETURNS DECIMAL(18,2)
AS
BEGIN
    DECLARE @avg_value DECIMAL(18,2);
    
    SELECT @avg_value = AVG(oi.quantity * oi.purchase_price)
    FROM Order_Items oi;
    
    RETURN @avg_value;
END;
GO

-- Проверка работы функции
SELECT dbo.fn_GetAverageOrderValue() AS AverageOrderValue;
GO


--- Функции, возвращающие табличные значения ---
--- Функция для получения товаров по категории
CREATE FUNCTION fn_GetProductsByCategory(@category NVARCHAR(255))
RETURNS TABLE
AS
RETURN
    SELECT p.name, p.price, p.stock_quantity, s.name AS supplier_name
    FROM Products p
    JOIN Suppliers s ON p.supplier_id = s.id
    WHERE p.category = @category;
GO

-- Проверка работы функции
SELECT * FROM dbo.fn_GetProductsByCategory('Household appliances');
GO


--- Процедура с использованием временных таблиц ---
--- Процедура для анализа продаж по поставщикам
CREATE PROCEDURE sp_AnalyzeSupplierSales
AS
BEGIN
    -- Создаем временную таблицу
    CREATE TABLE #SupplierSales (
        SupplierName NVARCHAR(255),
        TotalSales DECIMAL(18,2),
        ProductCount INT,
        AvgProductPrice DECIMAL(18,2)
    );
    
    -- Заполняем временную таблицу данными
    INSERT INTO #SupplierSales
    SELECT 
        s.name AS SupplierName,
        SUM(oi.quantity * oi.purchase_price) AS TotalSales,
        COUNT(DISTINCT oi.product_id) AS ProductCount,
        AVG(p.price) AS AvgProductPrice
    FROM Order_Items oi
    JOIN Products p ON oi.product_id = p.id
    JOIN Suppliers s ON p.supplier_id = s.id
    GROUP BY s.name;
    
    -- Выводим результаты
    SELECT * FROM #SupplierSales ORDER BY TotalSales DESC;
    
    -- Удаляем временную таблицу
    DROP TABLE #SupplierSales;
END;
GO

-- Проверка работы процедуры
EXEC sp_AnalyzeSupplierSales;
GO


--- Процедура с обработкой ошибок ---
--- Процедура для обновления цены товара с проверкой
CREATE PROCEDURE sp_UpdateProductPrice
    @product_id INT,
    @new_price DECIMAL(18,2)
AS
BEGIN
    BEGIN TRY
        IF NOT EXISTS (SELECT 1 FROM Products WHERE id = @product_id)
            RAISERROR('Product with ID %d does not exist', 16, 1, @product_id);
        
        IF @new_price <= 0
            RAISERROR('Price must be greater than zero', 16, 1);
        
        UPDATE Products
        SET price = @new_price
        WHERE id = @product_id;
        
        PRINT 'Price updated successfully';
    END TRY
    BEGIN CATCH
        PRINT 'Error: ' + ERROR_MESSAGE();
    END CATCH
END;
GO

-- Проверка работы процедуры (с ошибкой)
EXEC sp_UpdateProductPrice @product_id = 999, @new_price = 100.00;
GO

-- Проверка работы процедуры (успешно)
EXEC sp_UpdateProductPrice @product_id = 1, @new_price = 1099.99;
GO


--- Функция с условной логикой ---
--- Функция для классификации клиентов по объему покупок
CREATE FUNCTION fn_ClassifyCustomer(@customer_id INT)
RETURNS NVARCHAR(50)
AS
BEGIN
    DECLARE @total_spent DECIMAL(18,2);
    DECLARE @classification NVARCHAR(50);
    
    SELECT @total_spent = SUM(oi.quantity * oi.purchase_price)
    FROM Orders o
    JOIN Order_Items oi ON o.id = oi.order_id
    WHERE o.customer_id = @customer_id;
    
    IF @total_spent IS NULL
        SET @classification = 'New customer';
    ELSE IF @total_spent < 500
        SET @classification = 'Regular customer';
    ELSE IF @total_spent < 2000
        SET @classification = 'Silver customer';
    ELSE
        SET @classification = 'Gold customer';
    
    RETURN @classification;
END;
GO

-- Проверка работы функции
SELECT 
    c.first_name + ' ' + c.last_name AS CustomerName,
    dbo.fn_ClassifyCustomer(c.id) AS CustomerClass
FROM Customers c;
GO