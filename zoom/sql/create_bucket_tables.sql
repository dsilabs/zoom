/** 
*	Create tables used by the database bucket backend. This setup is performed
*	by application logic.
**/

CREATE TABLE IF NOT EXISTS buckets (
	id UNSIGNED INT PRIMARY KEY AUTO_INCREMENT,
	name VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS bucket_blobs (
	id VARCHAR(255) NOT NULL,
	bucket_id UNSIGNED INT NOT NULL REFERENCES buckets(id),
	data LONGBLOB NOT NULL
);
