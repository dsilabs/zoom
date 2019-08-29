/** 
*	Create tables used by the database bucket backend. This setup is performed
*	by application logic.
**/

CREATE TABLE IF NOT EXISTS buckets (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	name VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS bucket_blobs (
	id CHAR(32) NOT NULL,
	bucket_id INT UNSIGNED NOT NULL REFERENCES buckets(id),
	data LONGBLOB NOT NULL
)