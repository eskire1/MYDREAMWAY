-- Создание базы данных для клиентов и заказов
CREATE DATABASE DataBase_Sales;
GO

USE DataBase_Sales;
GO

-- Таблица Клиенты
CREATE TABLE Customers (
    id INT IDENTITY(1,1) PRIMARY KEY,
    first_name NVARCHAR(255) NOT NULL,
    last_name NVARCHAR(255) NOT NULL,
    email NVARCHAR(255) UNIQUE,
    phone NVARCHAR(50),
    address NVARCHAR(MAX)
);

-- Таблица Заказы
CREATE TABLE Orders (
    id INT IDENTITY(1,1) PRIMARY KEY,
    customer_id INT,
    order_date DATETIME,
    total_quantity INT,
    status NVARCHAR(50),
    FOREIGN KEY (customer_id) REFERENCES Customers(id)
);

-- Таблица Элементы_заказа
CREATE TABLE Order_Items (
    id INT IDENTITY(1,1) PRIMARY KEY,
    order_id INT,
    product_id INT, -- ссылка на таблицу Products из другой базы
    quantity INT NOT NULL,
    purchase_price DECIMAL(18, 2) NOT NULL
    -- FOREIGN KEY (product_id) REFERENCES [DataBase_Products].dbo.Products(id)
);

-- Наполнение таблиц
INSERT INTO Customers (first_name, last_name, email, phone, address) VALUES
('Ivan', 'Petrov', 'ivan.petrov@email.com', '+79991234567', 'Moscow, Lenin st., b. 10'),
('Anna', 'Sidorova', 'anna.sidorova@email.com', '+79992345678', 'Saint-Petersburg, Nevskiy av., b. 25'),
('Dmitriy', 'Kozlov', 'dmitry.kozlov@email.com', '+79993456789', 'Novosibirsk, Krasnaia st., b. 5'),
('Olga', 'Morozova', 'olga.morozova@email.com', '+79994567890', 'Ekaterinburg, Chapaev st., b. 12'),
('Aleksei', 'Smirnov', 'alexey.smirnov@email.com', '+79995678901', 'Kazan, Tverskaya st., b. 8'),
('Maria', 'Fedorova', 'maria.fedorova@email.com', '+79996789012', 'Nizhniy Novgorod, Gogolya st., b. 14'),
('Sergei', 'Vasiliev', 'sergey.vasilyev@email.com', '+79997890123', 'Chelyabinsk, Pushkin st., b. 7'),
('Elena', 'Mihailova', 'elena.mikhailova@email.com', '+79998901234', 'Rostov-Na-Donu, Sovetskaya st., b. 6'),
('Nikolai', 'Popova', 'nikolay.popov@email.com', '+79999012345', 'Omsk, Lomonosova av., b. 3'),
('Tatyana', 'Grigorieva', 'tatyana.grigorieva@email.com', '+79990123456', 'Voronezh, Kirova st., b. 9');

INSERT INTO Orders (customer_id, order_date, total_quantity, status) VALUES
(1, '2025-02-10 14:30:00', 2, N'In processing'),
(2, '2025-02-11 10:15:00', 1, N'Sent'),
(3, '2025-02-12 16:45:00', 3, N'Delivered'),
(4, '2025-02-13 09:30:00', 1, N'Cancelled'),
(5, '2025-02-14 12:00:00', 2, N'In processing'),
(6, '2025-02-15 18:20:00', 1, N'Delivered'),
(7, '2025-02-16 08:40:00', 4, N'In processing'),
(8, '2025-02-17 21:10:00', 2, N'Sent'),
(9, '2025-02-18 14:00:00', 3, N'Delivered'),
(10, '2025-02-19 11:25:00', 1, N'Cancelled');

INSERT INTO Order_Items (order_id, product_id, quantity, purchase_price) VALUES
(1, 1, 1, 999.99),
(1, 3, 1, 199.99),
(2, 3, 1, 199.99),
(3, 2, 2, 799.99),
(3, 5, 1, 599.99),
(4, 5, 1, 599.99),
(5, 7, 2, 299.99),
(6, 4, 1, 249.99),
(7, 6, 2, 349.99),
(7, 1, 2, 999.99),
(8, 9, 1, 499.99),
(8, 10, 1, 399.99),
(9, 10, 1, 399.99),
(9, 12, 2, 59.99),
(9, 13, 1, 149.99),
(10, 8, 1, 899.99);
