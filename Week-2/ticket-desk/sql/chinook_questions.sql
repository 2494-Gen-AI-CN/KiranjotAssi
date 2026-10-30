-- Active: 1793208308507@@127.0.0.1@3306@Chinook

USE Chinook;

-- ============================================================
-- Part A: one table (SELECT, WHERE, ORDER BY, LIMIT)
-- ============================================================

-- Q01. Every genre name, A to Z.
SELECT Name FROM Genre
ORDER BY Name ASC;


-- Q02. The customers who live in Canada: first name, last name and city, sorted by city.
SELECT FirstName, LastName, City FROM Customer WHERE Country = 'Canada' ORDER BY City; 


-- Q03. The ten longest tracks that run over 10 minutes: name and length in minutes
--      (one decimal), longest first.

SELECT Name, ROUND(Milliseconds / 60000.0, 1) AS Length 
FROM Track 
WHERE (Milliseconds / 60000.0) > 10.0
ORDER BY Milliseconds ASC
LIMIT 10;

-- Q04. Invoices from 2025 whose total is above 10: invoice id, date and total, highest total first.
SELECT InvoiceId, EXTRACT(YEAR FROM InvoiceDate) AS Year, Total FROM Invoice
WHERE Total > 10
ORDER by Total DESC;

-- Q05. Albums whose title contains the word Live, A to Z.
SELECT Title FROM Album 
WHERE Title LIKE "%Live%"
ORDER BY Title ASC;

-- Q06. Customers in the USA or Canada who gave a company name: the full name in one
--      column called customer, the company and the country, sorted by company.
SELECT  CONCAT(FirstName, ' ', LastName) as customer, Company, Country
FROM Customer
WHERE Country IN ('Canada', 'USA') AND Company IS NOT NULL
ORDER BY Company;

-- ============================================================
-- Part B: aggregates (GROUP BY, HAVING)
-- ============================================================

-- Q07. One row about the whole Track table: how many tracks, and the shortest, longest
--      and average length in minutes (two decimals).
SELECT COUNT(TrackID) AS Count, MIN(ROUND(Milliseconds / 60000.0, 2)) AS Shortest, MAX(ROUND(Milliseconds / 60000.0, 2)) AS Longest, 
AVG(ROUND(Milliseconds / 60000.0, 2)) AS Average
FROM Track

-- Q08. How many customers live in each country, most customers first, then country A to Z.
SELECT Country, COUNT(CustomerId) AS Population FROM Customer
GROUP BY Country
ORDER BY Population DESC, Country ASC;

-- Q09. Total billed per billing country (two decimals), only the countries billed more
--      than 100 in all, highest first.
SELECT BillingCountry, ROUND(SUM(Total)) AS total FROM Invoice
GROUP BY BillingCountry
HAVING total > 100
ORDER BY total DESC;

-- Q10. Albums with more than 25 tracks: the album id and its track count, most tracks first.
--      (Only the id for now. Q13 adds the title.)
SELECT DISTINCT(AlbumId), COUNT(TrackId) AS count FROM Track
GROUP BY AlbumId
HAVING count > 25
ORDER BY count DESC;

-- Q11. Per customer id: how many invoices and how much they spent in all (two decimals),
--      only the customers who spent more than 45, biggest spender first.
SELECT CustomerId, COUNT(InvoiceId) as InvoiceCount, ROUND(SUM(Total), 2) as TotalSpent FROM Invoice
GROUP BY CustomerId
HAVING TotalSpent > 45
ORDER BY TotalSpent DESC;

-- ============================================================
-- Part C: joins
-- ============================================================

-- Q12. Every album title with the name of its artist, sorted by artist then title.
SELECT a.Title, ar.Name 
FROM Album as a
JOIN Artist AS ar
ON a.ArtistId = ar.ArtistId
ORDER BY ar.Name, a.Title;

-- Q13. Q10 again, with the album title and the artist name instead of the id.
-- Albums with more than 25 tracks: the album id and its track count, most tracks first.
--      (Only the id for now. Q13 adds the title.)
SELECT Album.Title, Artist.Name, Album.AlbumId, COUNT(Track.TrackId) AS SongCount
FROM Album 
JOIN Artist ON Album.ArtistId = Artist.ArtistId
JOIN Track ON Track.AlbumId = Album.AlbumId
GROUP BY Album.AlbumId, Album.Title, Artist.Name
HAVING SongCount > 25
ORDER BY SongCount DESC;

-- Q14. Every track by Iron Maiden: album title and track name, sorted by album then track.
SELECT Album.Title, Track.Name
FROM Track
JOIN Album ON Track.AlbumId = Album.AlbumId
JOIN Artist ON Artist.ArtistId = Album.ArtistId
WHERE Artist.Name = 'Iron Maiden'
ORDER BY Album.AlbumId, Track.TrackId;

-- Q15. Every Jazz track: track name, album title and media type name, sorted by album then track.


-- Q16. Each customer with the employee who supports them: customer full name and rep full
--      name (one column each), sorted by rep then customer.


-- Q17. Every employee and how many customers they support, including the employees who
--      support nobody (they show 0), most customers first, then last name.


-- Q18. The five genres that earned the most: genre name and revenue (the sum of unit price
--      times quantity over every invoice line, two decimals), highest first.


-- Q19. How many tracks have never been sold? One number, found with a LEFT JOIN
--      from Track to InvoiceLine and a test for NULL.


-- ============================================================
-- Part D: subqueries
-- ============================================================

-- Q20. Every track on the album called Let There Be Rock: name and length in milliseconds,
--      in track order (by TrackId). Use a subquery for the album id, not a join.


-- Q21. Tracks that cost more than the average track price: name and unit price,
--      the first ten alphabetically.


-- Q22. Artists with no album at all, A to Z. Write it with NOT IN and a subquery.


-- Q22b. Same question, written as a LEFT JOIN. Same rows?


-- Q23. The invoice with the highest total: invoice id, customer id, date and total.


-- Q24. Customers who bought at least one Metal track: full name and country, sorted by
--      name. The list of customer ids comes from a subquery that joins Invoice,
--      InvoiceLine, Track and Genre.


-- ============================================================
-- Stretch (for home, or if you finish early)
-- ============================================================

-- Q25. Each employee with the name of the person they report to. The general manager
--      reports to nobody and must still appear, with NULL. Hint: join Employee to
--      itself under two aliases.


-- Q26. Customers whose total spend is above the average customer's total spend: full name
--      and what they spent (two decimals), biggest first. The average of the per-customer
--      totals needs a subquery in FROM (the notes page calls it a derived table).