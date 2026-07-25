USE DataBase_DropShipping
GO

-- Получить весь XML узел <features> с помощью метода query
SELECT ProductInfo.query('/product/features') AS FeaturesXML
FROM Products
WHERE id = 1;

SELECT ProductInfo.query('
	for $f in /product/features 
	return $f  
') AS FeaturesXML
FROM Products
WHERE id = 1;


-- Извлечь значение узла <manufacturer> с помощью метода value
SELECT ProductInfo.value('(/product/manufacturer)[1]', 'NVARCHAR(100)') AS Manufacturer
FROM Products
WHERE id = 1;

-- Проверить, существует ли узел <warranty> с помощью метода exist
SELECT 
    CASE 
        WHEN ProductInfo.exist('/product/warranty') = 1 THEN N'Есть гарантия'
        ELSE N'Нет гарантии'
    END AS WarrantyExists
FROM Products
WHERE id = 1;



-- Добавить новый элемент <color> внутрь <product> с помощью modify
UPDATE Products
SET ProductInfo.modify('insert <color>Black</color> into (/product)[1]')
WHERE id = 1;

-- Проверка
SELECT ProductInfo
FROM Products
WHERE id = 1;

-- Изменить значение <warranty> на "2 years" с помощью modify
UPDATE Products
SET ProductInfo.modify('replace value of (/product/warranty/text())[1] with "2 years"')
WHERE id = 1;

-- Извлечь каждый элемент <feature> как отдельную строку с помощью nodes
SELECT 
    T.Item.value('.', 'NVARCHAR(100)') AS Feature
FROM Products
CROSS APPLY ProductInfo.nodes('/product/features/feature') AS T(Item)
WHERE id = 1;
