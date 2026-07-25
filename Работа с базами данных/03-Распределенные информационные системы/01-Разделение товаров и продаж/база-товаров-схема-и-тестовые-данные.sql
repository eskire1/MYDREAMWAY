-- Создание базы данных для поставщиков и товаров
CREATE DATABASE DataBase_Products;
GO

USE DataBase_Products;
GO

-- Таблица Поставщики
CREATE TABLE Suppliers (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(255) NOT NULL,
    contact_info NVARCHAR(MAX),
    reliability_rating INT,
    delivery_time NVARCHAR(255)
);

-- Таблица Товары
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

-- Наполнение таблицы Suppliers
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

-- Наполнение таблицы Products
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
