USE DataBase_DropShipping
GO

--- 1. §²§Ö§Ø§Ú§Þ RAW
-- §£§í§Ó§à§Õ§Ú§ä XML, §Ô§Õ§Ö §Ü§Ñ§Ø§Õ§Ñ§ñ §ã§ä§â§à§Ü§Ñ ¡ª §ï§ä§à §ï§Ý§Ö§Þ§Ö§ß§ä <Product> §ã §Ñ§ä§â§Ú§Ò§å§ä§Ñ§Þ§Ú.
SELECT id, name, price 
FROM Products 
FOR XML RAW('Product'), ROOT('Products');

-- §£§í§Ó§à§Õ§Ú§ä XML, §Ô§Õ§Ö §Ü§Ñ§Ø§Õ§à§Ö §á§à§Ý§Ö §á§â§Ö§Õ§ã§ä§Ñ§Ó§Ý§ñ§Ö§ä§ã§ñ §Ü§Ñ§Ü §ï§Ý§Ö§Þ§Ö§ß§ä.
SELECT id, first_name, last_name 
FROM Customers 
FOR XML RAW, ELEMENTS, ROOT('Customers');


--- 2. §²§Ö§Ø§Ú§Þ AUTO
-- §¶§à§â§Þ§Ú§â§å§Ö§ä §Ú§Ö§â§Ñ§â§ç§Ú§ð, §Ô§Õ§Ö <Customer> §ã§à§Õ§Ö§â§Ø§Ú§ä §Ó§Ý§à§Ø§Ö§ß§ß§í§Ö <Order>.
SELECT c.id, c.first_name, c.last_name, o.id AS order_id, o.order_date 
FROM Customers c 
JOIN Orders o ON c.id = o.customer_id 
ORDER BY c.id 
FOR XML AUTO, ELEMENTS, ROOT('CustomerOrders');


--- 3. §²§Ö§Ø§Ú§Þ PATH
-- §³§à§Ù§Õ§Ñ§×§ä XML §ã §Ñ§ä§â§Ú§Ò§å§ä§Ñ§Þ§Ú §Ú §Ó§Ý§à§Ø§Ö§ß§ß§í§Þ§Ú §ï§Ý§Ö§Þ§Ö§ß§ä§Ñ§Þ§Ú.
SELECT 
    c.id AS "@CustomerID",
    c.first_name AS "Name/First",
    c.last_name AS "Name/Last",
    o.id AS "Orders/Order/@OrderID",
    o.order_date AS "Orders/Order/Date"
FROM Customers c
JOIN Orders o ON c.id = o.customer_id
FOR XML PATH('Customer'), ROOT('Customers');


--- 4. §²§Ö§Ø§Ú§Þ EXPLICIT
-- §¤§Ö§ß§Ö§â§Ú§â§å§Ö§ä XML §ã §ä§à§é§ß§í§Þ §Ü§à§ß§ä§â§à§Ý§Ö§Þ §ã§ä§â§å§Ü§ä§å§â§í.
SELECT 
    1 AS Tag, NULL AS Parent, 
    c.id AS [Customer!1!CustomerID], 
    c.first_name AS [Customer!1!FirstName], 
    c.last_name AS [Customer!1!LastName], 
    NULL AS [Order!2!OrderID], 
    NULL AS [Order!2!Date]
FROM Customers c
UNION ALL
SELECT 
    2 AS Tag, 1 AS Parent, 
    o.customer_id, NULL, NULL, 
    o.id, o.order_date
FROM Orders o
ORDER BY [Customer!1!CustomerID], [Order!2!OrderID]
FOR XML EXPLICIT;
