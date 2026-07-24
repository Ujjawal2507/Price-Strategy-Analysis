-- Phase 5: MySQL schema — star-schema style
-- Fact table: transactions. Dimensions: products, households, campaigns, causal.
-- MySQL notes vs the original Postgres version:
--   * TEXT columns that were used as short descriptive fields are switched to
--     VARCHAR, since MySQL cannot cleanly index a plain TEXT column and these
--     values are all short, bounded strings.
--   * "CREATE INDEX IF NOT EXISTS" is not supported in MySQL, so indexes are
--     declared inline inside each CREATE TABLE instead.
--   * ENGINE=InnoDB and DEFAULT CHARSET=utf8mb4 are pinned explicitly, since
--     InnoDB is required for foreign key support.

CREATE TABLE IF NOT EXISTS dim_products (
    product_id            BIGINT PRIMARY KEY,
    manufacturer          VARCHAR(255),
    department            VARCHAR(255),
    brand                 VARCHAR(255),
    commodity_desc        VARCHAR(255),
    sub_commodity_desc    VARCHAR(255),
    curr_size_of_product  VARCHAR(255)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS dim_households (
    household_key         BIGINT PRIMARY KEY,
    age_desc               VARCHAR(255),
    marital_status_code    VARCHAR(255),
    income_desc             VARCHAR(255),
    homeowner_desc          VARCHAR(255),
    hh_comp_desc            VARCHAR(255),
    household_size_desc     VARCHAR(255),
    kid_category_desc       VARCHAR(255)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS dim_campaign_desc (
    campaign      BIGINT PRIMARY KEY,
    description    VARCHAR(255),
    start_day      INTEGER,
    end_day        INTEGER
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS fact_transactions (
    household_key                   BIGINT,
    basket_id                        BIGINT,
    day                              INTEGER,
    product_id                       BIGINT,
    quantity                         INTEGER,
    sales_value                      NUMERIC(10,2),
    store_id                         BIGINT,
    retail_disc                      NUMERIC(10,2),
    trans_time                       INTEGER,
    week_no                          INTEGER,
    coupon_disc                      NUMERIC(10,2),
    coupon_match_disc                NUMERIC(10,2),
    total_discount                   NUMERIC(10,2),
    unit_price                       NUMERIC(10,2),
    list_price                       NUMERIC(10,2),
    is_promo                         SMALLINT,
    estimated_cost                   NUMERIC(10,2),
    estimated_profit                 NUMERIC(10,2),
    profit_margin_pct                NUMERIC(6,2),
    basket_value                     NUMERIC(10,2),
    household_purchase_frequency     INTEGER,
    INDEX idx_fact_txn_product (product_id),
    INDEX idx_fact_txn_household (household_key),
    INDEX idx_fact_txn_week (week_no),
    CONSTRAINT fk_fact_txn_household FOREIGN KEY (household_key) REFERENCES dim_households(household_key),
    CONSTRAINT fk_fact_txn_product FOREIGN KEY (product_id) REFERENCES dim_products(product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS fact_causal (
    product_id    BIGINT,
    store_id       BIGINT,
    week_no        INTEGER,
    display         VARCHAR(255),
    mailer           VARCHAR(255),
    INDEX idx_fact_causal_product (product_id),
    CONSTRAINT fk_fact_causal_product FOREIGN KEY (product_id) REFERENCES dim_products(product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
