-- ================================================
-- CampusConnect Database Schema
-- Oracle SQL (Autonomous Database)
-- CSC270: Database Systems - I | Spring 2026
-- Team: Muhim Akhtar, Izhan Shah, Sohail Wazir
-- ================================================

-- Drop tables in correct order (child first)
DROP TABLE ITEM_REPORTS      CASCADE CONSTRAINTS;
DROP TABLE HOSTEL_BOOKMARKS  CASCADE CONSTRAINTS;
DROP TABLE RIDE_PASSENGERS   CASCADE CONSTRAINTS;
DROP TABLE NOTIFICATIONS     CASCADE CONSTRAINTS;
DROP TABLE REVIEWS           CASCADE CONSTRAINTS;
DROP TABLE MESSAGES          CASCADE CONSTRAINTS;
DROP TABLE MARKETPLACE       CASCADE CONSTRAINTS;
DROP TABLE HOSTELS           CASCADE CONSTRAINTS;
DROP TABLE RIDE_REQUESTS     CASCADE CONSTRAINTS;
DROP TABLE RIDES             CASCADE CONSTRAINTS;
DROP TABLE USER_PROFILES     CASCADE CONSTRAINTS;
DROP TABLE USERS             CASCADE CONSTRAINTS;

-- ================================================
-- TABLE 1: USERS
-- ================================================
CREATE TABLE USERS (
    user_id    NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    full_name  VARCHAR2(100) NOT NULL,
    email      VARCHAR2(100) NOT NULL UNIQUE,
    password   VARCHAR2(255) NOT NULL,
    university VARCHAR2(100) DEFAULT 'COMSATS University Islamabad',
    created_at DATE DEFAULT SYSDATE
);

-- ================================================
-- TABLE 2: USER_PROFILES
-- ================================================
CREATE TABLE USER_PROFILES (
    profile_id  NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id     NUMBER NOT NULL UNIQUE,
    department  VARCHAR2(100),
    semester    VARCHAR2(20),
    roll_no     VARCHAR2(30),
    bio         VARCHAR2(300),
    phone       VARCHAR2(20),
    city        VARCHAR2(50),
    profile_pic VARCHAR2(255),
    created_at  DATE DEFAULT SYSDATE,
    CONSTRAINT fk_profile_user FOREIGN KEY (user_id) REFERENCES USERS(user_id)
);

-- ================================================
-- TABLE 3: RIDES
-- ================================================
CREATE TABLE RIDES (
    ride_id         NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id         NUMBER NOT NULL,
    from_location   VARCHAR2(200) NOT NULL,
    to_location     VARCHAR2(200) NOT NULL,
    ride_date       DATE NOT NULL,
    ride_time       VARCHAR2(20),
    seats_available NUMBER DEFAULT 1,
    price_per_seat  NUMBER DEFAULT 0,
    status          VARCHAR2(20) DEFAULT 'active',
    pickup_lat      NUMBER,
    pickup_lng      NUMBER,
    dropoff_lat     NUMBER,
    dropoff_lng     NUMBER,
    distance_km     NUMBER,
    duration_mins   NUMBER,
    created_at      DATE DEFAULT SYSDATE,
    CONSTRAINT fk_rides_user FOREIGN KEY (user_id) REFERENCES USERS(user_id)
);

-- ================================================
-- TABLE 4: RIDE_REQUESTS
-- ================================================
CREATE TABLE RIDE_REQUESTS (
    request_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ride_id    NUMBER NOT NULL,
    user_id    NUMBER NOT NULL,
    status     VARCHAR2(20) DEFAULT 'pending',
    created_at DATE DEFAULT SYSDATE,
    CONSTRAINT fk_rr_ride FOREIGN KEY (ride_id) REFERENCES RIDES(ride_id),
    CONSTRAINT fk_rr_user FOREIGN KEY (user_id) REFERENCES USERS(user_id)
);

-- ================================================
-- TABLE 5: RIDE_PASSENGERS
-- ================================================
CREATE TABLE RIDE_PASSENGERS (
    passenger_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ride_id      NUMBER NOT NULL,
    user_id      NUMBER NOT NULL,
    status       VARCHAR2(20) DEFAULT 'confirmed',
    joined_at    DATE DEFAULT SYSDATE,
    CONSTRAINT fk_rp_ride FOREIGN KEY (ride_id) REFERENCES RIDES(ride_id),
    CONSTRAINT fk_rp_user FOREIGN KEY (user_id) REFERENCES USERS(user_id)
);

