-- Создание базы данных
CREATE DATABASE DataBase_DropShipping;
GO

-- Использование созданной базы данных
USE DataBase_DropShipping;
GO

-- Создание таблицы Поставщики
CREATE TABLE Suppliers (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(255) NOT NULL,
    contact_info NVARCHAR(MAX),
    reliability_rating INT,
    delivery_time NVARCHAR(255)
);

-- Создание таблицы Товары
CREATE TABLE Products (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(255) NOT NULL,
    description NVARCHAR(MAX),
    price DECIMAL(18, 2) NOT NULL,
    stock_quantity INT NOT NULL,
    supplier_id INT,
    category NVARCHAR(255),
    FOREIGN KEY (supplier_id) REFERENCES Suppliers(id)
);

-- Создание таблицы Клиенты
CREATE TABLE Customers (
    id INT IDENTITY(1,1) PRIMARY KEY,
    first_name NVARCHAR(255) NOT NULL,
    last_name NVARCHAR(255) NOT NULL,
    email NVARCHAR(255) UNIQUE,
    phone NVARCHAR(50),
    address NVARCHAR(MAX)
);

-- Создание таблицы Заказы
CREATE TABLE Orders (
    id INT IDENTITY(1,1) PRIMARY KEY,
    customer_id INT,
    order_date DATETIME,
    total_quantity INT,
    status NVARCHAR(50),
    FOREIGN KEY (customer_id) REFERENCES Customers(id)
);

-- Создание таблицы Элементы_заказа
CREATE TABLE Order_Items (
    id INT IDENTITY(1,1) PRIMARY KEY,
    order_id INT,
    product_id INT,
    quantity INT NOT NULL,
    purchase_price DECIMAL(18, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES Orders(id),
    FOREIGN KEY (product_id) REFERENCES Products(id)
);

-- Заполнение таблицы Поставщики
INSERT INTO Suppliers (name, contact_info, reliability_rating, delivery_time) VALUES
('Trading Company "Alpha"', 'sales@alpha.com', 5, '1 week'),
('Supplier "Beta Trade"', 'info@beta-trade.com', 4, '2 weeks'),
('Company "Range of Products"', 'contact@gamma-products.com', 3, '3 weeks'),
('Distributor "Delta Element"', 'support@delta-element.com', 5, '1 week'),
('Trade Net "Europe"', 'sales@europa.com', 4, '2 weeks'),
('Company "Zeta Technologies"', 'info@zeta-tech.com', 2, '4 weeks'),
('Supplier "Eta Systems"', 'contact@eta-systems.com', 3, '3 weeks'),
('Trade Company "Theta Logistic"', 'support@theta-logistics.com', 5, '1 week'),
('Company "Iota Invest"', 'sales@iota-invest.com', 4, '2 weeks'),
('Supplier "Kappa Group"', 'info@kappa-group.com', 2, '5 weeks');

-- Заполнение таблицы Товары
INSERT INTO Products (name, description, price, stock_quantity, supplier_id, category) VALUES
('Smartphone "Galaxy Z"', 'A modern smartphone with a flexible screen and high performance.', 999.99, 50, 1, 'Electronics'),
('Laptop "ProBook 450"', 'Powerful laptop for work and study with long battery life.', 799.99, 30, 2, 'Computers'),
('Headphones "SoundMax"', 'Wireless earbuds with active noise cancellation and long runtime.', 199.99, 20, 1, 'Audio equipment'),
('Smart Watch "FitWatch"', 'Smartwatch with activity tracking and health monitoring.', 249.99, 10, 3, 'Accessories'),
('TV "UltraHD 55"', '4K TV with HDR support.', 599.99, 15, 4, 'Household appliances'),
('Coffee machine "CoffeeMaster"', 'Automatic coffee machine with cappuccino function.', 349.99, 5, 5, 'Kitchen appliances'),
('Vacuum cleaner "CleanPro"', 'Powerful vacuum cleaner with wet mopping function.', 299.99, 25, 6, 'Household appliances'),
('Fridge "CoolTech 3000"', 'Energy-saving refrigerator with large volume.', 899.99, 8, 7, 'Household appliances'),
('Camera "PhotoPro 2000"', 'High-resolution digital camera with 4K capability.', 499.99, 12, 8, 'Photo and Video'),
('Game Console "GameBox X"', 'Modern gaming console with VR and online gaming support.', 399.99, 3, 9, 'Games and entertainment'),
('Typeface "GameSound"', 'Gaming headset with surround sound and microphone.', 89.99, 0, 10, 'Audio equipment'),
('Electrical Toothbrush "CleanBrush"', 'Electric brush with multiple cleaning modes.', 59.99, 20, 1, 'Cosmetics and health'),
('Blender "SmoothMix 500"', 'Powerful blender with multiple speeds and ice crushing function.', 149.99, 18, 2, 'Kitchen appliances'),
('Humidifier "AirMoist"', 'Humidifier with aromatherapy function and timer.', 79.99, 10, 3, 'Climate technology'),
('Hairdryer "QuickDry 3000"', 'Powerful hairdryer with multiple heat settings and styling attachments.', 49.99, 15, 6, 'Household appliances');

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

DROP DATABASE DataBase_DropShipping;

SELECT * FROM sys.dm_exec_sessions;

SELECT DB_ID('DataBase_DropShipping') AS DatabaseID;

USE master
ALTER DATABASE DataBase_DropShipping SET SINGLE_USER WITH ROLLBACK IMMEDIATE;

SELECT name FROM sys.databases;

SELECT name, state_desc FROM sys.databases WHERE name = 'DataBase_DropShipping';

USE DataBase_DropShipping
GO
SELECT * FROM Suppliers;