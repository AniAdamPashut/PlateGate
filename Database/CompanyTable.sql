CREATE TABLE IF NOT EXISTS companies (
    company_id INT,
    company_name VARCHAR(30),
    manager_id INT,
    PRIMARY KEY  (company_id),
    CONSTRAINT FK_manager_id FOREIGN KEY (manager_id)
    REFERENCES users(id_number)
)