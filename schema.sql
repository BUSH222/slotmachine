CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(32),
    password VARCHAR(32),
    balance INTEGER DEFAULT 3000);
DO $$
BEGIN
	IF NOT EXISTS (SELECT 1 FROM users) THEN
    INSERT INTO users (id, name, password, balance) VALUES
    (1, 'a', '12345678', '2500'),
    (2, 'bob', 'sec', '4000');
END IF;
END $$;