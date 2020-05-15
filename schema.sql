SET NAMES utf8mb4;

-- create table to track which users are in which guilds
CREATE TABLE IF NOT EXISTS guilds (
    id      SMALLINT UNSIGNED   AUTO_INCREMENT PRIMARY KEY,
    guild   VARCHAR (20)        NOT NULL,
    user    VARCHAR (20)        NOT NULL

    UNIQUE INDEX unique_guild_member (guild, user)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE utf8mb4_general_ci;

-- create table to track user keywords
CREATE TABLE IF NOT EXISTS keywords (
    id      SMALLINT UNSIGNED   AUTO_INCREMENT PRIMARY KEY,
    user    VARCHAR (20)        NOT NULL,
    word    VARCHAR (255)       NOT NULL,

    UNIQUE INDEX unique_keyword (user, word)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE utf8mb4_general_ci;

-- stored procedure to get all users and keywords for a given guild
DELIMITER $$

DROP PROCEDURE IF EXISTS get_words;
CREATE PROCEDURE get_words (
    IN guild_id VARCHAR(20)
)
BEGIN
    SELECT kw.user, word FROM keywords kw
    INNER JOIN guilds g ON kw.user = g.user
    WHERE guild = guild_id;
END $$

DELIMITER ;
