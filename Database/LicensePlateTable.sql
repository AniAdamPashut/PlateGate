CREATE TABLE IF NOT EXISTS licenseplates (
    platenumber INT,
    ownerid INT,
    PRIMARY KEY (platenumber),
    CONSTRAINT FK_idnumber FOREIGN KEY (ownerid)
    REFERENCES users(idnumber)

)