-- ================================================
-- TABLE 6: HOSTELS
-- ================================================
CREATE TABLE HOSTELS (
    hostel_id      NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id        NUMBER NOT NULL,
    name           VARCHAR2(200) NOT NULL,
    location       VARCHAR2(300) NOT NULL,
    price          NUMBER NOT NULL,
    gender         VARCHAR2(20),
    facilities     VARCHAR2(500),
    contact        VARCHAR2(50),
    image_filename VARCHAR2(255),
    created_at     DATE DEFAULT SYSDATE,
    CONSTRAINT fk_hostels_user FOREIGN KEY (user_id) REFERENCES USERS(user_id)
);

-- ================================================
-- TABLE 7: HOSTEL_BOOKMARKS
-- ================================================
CREATE TABLE HOSTEL_BOOKMARKS (
    bookmark_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id     NUMBER NOT NULL,
    hostel_id   NUMBER NOT NULL,
    created_at  DATE DEFAULT SYSDATE,
    CONSTRAINT fk_bm_user   FOREIGN KEY (user_id)   REFERENCES USERS(user_id),
    CONSTRAINT fk_bm_hostel FOREIGN KEY (hostel_id) REFERENCES HOSTELS(hostel_id),
    CONSTRAINT uq_bookmark  UNIQUE (user_id, hostel_id)
);

-- ================================================
-- TABLE 8: MARKETPLACE
-- ================================================
CREATE TABLE MARKETPLACE (
    item_id        NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id        NUMBER NOT NULL,
    title          VARCHAR2(200) NOT NULL,
    description    VARCHAR2(1000),
    price          NUMBER NOT NULL,
    category       VARCHAR2(50) DEFAULT 'Books',
    condition      VARCHAR2(50) DEFAULT 'Good',
    status         VARCHAR2(20) DEFAULT 'available',
    image_filename VARCHAR2(255),
    created_at     DATE DEFAULT SYSDATE,
    CONSTRAINT fk_market_user FOREIGN KEY (user_id) REFERENCES USERS(user_id)
);

-- ================================================
-- TABLE 9: ITEM_REPORTS
-- ================================================
CREATE TABLE ITEM_REPORTS (
    report_id   NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    reporter_id NUMBER NOT NULL,
    item_id     NUMBER NOT NULL,
    reason      VARCHAR2(200) NOT NULL,
    status      VARCHAR2(20) DEFAULT 'pending',
    created_at  DATE DEFAULT SYSDATE,
    CONSTRAINT fk_report_user FOREIGN KEY (reporter_id) REFERENCES USERS(user_id),
    CONSTRAINT fk_report_item FOREIGN KEY (item_id)     REFERENCES MARKETPLACE(item_id)
);

-- ================================================
-- TABLE 10: MESSAGES
-- ================================================
CREATE TABLE MESSAGES (
    msg_id      NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sender_id   NUMBER NOT NULL,
    receiver_id NUMBER NOT NULL,
    message     VARCHAR2(1000) NOT NULL,
    is_read     NUMBER(1) DEFAULT 0,
    created_at  DATE DEFAULT SYSDATE,
    CONSTRAINT fk_msg_sender   FOREIGN KEY (sender_id)   REFERENCES USERS(user_id),
    CONSTRAINT fk_msg_receiver FOREIGN KEY (receiver_id) REFERENCES USERS(user_id)
);

-- ================================================
-- TABLE 11: NOTIFICATIONS
-- ================================================
CREATE TABLE NOTIFICATIONS (
    notif_id   NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id    NUMBER NOT NULL,
    title      VARCHAR2(100) NOT NULL,
    message    VARCHAR2(500) NOT NULL,
    notif_type VARCHAR2(30) DEFAULT 'general',
    is_read    NUMBER(1) DEFAULT 0,
    created_at DATE DEFAULT SYSDATE,
    CONSTRAINT fk_notif_user FOREIGN KEY (user_id) REFERENCES USERS(user_id)
);

-- ================================================
-- TABLE 12: REVIEWS
-- ================================================
CREATE TABLE REVIEWS (
    review_id   NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    reviewer_id NUMBER NOT NULL,
    target_type VARCHAR2(20) NOT NULL,
    target_id   NUMBER NOT NULL,
    rating      NUMBER(1) NOT NULL,
    comments    VARCHAR2(500),
    created_at  DATE DEFAULT SYSDATE,
    CONSTRAINT fk_review_user FOREIGN KEY (reviewer_id) REFERENCES USERS(user_id)
);

-- ================================================
-- SAMPLE DATA
-- ================================================

-- Users
INSERT INTO USERS (full_name, email, password, university)
VALUES ('Muhim Akhtar', 'fa24-bse-080@isbstudent.comsats.edu.pk',
        'e3b0c44298fc1c149afbf4c8996fb924', 'COMSATS University Islamabad');

INSERT INTO USERS (full_name, email, password, university)
VALUES ('Izhan Shah', 'fa24-bse-095@isbstudent.comsats.edu.pk',
        'e3b0c44298fc1c149afbf4c8996fb924', 'COMSATS University Islamabad');

