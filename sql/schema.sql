-- ================================================
-- CampusConnect Database Schema
-- Oracle SQL
-- ================================================

-- Drop tables if they exist (clean start)
DROP TABLE MESSAGES CASCADE CONSTRAINTS;
DROP TABLE RIDE_REQUESTS CASCADE CONSTRAINTS;
DROP TABLE MARKETPLACE CASCADE CONSTRAINTS;
DROP TABLE HOSTELS CASCADE CONSTRAINTS;
DROP TABLE RIDES CASCADE CONSTRAINTS;
DROP TABLE USERS CASCADE CONSTRAINTS;

-- ================================================
-- TABLE 1: USERS
-- ================================================
CREATE TABLE USERS (
    user_id     NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    full_name   VARCHAR2(100) NOT NULL,
    email       VARCHAR2(100) NOT NULL UNIQUE,
    password    VARCHAR2(255) NOT NULL,
    university  VARCHAR2(100) DEFAULT 'COMSATS University',
    created_at  DATE DEFAULT SYSDATE
);

-- ================================================
-- TABLE 2: RIDES
-- ================================================
CREATE TABLE RIDES (
    ride_id         NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id         NUMBER NOT NULL,
    from_location   VARCHAR2(100) NOT NULL,
    to_location     VARCHAR2(100) NOT NULL,
    ride_date       DATE NOT NULL,
    ride_time       VARCHAR2(20) NOT NULL,
    seats_available NUMBER(2) NOT NULL,
    price_per_seat  NUMBER(10,2) DEFAULT 0,
    status          VARCHAR2(20) DEFAULT 'active',
    created_at      DATE DEFAULT SYSDATE,
    CONSTRAINT fk_rides_user FOREIGN KEY (user_id) REFERENCES USERS(user_id)
);

-- ================================================
-- TABLE 3: RIDE_REQUESTS
-- ================================================
CREATE TABLE RIDE_REQUESTS (
    request_id  NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ride_id     NUMBER NOT NULL,
    user_id     NUMBER NOT NULL,
    status      VARCHAR2(20) DEFAULT 'pending',
    created_at  DATE DEFAULT SYSDATE,
    CONSTRAINT fk_rr_ride FOREIGN KEY (ride_id) REFERENCES RIDES(ride_id),
    CONSTRAINT fk_rr_user FOREIGN KEY (user_id) REFERENCES USERS(user_id)
);

-- ================================================
-- TABLE 4: HOSTELS
-- ================================================
CREATE TABLE HOSTELS (
    hostel_id   NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id     NUMBER NOT NULL,
    name        VARCHAR2(100) NOT NULL,
    location    VARCHAR2(200) NOT NULL,
    price       NUMBER(10,2) NOT NULL,
    gender      VARCHAR2(10) DEFAULT 'Any',
    facilities  VARCHAR2(300),
    contact     VARCHAR2(20),
    created_at  DATE DEFAULT SYSDATE,
    CONSTRAINT fk_hostels_user FOREIGN KEY (user_id) REFERENCES USERS(user_id)
);

-- ================================================
-- TABLE 5: MARKETPLACE
-- ================================================
CREATE TABLE MARKETPLACE (
    item_id     NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id     NUMBER NOT NULL,
    title       VARCHAR2(100) NOT NULL,
    description VARCHAR2(500),
    price       NUMBER(10,2) NOT NULL,
    category    VARCHAR2(50) DEFAULT 'Books',
    condition   VARCHAR2(20) DEFAULT 'Good',
    status      VARCHAR2(20) DEFAULT 'available',
    created_at  DATE DEFAULT SYSDATE,
    CONSTRAINT fk_market_user FOREIGN KEY (user_id) REFERENCES USERS(user_id)
);

-- ================================================
-- TABLE 6: MESSAGES
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
-- SAMPLE DATA FOR TESTING
-- ================================================
INSERT INTO USERS (full_name, email, password, university)
VALUES ('Izhan Shah', 'izhan@comsats.edu.pk', 'test123', 'COMSATS University');

INSERT INTO USERS (full_name, email, password, university)
VALUES ('Muhim Akhtar', 'muhim@comsats.edu.pk', 'test123', 'COMSATS University');

INSERT INTO USERS (full_name, email, password, university)
VALUES ('Muskan Zehra', 'muskan@comsats.edu.pk', 'test123', 'COMSATS University');

COMMIT;