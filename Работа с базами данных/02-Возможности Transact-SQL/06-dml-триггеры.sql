USE DataBase_DropShipping
GO

--- Триггер AfterInsert (После вставки)
CREATE TRIGGER trg_AfterInsert_Orders
ON Orders
AFTER INSERT
AS
BEGIN
    PRINT 'New order inserted with ID(s):'
    SELECT id, customer_id, order_date FROM inserted;
END;
GO


--- Триггер AfterUpdate (После обновления)
CREATE TRIGGER trg_AfterUpdate_Products
ON Products
AFTER UPDATE
AS
BEGIN
    IF UPDATE(price)
    BEGIN
        PRINT 'Product price has been updated:'
        SELECT name, price FROM inserted;
    END;
END;
GO


--- Триггер AfterDelete (После удаления)
CREATE TRIGGER trg_AfterDelete_Customers
ON Customers
AFTER DELETE
AS
BEGIN
    PRINT 'Customer deleted:'
    SELECT id, first_name, last_name FROM deleted;
END;
GO


--- Триггер InsteadOfDelete (Вместо удаления)
CREATE TRIGGER trg_InsteadOfDelete_Suppliers
ON Suppliers
INSTEAD OF DELETE
AS
BEGIN
    IF EXISTS (SELECT * FROM deleted WHERE reliability_rating >= 4)
    BEGIN
        RAISERROR('Reliable suppliers (rating >= 4) cannot be deleted.', 16, 1);
        ROLLBACK TRANSACTION;
    END
    ELSE
    BEGIN
        DELETE FROM Suppliers WHERE id IN (SELECT id FROM deleted);
    END
END;
GO



--- Проверка работы триггеров
-- AFTER INSERT
INSERT INTO Orders (customer_id, order_date, total_quantity, status)
VALUES (1, GETDATE(), 2, 'In processing');
--- (Откат вставки)
DELETE FROM Orders WHERE id = 11;
SELECT * FROM Orders;

-- AFTER UPDATE
UPDATE Products SET price = price + 10 WHERE id = 1;
--- (Откат обновления цены продукта в таблице Products)
UPDATE Products SET price = price - 10 WHERE id = 1;

-- AFTER DELETE
--- (Сначала вставка)
INSERT INTO Customers (first_name, last_name, email, phone, address)
VALUES ('Arthur', 'Petrov', 's.arthur995946@gmail.com', '+79378367114', 'Chetaeva st., b. 8');
--- (Проверка вставки)
SELECT * FROM Customers;
--- (Теперь удаление)
DELETE FROM Customers WHERE id = 11;
SELECT * FROM Customers;

-- INSTEAD OF DELETE
--- (Сначала просмотр таблицы)
SELECT * FROM Suppliers;
--- (Теперь удаление)
DELETE FROM Suppliers WHERE id = 1;  -- reliable supplier → ошибка
--- (Вставка покупателя с low reliability_rating)
INSERT INTO Suppliers (name, contact_info, reliability_rating, delivery_time)
VALUES ('NotCoolStore', 'notcoolstore@gmail.com', '3', '2 weeks');
--- (Проверка вставки)
SELECT * FROM Suppliers;
--- (Теперь удаление)
DELETE FROM Suppliers WHERE id = 13;  -- low rating → удалится


--- (На всякий)
UPDATE Suppliers SET reliability_rating = 3 WHERE id = 13;