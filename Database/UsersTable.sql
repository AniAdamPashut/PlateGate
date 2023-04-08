CREATE TABLE IF NOT EXISTS users (
    idnumber INT,
    fname VARCHAR(20),
    lname VARCHAR(20),
    password VARCHAR(260),
    salt VARCHAR(20),
    company_id VARCHAR(30),
    user_state INT,
    PRIMARY KEY (idnumber),
    CONSTRAINT `FK_company_id` FOREIGN KEY (`company_id`)
    REFERENCES `companies` (`company_id`)
)