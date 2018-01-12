CREATE SCHEMA IF NOT EXISTS coordinates;

use coordinates;

CREATE TABLE IF NOT EXISTS `coordinates`.`users` (
  `user_id` INT(11) NOT NULL AUTO_INCREMENT,
  `email` VARCHAR(255) NOT NULL,
  `firstname` VARCHAR(25) NOT NULL,
  `lastname` VARCHAR(25) NOT NULL,
  `password` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`user_id`),
  UNIQUE INDEX `email` (`email` ASC))
ENGINE = InnoDB
AUTO_INCREMENT = 4;

CREATE TABLE IF NOT EXISTS coordinates.locations (
	user VARCHAR(25) NOT NULL,
	locationname VARCHAR(25) NOT NULL,
	city VARCHAR(25) NOT NULL,
	street VARCHAR(25) NOT NULL,
	house_num VARCHAR(25) NOT NULL,
	zipcode VARCHAR(25) NOT NULL
);


