-- sql migrations

ALTER TABLE profiles
ADD COLUMN avatar VARCHAR(300) NULL;

ALTER TABLE profiles
ADD COLUMN bio VARCHAR(600) NULL;
