-- Create database (XAMPP / phpMyAdmin): run these in order
CREATE DATABASE IF NOT EXISTS ic_smart_library CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ic_smart_library;

-- CATEGORY
CREATE TABLE IF NOT EXISTS tbl_category (
  category_id    INT PRIMARY KEY AUTO_INCREMENT,
  category_name  VARCHAR(50) NOT NULL,
  UNIQUE KEY uq_category_name (category_name)
);

-- BOOK
CREATE TABLE IF NOT EXISTS tbl_book (
  book_id        INT PRIMARY KEY AUTO_INCREMENT,
  qr_code        VARCHAR(100) NOT NULL,
  title          VARCHAR(150) NOT NULL,
  author         VARCHAR(100),
  category_id    INT NOT NULL,
  publisher      VARCHAR(100),
  year_published YEAR(4),
  status         ENUM('available','borrowed','lost') DEFAULT 'available',
  CONSTRAINT fk_book_category
    FOREIGN KEY (category_id) REFERENCES tbl_category(category_id),
  UNIQUE KEY uq_book_qr (qr_code)
);

-- STUDENT
CREATE TABLE IF NOT EXISTS tbl_student (
  student_id   INT PRIMARY KEY AUTO_INCREMENT,
  fid_code     VARCHAR(100) NOT NULL,
  first_name   VARCHAR(50) NOT NULL,
  last_name    VARCHAR(50),
  year_level   VARCHAR(20),
  contact_no   VARCHAR(20),
  status       ENUM('active','inactive') DEFAULT 'active',
  UNIQUE KEY uq_student_fid (fid_code)
);

-- ROLES
CREATE TABLE IF NOT EXISTS tbl_role (
  role_id    INT PRIMARY KEY AUTO_INCREMENT,
  role_name  VARCHAR(50) NOT NULL,
  UNIQUE KEY uq_role_name (role_name)
);

-- USERS
CREATE TABLE IF NOT EXISTS tbl_user (
  user_id     INT PRIMARY KEY AUTO_INCREMENT,
  role_id     INT NOT NULL,
  first_name  VARCHAR(50) NOT NULL,
  last_name   VARCHAR(50),
  username    VARCHAR(100) NOT NULL,
  password    VARCHAR(255) NOT NULL,
  status      ENUM('pending','active','inactive') DEFAULT 'pending',
  CONSTRAINT fk_user_role
    FOREIGN KEY (role_id) REFERENCES tbl_role(role_id),
  UNIQUE KEY uq_username (username)
);

-- LIBRARY LOGS (RFID in/out)
CREATE TABLE IF NOT EXISTS tbl_library_logs (
  log_id     INT PRIMARY KEY AUTO_INCREMENT,
  student_id INT NOT NULL,
  log_date   DATE NOT NULL,
  log_time_in  DATETIME,
  log_time_out DATETIME,
  status     ENUM('in','out') DEFAULT 'in',
  CONSTRAINT fk_logs_student
    FOREIGN KEY (student_id) REFERENCES tbl_student(student_id)
);

-- BORROW (active + history)
CREATE TABLE IF NOT EXISTS tbl_borrow (
  borrow_id     INT PRIMARY KEY AUTO_INCREMENT,
  student_id    INT NOT NULL,
  book_id       INT NOT NULL,
  borrowed_date DATETIME NOT NULL,
  returned_date DATETIME NULL,
  processed_by  INT NOT NULL,         
  CONSTRAINT fk_borrow_student
    FOREIGN KEY (student_id) REFERENCES tbl_student(student_id),
  CONSTRAINT fk_borrow_book
    FOREIGN KEY (book_id) REFERENCES tbl_book(book_id),
  CONSTRAINT fk_borrow_user
    FOREIGN KEY (processed_by) REFERENCES tbl_user(user_id),
  KEY idx_active_borrow (book_id, returned_date)
);

-- INVENTORY ACTIONS
CREATE TABLE IF NOT EXISTS tbl_inventory_log (
  log_id     INT PRIMARY KEY AUTO_INCREMENT,
  user_id    INT NOT NULL,
  book_id    INT NOT NULL,
  action     VARCHAR(50) NOT NULL,
  action_date DATETIME NOT NULL,
  CONSTRAINT fk_inv_user  FOREIGN KEY (user_id) REFERENCES tbl_user(user_id),
  CONSTRAINT fk_inv_book  FOREIGN KEY (book_id) REFERENCES tbl_book(book_id)
);

-- Seed roles
INSERT IGNORE INTO tbl_role (role_id, role_name) VALUES
  (1,'librarian'),
  (2,'staff');

-- Seed default librarian
INSERT IGNORE INTO tbl_user (user_id, role_id, first_name, last_name, username, password, status)
VALUES (1, 1, 'Head', 'Librarian', 'Admin', SHA2('Smartcecilian',256), 'active');
