USE TradeDB
GO

--------------------------
--- Задание 1 ---
--------------------------

-- Создаём таблицу Table2
CREATE TABLE Table2 (
    pole1 NVARCHAR(100),
    pole2 INT
);
GO

-- Наполняем данными
INSERT INTO Table2 (pole1, pole2) VALUES
('Alpha', 10),
('Bravo', 20),
('Charlie', 30);
GO

SELECT * FROM Table2;

-----------------------
--- Задание 2 ---
-----------------------

-- Таблица для хранения глобального счётчика
IF OBJECT_ID('dbo.Counter') IS NULL
BEGIN
    CREATE TABLE dbo.Counter (
        id INT PRIMARY KEY CHECK (id = 1),
        value INT
    );

    INSERT INTO dbo.Counter (id, value) VALUES (1, 0);
END
GO

-- Функция для инкрементации (аналог inc(mode))
CREATE OR ALTER PROCEDURE dbo.inc
    @mode INT,
    @result INT OUTPUT
AS
BEGIN
    DECLARE @i INT;

    -- Получаем текущее значение
    SELECT @i = value FROM dbo.Counter WHERE id = 1;

    -- Логика ветвления
    IF @mode = 0
        SET @i = 0;
    ELSE
        SET @i = @i + 1;

    -- Сохраняем новое значение
    UPDATE dbo.Counter SET value = @i WHERE id = 1;

    -- Возвращаем значение через OUTPUT
    SET @result = @i;
END
GO

--Использование
----------------
DECLARE @num INT;
-- Первый вызов
EXEC dbo.inc @mode = 1, @result = @num OUTPUT;
SELECT @num AS num, pole1 FROM Table2;

-- Второй вызов
EXEC dbo.inc @mode = 1, @result = @num OUTPUT;
SELECT @num AS num, pole1 FROM Table2;

-- Сброс
EXEC dbo.inc @mode = 0, @result = @num OUTPUT;
SELECT @num AS num, pole1 FROM Table2;


----------------------
--- Задание 3 ---
----------------------

--- Создание 2-ой хранимой процедуры
CREATE OR ALTER PROCEDURE dbo.updTable2
    @pname NVARCHAR(20),
    @pCode INT
AS
BEGIN
    SET NOCOUNT ON;

    -- Обновляем все строки, где pole2 = @pCode, устанавливая pole1 = @pname
    UPDATE Table2
    SET pole1 = @pname
    WHERE pole2 = @pCode;
END
GO

--- Вставляем новую строку
INSERT INTO Table2 VALUES (N'Что-то', 1);
SELECT * FROM Table2;

-- Пример вызова
EXEC dbo.updTable2 @pname = N'Новое значение', @pCode = 1;

-- Проверка результата
SELECT * FROM Table2;
SELECT * FROM Table2 WHERE pole2 = 1;


---------------------
--- Задание 4 ---
---------------------

-- Отмена привилегий на UPDATE и DELETE для таблицы Table1
DENY UPDATE, DELETE ON dbo.Table2 TO [Admin\sarth];

-- Разрешаем выполнение процедуры updTable2
GRANT EXECUTE ON dbo.updTable2 TO [Admin\sarth];

-- Снятие DENY
REVOKE UPDATE, DELETE ON dbo.Table2 FROM [Admin\sarth];



---------------------
--- Задание 4 ---
---------------------

DROP PROCEDURE dbo.inc
DROP PROCEDURE dbo.updTable2

--------------------


-- Попытка изменить данные
UPDATE dbo.Table2
SET pole1 = 0
WHERE pole2 = 10;

SELECT * FROM Table2;

SELECT IS_ROLEMEMBER('db_owner') AS IsDbOwner;
SELECT SUSER_NAME() AS CurrentLogin;