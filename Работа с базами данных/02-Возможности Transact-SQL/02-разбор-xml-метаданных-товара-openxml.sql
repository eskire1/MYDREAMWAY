-- Добавим столбец XML в таблицу Products
USE DataBase_DropShipping
GO
ALTER TABLE Products ADD ProductInfo XML;

-- Заполним столбец ProductInfo для одного товара
UPDATE Products SET ProductInfo = 
N'<product>
	<manufacturer>ACME</manufacturer>
	<warranty>1 year</warranty>
	<features>
		<feature>Bluetooth</feature>
		<feature>WiFi</feature>
	</features>
</product>'
WHERE id = 1;

-- Объявим переменные и загрузим XML в память
DECLARE @idoc INT, @xml XML;
SELECT @xml = ProductInfo FROM Products WHERE id = 1;
EXEC sp_xml_preparedocument @idoc OUTPUT, @xml;

-- Извлечем производителя и гарантию (manufacturer и warranty)
SELECT * FROM OPENXML(@idoc, '/product', 2)
WITH (
    manufacturer NVARCHAR(100) 'manufacturer',
    warranty NVARCHAR(100) 'warranty'
);

-- Извлечем список features (Bluetooth, WiFi)
SELECT * FROM OPENXML(@idoc, '/product/features/feature', 2)
WITH (
    feature NVARCHAR(100) '.'
);

-- Освобождаем ресурсы
EXEC sp_xml_removedocument @idoc;


SELECT * FROM Products;