INSERT INTO USERS (full_name, email, password, university)
VALUES ('Sohail Wazir', 'fa24-bse-105@isbstudent.comsats.edu.pk',
        'e3b0c44298fc1c149afbf4c8996fb924', 'COMSATS University Islamabad');

-- User Profiles
INSERT INTO USER_PROFILES (user_id, department, semester, roll_no, bio, phone, city)
VALUES (1, 'Software Engineering', 'FA24', 'FA24-BSE-080',
        'Software Engineering student at COMSATS Islamabad.', '0311-1234567', 'Rawalpindi');

INSERT INTO USER_PROFILES (user_id, department, semester, roll_no, bio, phone, city)
VALUES (2, 'Software Engineering', 'FA24', 'FA24-BSE-095',
        'Software Engineering student at COMSATS Islamabad.', '0300-9876543', 'Islamabad');

-- Rides
INSERT INTO RIDES (user_id, from_location, to_location, ride_date, ride_time, seats_available, price_per_seat)
VALUES (1, 'Rawalpindi Saddar', 'COMSATS University Islamabad',
        TO_DATE('2026-04-10', 'YYYY-MM-DD'), '08:00 AM', 3, 150);

INSERT INTO RIDES (user_id, from_location, to_location, ride_date, ride_time, seats_available, price_per_seat)
VALUES (2, 'Bahria Town Phase 8', 'COMSATS University Islamabad',
        TO_DATE('2026-04-11', 'YYYY-MM-DD'), '07:30 AM', 2, 100);

-- Ride Requests
INSERT INTO RIDE_REQUESTS (ride_id, user_id, status)
VALUES (1, 2, 'pending');

INSERT INTO RIDE_REQUESTS (ride_id, user_id, status)
VALUES (2, 3, 'approved');

-- Ride Passengers
INSERT INTO RIDE_PASSENGERS (ride_id, user_id, status)
VALUES (2, 3, 'confirmed');

-- Hostels
INSERT INTO HOSTELS (user_id, name, location, price, gender, facilities, contact)
VALUES (1, 'Al-Rehman Boys Hostel', 'Koral Town, Islamabad',
        8000, 'Male', 'WiFi, Laundry, Generator, Water Cooler', '0300-1234567');

INSERT INTO HOSTELS (user_id, name, location, price, gender, facilities, contact)
VALUES (2, 'Fatima Girls Hostel', 'Gulberg Greens, Islamabad',
        9000, 'Female', 'WiFi, AC, Security, Meals', '0311-9876543');

-- Hostel Bookmarks
INSERT INTO HOSTEL_BOOKMARKS (user_id, hostel_id)
VALUES (2, 1);

-- Marketplace
INSERT INTO MARKETPLACE (user_id, title, description, price, category, condition)
VALUES (2, 'Calculus Textbook 10th Edition',
        'Good condition, no missing pages, minor highlights', 500, 'Books', 'Good');

INSERT INTO MARKETPLACE (user_id, title, description, price, category, condition)
VALUES (1, 'Dell Laptop i5 8th Gen',
        '8GB RAM, 256GB SSD, charger included, minor scratches', 45000, 'Gadgets', 'Fair');

-- Item Reports
INSERT INTO ITEM_REPORTS (reporter_id, item_id, reason)
VALUES (3, 2, 'Price seems too high compared to market value.');

-- Messages
INSERT INTO MESSAGES (sender_id, receiver_id, message)
VALUES (2, 1, 'Assalamu Alaikum, is the hostel still available?');

INSERT INTO MESSAGES (sender_id, receiver_id, message)
VALUES (1, 2, 'Wa alaikum salam, yes it is available!');

-- Notifications
INSERT INTO NOTIFICATIONS (user_id, title, message, notif_type)
VALUES (1, 'New Ride Request', 'Izhan Shah requested a seat on your ride.', 'ride_request');

INSERT INTO NOTIFICATIONS (user_id, title, message, notif_type)
VALUES (2, 'Ride Request Accepted', 'Your ride request has been accepted!', 'ride_request');

INSERT INTO NOTIFICATIONS (user_id, title, message, notif_type)
VALUES (1, 'New Message', 'You have a new message from Izhan Shah.', 'message');

-- Reviews
INSERT INTO REVIEWS (reviewer_id, target_type, target_id, rating, comments)
VALUES (2, 'HOSTEL', 1, 5, 'Excellent hostel, very clean and close to campus!');

INSERT INTO REVIEWS (reviewer_id, target_type, target_id, rating, comments)
VALUES (3, 'RIDE', 2, 4, 'Driver was punctual and the ride was comfortable.');

COMMIT;
