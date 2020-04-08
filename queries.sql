/*	Some sample queries for db.sqlite3 */

# Get all distinct artists by frequency of occrence
SELECT DISTINCT artist, COUNT(artist) AS freq
FROM playlists_content GROUP BY artist
ORDER BY COUNT(artist) DESC;

# Get distinct album/artist pairs by frequency of occurrence 
SELECT DISTINCT album, artist, COUNT(album) AS freq
FROM playlists_content GROUP BY album, artist
ORDER BY COUNT(album) DESC;

# Get distinct song/artist/album combinations by frequency of occurence
SELECT DISTINCT song, artist, album, COUNT(song) AS freq
FROM playlists_content GROUP BY song, artist, album
ORDER BY COUNT(song) DESC;

# check lowest playlist ID value
SELECT MIN(playlist_id_id) FROM playlists_content;

# check highest playlist ID value
SELECT MAX(playlist_id_id) FROM playlists_content;

# check lowest DJ ID value
SELECT MIN(dj_id_id) FROM playlists_content;

# check highest DJ ID value
SELECT MAX(dj_id_id) FROM playlists_content;

# Search on specific date
SELECT * FROM playlists_playlist
WHERE start_time LIKE 'YYYY-MM-DD%'; 


# Search within date range
SELECT * FROM playlists_playlist WHERE start_time
BETWEEN 'YYYY-MM-DD HH-mm-SS' AND 'YYYY-MM-DD HH-mm-SS'; 

SELECT DISTINCT genre, COUNT(genre) AS freq
FROM playlists_playlist GROUP BY genre
ORDER BY COUNT(genre) DESC;

# Full outer joins to display content and restrict timeframe
SELECT DISTINCT UPPER(TRIM(playlists_content.artist)) AS Artist,
		COUNT(UPPER(TRIM(playlists_content.artist))) AS Frequency
	FROM playlists_content
		JOIN playlists_playlist
			ON playlists_playlist.playlist_id = playlists_content.playlist_id_id
			AND (playlists_playlist.start_time LIKE "2020-%")
	GROUP by playlists_content.artist, playlists_content.song
	ORDER BY COUNT(playlists_content.artist) DESC;


SELECT DISTINCT UPPER(TRIM(playlists_content.artist)) AS Artist,
		UPPER(TRIM(playlists_content.song)) AS Title,
		COUNT(UPPER(TRIM(playlists_content.song))) AS Frequency
	FROM playlists_content
		JOIN playlists_playlist
			ON playlists_playlist.playlist_id = playlists_content.playlist_id_id
			AND (playlists_playlist.start_time LIKE "2020-%")
	GROUP by playlists_content.artist, playlists_content.song
	ORDER BY COUNT(UPPER(TRIM(playlists_content.song))) DESC;


SELECT DISTINCT UPPER(TRIM(playlists_content.artist)),
		COUNT(UPPER(TRIM(playlists_content.artist))) as freq
	FROM playlists_content
		JOIN playlists_playlist
			ON playlists_content.dj_id_id = playlists_playlist.dj_id
			AND playlists_playlist.dj_name = "Jon Solomon"
	GROUP BY playlists_content.artist, playlists_content.dj_id_id
	ORDER BY COUNT(UPPER(TRIM(artist))) DESC;